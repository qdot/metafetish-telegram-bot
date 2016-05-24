from telegram.ext import CommandHandler
from .pickledb import pickledb
import os


class UserNotFoundException(Exception):
    pass


class UserFlagGroupNotFoundException(Exception):
    pass


def require_register(func):
    def func_wrapper(self, bot, update):
        user_id = update.message.from_user.id
        if not self.is_valid_user(user_id):
            bot.sendMessage(update.message.chat_id,
                            text="Please register with the bot (using the /register command) before using this command!")
            return
        func(self, bot, update)
    return func_wrapper


class UserManager(object):
    def __init__(self, dispatcher, dbdir):
        userdir = os.path.join(dbdir, "users")
        if not os.path.isdir(userdir):
            os.makedirs(userdir)
        self.db = pickledb(os.path.join(userdir, "users.db"), True)

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

    @require_register
    def set_show_profile(self, bot, update):
        user_id = update.message.from_user.id
        self.db.dadd(user_id, ("show_profile", True))

    @require_register
    def set_hide_profile(self, bot, update):
        user_id = update.message.from_user.id
        self.db.dadd(user_id, ("show_profile", False))

    @require_register
    def get_user_flag_group(self, user_id, flag_group):
        pass

    @require_register
    def set_user_flag_group(self, user_id, flag_group, flag_values):
        pass

    @require_register
    def get_user_field(self, user_id, field):
        pass

    @require_register
    def set_user_field(self, user_id, field, field_value):
        pass

    @require_register
    def shutdown(self):
        self.db.dump()
