from telegram.ext import CommandHandler
from .base import MetafetishModuleBase
import cgi


class UserNotFoundException(Exception):
    pass


class UserFlagGroupNotFoundException(Exception):
    pass


class UserManager(MetafetishModuleBase):
    def __init__(self, dbdir):
        super().__init__(dbdir, "users", __name__, True)
        self.has_admin = True
        if self.get_num_users() == 0:
            self.has_admin = False

    def register_with_dispatcher(self, dispatcher):
        dispatcher.add_handler(CommandHandler('register', self.register))
        dispatcher.add_handler(CommandHandler('profile_hide',
                                              self.set_hide_profile))
        dispatcher.add_handler(CommandHandler('profile_show',
                                              self.set_show_profile))

    def get_num_users(self):
        return len(self.db.getall())

    def is_valid_user(self, user_id):
        if str(user_id) in self.db.getall():
            return True
        return False

    def register(self, bot, update):
        user_id = str(update.message.from_user.id)
        if self.is_valid_user(user_id):
            bot.sendMessage(update.message.chat_id,
                            text="You're already registered!")
            return
        # Use the user_id as the dictionary key. Unfortunately the id is an
        # int so this requires casting to make sure comparisons work.
        user_db = {"flags": ["admin" if not self.has_admin else ""],
                   "fields": {},
                   "show_profile": False,
                   "username": update.message.from_user.username,
                   "displayname": "%s %s" % (update.message.from_user.first_name,
                                             update.message.from_user.last_name)}
        if not self.has_admin:
            bot.sendMessage(update.message.chat_id,
                            text="You're the first user, therefore you're the <b>admin</b>.",
                            parse_mode="HTML")
        self.has_admin = True
        self.db.set(str(user_id), user_db)
        bot.sendMessage(update.message.chat_id,
                        text="You are now registered!")

    def help(self, bot, update):
        bot.sendMessage(update.message.chat_id,
                        text="""
<b>User Module</b>

The user module allows telegram users to register with the bot to use different functionality. Bot administrators can delegate privileges to registered users for different bot capabilities.

Each registered user can also have profiles, which consists of a field name (with no whitespace) and description of that field. This allows users to share whatever information they might want about themselves. Profiles sharing is offby default, and can be turned on and off as needed.

For instance, to add a twitter account to your profile, the command would be:

/useraddfield TwitterAccount http://www.twitter.com/metafetish

To remove that field:

/userrmfield TwitterAccount

Note that field names are case insensitive for search, but will display as entered.

<b>Commands</b>

%s
""" % (self.commands()),
                        parse_mode="HTML")

    def commands(self):
        return """/userhelp - Display users help message.
/userregister - Register an account with the bot.
/useraddfield - Parameters: [field name] [field desc]. Add or update a profile field.
/userrmfield - Parameters: [field name]. Remove a profile field.
/usershowprofile - Turn profile sharing on.
/userhideprofile - Turn profile sharing off.
/userprofile - Parameters: [telegram user name or display name]. Show the profile of another user."""

    def show_profile(self, bot, update, show_profile):
        user_id = str(update.message.from_user.id)
        self.db.dadd(user_id, ("show_profile", show_profile))
        bot.sendMessage(update.message.chat_id,
                        text="Profile display is now turned <b>%s</b>." % ("ON" if show_profile else "OFF"),
                        parse_mode="HTML")

    def get_user_by_name_or_id(self, user_name_or_id):
        user_id = None
        user = None
        if user_name_or_id in self.db.getall():
            user_id = user_name_or_id
            user = self.db.get(user_name_or_id)
        else:
            for id in self.db.getall():
                data = self.db.get(id)
                if data["username"] == user_name_or_id:
                    user_id = id
                    user = data
        return (user_id, user)

    def add_flag(self, bot, update):
        try:
            (user_command, user_name_or_id, user_flag) = update.message.text.split()
        except:
            bot.sendMessage(update.message.chat_id,
                            text="Incorrect syntax for add flag command. Please try again.")
            return
        (user_id, user) = self.get_user_by_name_or_id(user_name_or_id)
        if not user_id:
            bot.sendMessage(update.message.chat_id,
                            text="Can't find user to add tags to!")
            return
        if user_flag not in user["flags"]:
            user["flags"].append(user_flag)
            self.db.set(user_id, user)
            bot.sendMessage(update.message.chat_id,
                            text="Added flag %s to %s" % (user_flag, user_name_or_id))
        else:
            bot.sendMessage(update.message.chat_id,
                            text="User %s already has flag %s" % (user_name_or_id, user_flag))

    def remove_flag(self, bot, update):
        try:
            (user_command, user_name_or_id, user_flag) = update.message.text.split()
        except:
            bot.sendMessage(update.message.chat_id,
                            text="Incorrect syntax for add flag command. Please try again.")
            return
        (user_id, user) = self.get_user_by_name_or_id(user_name_or_id)
        if not user_id:
            bot.sendMessage(update.message.chat_id,
                            text="Can't find user to add tags to!")
            return
        if user_flag in user["flags"]:
            user["flags"].remove(user_flag)
            self.db.set(user_id, user)
            bot.sendMessage(update.message.chat_id,
                            text="Remove flag %s from %s" % (user_flag, user_name_or_id))
        else:
            bot.sendMessage(update.message.chat_id,
                            text="User %s does not have flag %s" % (user_name_or_id, user_flag))

    def has_flag(self, user_id, flag):
        if type(user_id) is not str:
            user_id = str(user_id)
        try:
            user = self.db.get(user_id)
        except KeyError:
            return False
        if flag in user["flags"]:
            return True
        return False

    def get_fields(self, bot, update):
        try:
            (prof_command, prof_name) = update.message.text.split()
        except:
            prof_name = update.message.from_user.username
        self.logger.warn("NAME %s" % prof_name)
        (user_id, user) = self.get_user_by_name_or_id(prof_name)
        if not user_id or not user["show_profile"]:
            bot.sendMessage(update.message.chat_id,
                            text="User not found, or does not have a public profile")
            return
        fields = "<b>User Profile for %s</b>\n\n" % (prof_name)
        for (k, v) in user["fields"].items():
            fields += "<b>%s</b>\n\n%s\n\n" % (k, v)
        bot.sendMessage(update.message.chat_id,
                        text=fields,
                        parse_mode="HTML",
                        disable_web_page_preview=True)

    def add_field(self, bot, update):
        user_id = str(update.message.from_user.id)
        try:
            (field_command, field_name, field_value) = update.message.text.split()
        except:
            bot.sendMessage(update.message.chat_id,
                            text="Incorrect syntax for add field command. Please try again.")
            return
        user = self.db.get(user_id)
        user["fields"][cgi.escape(field_name)] = cgi.escape(field_value)
        self.db.set(user_id, user)
        bot.sendMessage(update.message.chat_id,
                        text="Field %s is now set/updated in your profile." % (field_name))

    def remove_field(self, bot, update):
        user_id = str(update.message.from_user.id)
        try:
            (field_command, field_name) = update.message.text.split()
        except:
            bot.sendMessage(update.message.chat_id,
                            text="Incorrect syntax for remove field command. Please try again.")
            return
        user = self.db.get(user_id)
        try:
            del user["fields"][cgi.escape(field_name)]
        except KeyError:
            bot.sendMessage(update.message.chat_id,
                            text="Can't find field %s in your profile." % (field_name))
            return
        self.db.set(user_id, user)
        bot.sendMessage(update.message.chat_id,
                        text="Field %s has been removed from your profile." % (field_name))

    def show_list(self, bot, update):
        users = "User list:\n\n"
        for k in self.db.getall():
            user_info = self.db.get(k)
            users += "- %s : %s : %s\n" % (user_info["username"],
                                           user_info["displayname"],
                                           k)
        bot.sendMessage(update.message.chat_id,
                        text=users)
