from telegram.ext import CommandHandler
from .pickledb import pickledb
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

    def register_with_dispatcher(self, dispatcher):
        dispatcher.add_handler(CommandHandler('register', self.register))
        dispatcher.add_handler(CommandHandler('profile_hide',
                                              self.set_hide_profile))
        dispatcher.add_handler(CommandHandler('profile_show',
                                              self.set_show_profile))

    def is_valid_user(self, user_id):
        try:
            self.db.dgetall(user_id)
            return True
        except:
            return False

    def register(self, bot, update):
        user_id = update.message.from_user.id
        if self.is_valid_user(user_id):
            bot.sendMessage(update.message.chat_id,
                            text="You're already registered!")
            return
        self.db.dcreate(user_id)
        self.db.dadd(user_id, ("flags", {}))
        self.db.dadd(user_id, ("fields", {}))
        self.db.dadd(user_id, ("show_profile", False))
        bot.sendMessage(update.message.chat_id,
                        text="You are now registered!")

    def set_show_profile(self, bot, update):
        user_id = update.message.from_user.id
        self.db.dadd(user_id, ("show_profile", True))

    def set_hide_profile(self, bot, update):
        user_id = update.message.from_user.id
        self.db.dadd(user_id, ("show_profile", False))

    def get_user_flag_group(self, user_id, flag_group):
        pass

    def set_user_flag_group(self, user_id, flag_group, flag_values):
        pass

    def get_user_field(self, user_id, field):
        pass

    def set_user_field(self, user_id, field, field_value):
        pass

    def shutdown(self):
        self.db.dump()
