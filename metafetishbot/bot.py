from telegram.ext import Updater, CommandHandler
from .permissioncommandhandler import PermissionCommandHandler
from .definitions import DefinitionManager
from .users import UserManager
from .groups import GroupManager
import argparse
import os
import logging
from functools import partial


class MetafetishTelegramBot(object):
    FLAGS = ["admin", "def_edit", "user_flags"]

    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--dbdir", dest="dbdir",
                            help="Directory for pickledb storage")
        parser.add_argument("-t", "--token", dest="token_file",
                            help="File containing telegram API token")
        args = parser.parse_args()

        if not args.token_file:
            print("Token file argument required!")
            parser.print_help()
            raise RuntimeError()

        try:
            with open(args.token_file, "r") as f:
                tg_token = f.readline()[0:-1]
        except:
            print("Cannot open token file!")
            return 0

        if not args.dbdir or not os.path.isdir(args.dbdir):
            print("Valid database directory required!")
            parser.print_help()
            raise RuntimeError()

        self.logger = logging.getLogger(__name__)
        self.updater = Updater(token=tg_token)
        self.dispatcher = self.updater.dispatcher
        self.users = UserManager(args.dbdir)
        self.definitions = DefinitionManager(args.dbdir)
        self.groups = GroupManager(args.dbdir)

        # Default commands
        self.dispatcher.add_handler(CommandHandler('start', self.handle_start))
        self.dispatcher.add_handler(CommandHandler('help', self.handle_help))
        self.dispatcher.add_handler(CommandHandler('settings', self.handle_settings))

        # User module commands
        self.dispatcher.add_handler(PermissionCommandHandler('register',
                                                             [self.require_group],
                                                             self.users.register))
        self.dispatcher.add_handler(PermissionCommandHandler('helpuser',
                                                             [self.require_group],
                                                             self.users.help))
        # self.dispatcher.add_handler(PermissionCommandHandler('addprofilefield',
        #                                                      [self.require_group,
        #                                                       self.require_register],
        #                                                      self.users.add_field))
        # self.dispatcher.add_handler(PermissionCommandHandler('rmprofilefield',
        #                                                      [self.require_group,
        #                                                       self.require_register],
        #                                                      self.users.remove_field))

        # Definition module commands
        self.dispatcher.add_handler(PermissionCommandHandler('def',
                                                             [self.require_group,
                                                              self.require_register],
                                                             self.definitions.show))
        self.dispatcher.add_handler(PermissionCommandHandler('helpdef',
                                                             [self.require_group,
                                                              self.require_register],
                                                             self.definitions.help))
        self.dispatcher.add_handler(PermissionCommandHandler('adddef',
                                                             [self.require_group,
                                                              self.require_register,
                                                              partial(self.require_flag, flag="def_edit")],
                                                             self.definitions.add))
        self.dispatcher.add_handler(PermissionCommandHandler('rmdef',
                                                             [self.require_group,
                                                              self.require_register,
                                                              partial(self.require_flag, flag="def_edit")],
                                                             self.definitions.rm))

        # Admin commands
        self.dispatcher.add_handler(PermissionCommandHandler('adduserflag',
                                                             [self.require_register,
                                                              partial(self.require_flag, flag="admin")],
                                                             self.users.add_flag))
        self.dispatcher.add_handler(PermissionCommandHandler('rmuserflag',
                                                             [self.require_register,
                                                              partial(self.require_flag, flag="admin")],
                                                             self.users.remove_flag))
        self.dispatcher.add_handler(PermissionCommandHandler('addbotgroup',
                                                             [self.require_register,
                                                              partial(self.require_flag, flag="admin")],
                                                             self.groups.add_group))
        self.dispatcher.add_handler(PermissionCommandHandler('rmbotgroup',
                                                             [self.require_register,
                                                              partial(self.require_flag, flag="admin")],
                                                             self.groups.rm_group))

        # On errors, just print to console and hope someone sees it
        self.dispatcher.add_error_handler(self.handle_error)

    def handle_start(self, bot, update):
        user_id = update.message.from_user.id
        start_text = ["Hi! I'm @metafetish_bot, the bot for the Metafetish Telegram Channel.", ""]
        should_help = False
        if not self.groups.user_in_groups(bot, user_id):
            start_text += ["Before we get started, you'll need to join the metafetish channel. You can do so by going to http://telegram.me/metafetish.",
                           "After you've done that, send me the /register command so I can register you to use bot features.",
                           "Once you've joined and registered, message me with /start again and we can continue!"]
        elif not self.users.is_valid_user(user_id):
            start_text += ["Looks like you're in the group, great! Now, send me the /register command so I can register you to use bot features.",
                           "Once you've joined and registered, message me with /start again and we can continue!"]
        else:
            start_text += ["It looks like you're in the channel and registered, so let's get started!", ""]
            should_help = True

        bot.sendMessage(update.message.chat_id,
                        "\n".join(start_text))
        if should_help:
            self.handle_help(bot, update)

    def handle_help(self, bot, update):
        user_id = update.message.from_user.id
        if not self.groups.user_in_groups(bot, user_id) or not self.users.is_valid_user(user_id):
            self.handle_start(bot, update)
            return
        help_text = ["I have the following modules available currently:",
                     "",
                     "<b>Definitions</b>",
                     "Allows users to store and retrieve definitions for words, phrases, etc. Use /def_help for commands and options.",
                     "",
                     "<b>Users</b>",
                     "Handles user registration and profiles. Use /user_help for command and options."]
        bot.sendMessage(update.message.chat_id,
                        "\n".join(help_text),
                        parse_mode="HTML")

    def handle_settings(self, bot, update):
        pass

    def handle_error(self, bot, update, error):
        self.logger.warn("Exception thrown! %s", self.error)

    def require_register(self, bot, update):
        user_id = update.message.from_user.id
        if not self.users.is_valid_user(user_id):
            bot.sendMessage(update.message.chat_id,
                            text="Please register with the bot (using the /register command) before using this command!")
            return False
        return True

    def require_group(self, bot, update):
        # Special Case: If the bot has no users yet, we need to let the first
        # user register so they can be an admin. After that, always require
        # membership
        if self.users.get_num_users() == 0:
            return True
        user_id = update.message.from_user.id
        if not self.groups.user_in_groups(bot, user_id):
            bot.sendMessage(update.message.chat_id,
                            text="Please join the 'metafetish' group to use this bot! http://telegram.me/metafetish")
            return False
        return True

    # When used with PermissionCommandHandler, Function requires currying with
    # flag we want to check for.
    def require_flag(self, bot, update, flag):
        user_id = update.message.from_user.id
        if not self.users.has_flag(user_id, flag):
            bot.sendMessage(update.message.chat_id,
                            text="You do not have the required permissions to run this command. Please check the help for the module the command comes from.")
            return False
        return True

    def start_loop(self):
        self.updater.start_polling()
        self.updater.idle()

    def shutdown(self):
        self.users.shutdown()
        self.definitions.shutdown()
        self.groups.shutdown()
