from telegram.ext import CommandHandler
from .pickledb import pickledb
import logging
import os


class UserNotFoundException(Exception):
    pass


class UserFlagGroupNotFoundException(Exception):
    pass


class UserManager(object):
    def __init__(self, dbdir):
        userdir = os.path.join(dbdir, "users")
        if not os.path.isdir(userdir):
            os.makedirs(userdir)
        self.db = pickledb(os.path.join(userdir, "users.db"), True)
        self.logger = logging.getLogger(__name__)
        self.has_admin = True
        if not self.db.get("users"):
            self.db.dcreate("users")
            self.has_admin = False

    def register_with_dispatcher(self, dispatcher):
        dispatcher.add_handler(CommandHandler('register', self.register))
        dispatcher.add_handler(CommandHandler('profile_hide',
                                              self.set_hide_profile))
        dispatcher.add_handler(CommandHandler('profile_show',
                                              self.set_show_profile))

    def is_valid_user(self, user_id):
        if str(user_id) in self.db.dkeys("users"):
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
        self.db.dadd("users", (str(user_id), user_db))
        bot.sendMessage(update.message.chat_id,
                        text="You are now registered!")

    def help(self, bot, update):
        bot.sendMessage(update.message.chat_id,
                        text="This is not helpful.")

    def set_show_profile(self, bot, update):
        user_id = str(update.message.from_user.id)
        self.db.dadd(user_id, ("show_profile", True))

    def set_hide_profile(self, bot, update):
        user_id = str(update.message.from_user.id)
        self.db.dadd(user_id, ("show_profile", False))

    def get_user_by_name_or_id(self, user_name_or_id):
        user_id = None
        user = None
        if user_name_or_id in self.db.dkeys("users"):
            user_id = user_name_or_id
            user = self.db.dget("users", user_name_or_id)
        else:
            for (id, fields) in self.db.dgetall("users").items():
                if fields["username"] == user_name_or_id:
                    user_id = id
                    user = fields
        return (user_id, user)

    def add_flag(self, bot, update):
        try:
            (user_command, user_name_or_id, user_flag) = update.message.text.split()
        except:
            bot.sendMessage(update.message.chat_id,
                            text="Incorrect syntax for add flag command. Please try again.")
        (user_id, user) = self.get_user_by_name_or_id(user_name_or_id)
        if not user_id:
            bot.sendMessage(update.message.chat_id,
                            text="Can't find user to add tags to!")
            return
        if user_flag not in user["flags"]:
            user["flags"].append(user_flag)
            self.db.dadd("users", (user_id, user))
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
        (user_id, user) = self.get_user_by_name_or_id(user_name_or_id)
        if not user_id:
            bot.sendMessage(update.message.chat_id,
                            text="Can't find user to add tags to!")
        if user_flag in user["flags"]:
            user["flags"].remove(user_flag)
            self.db.dadd("users", (user_id, user))
            bot.sendMessage(update.message.chat_id,
                            text="Remove flag %s from %s" % (user_flag, user_name_or_id))
        else:
            bot.sendMessage(update.message.chat_id,
                            text="User %s does not have flag %s" % (user_name_or_id, user_flag))

    def has_flag(self, user_id, flag):
        if type(user_id) is not str:
            user_id = str(user_id)
        try:
            user = self.db.dget("users", user_id)
        except KeyError:
            return False
        if flag in user["flags"]:
            return True
        return False

    def get_fields(self, user_id):
        pass

    def add_field(self, user_id, field, field_value):
        pass

    def remove_field(self, user_id, field):
        pass

    def shutdown(self):
        self.db.dump()
