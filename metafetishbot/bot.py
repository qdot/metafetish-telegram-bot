from telegram.ext import Updater
from .permissioncommandhandler import PermissionCommandHandler
from .definitions import DefinitionManager
from .users import UserManager
from .groups import GroupManager
import argparse
import os
import logging


class MetafetishTelegramBot(object):
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
        self.group = GroupManager(args.dbdir)

        self.dispatcher.add_handler(PermissionCommandHandler('register',
                                                             [self.require_group],
                                                             self.users.register))
        self.dispatcher.add_handler(PermissionCommandHandler('def',
                                                             [self.require_register,
                                                              self.require_group],
                                                             self.definitions.show))
        self.dispatcher.add_handler(PermissionCommandHandler('def_show',
                                                             [self.require_register,
                                                              self.require_group],
                                                             self.definitions.show))
        self.dispatcher.add_handler(PermissionCommandHandler('def_add',
                                                             [self.require_register,
                                                              self.require_group],
                                                             self.definitions.add))
        self.dispatcher.add_handler(PermissionCommandHandler('def_rm',
                                                             [self.require_register,
                                                              self.require_group],
                                                             self.definitions.rm))

        self.dispatcher.add_error_handler(self.handle_error)

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
        user_id = update.message.from_user.id
        if not self.group.user_in_group(bot, user_id):
            bot.sendMessage(update.message.chat_id,
                            text="Please join the 'metafetish' group to use this bot! http://telegram.me/metafetish")
            return False
        return True

    def start_loop(self):
        self.updater.start_polling()
        self.updater.idle()

    def shutdown(self):
        self.users.shutdown()
        self.definitions.shutdown()
