from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
from .permissioncommandhandler import PermissionCommandHandler
from .definitions import DefinitionManager
from .users import UserManager
from .groups import GroupManager
from .conversations import ConversationManager
import argparse
import os
import logging
from functools import partial


class MetafetishTelegramBot(object):
    FLAGS = ["admin", "def_edit", "user_flags"]

    def __init__(self, dbdir, tg_token):
        if not dbdir or not os.path.isdir(dbdir):
            print("Valid database directory required!")
            raise RuntimeError()
        self.logger = logging.getLogger(__name__)
        self.updater = Updater(token=tg_token)
        self.dispatcher = self.updater.dispatcher
        self.conversations = ConversationManager()
        self.users = UserManager(dbdir, self.conversations)
        self.definitions = DefinitionManager(dbdir, self.conversations)
        self.groups = GroupManager(dbdir)

        self.modules = [self.users, self.definitions, self.groups]

        self.dispatcher.add_handler(MessageHandler([Filters.text],
                                                   self.handle_message))

        # Default commands
        self.dispatcher.add_handler(PermissionCommandHandler('start',
                                                             [self.try_register,
                                                              self.require_privmsg],
                                                             self.handle_start))
        self.dispatcher.add_handler(PermissionCommandHandler('help',
                                                             [self.try_register,
                                                              self.require_privmsg],
                                                             self.handle_help))
        self.dispatcher.add_handler(PermissionCommandHandler('settings',
                                                             [self.try_register,
                                                              self.require_privmsg],
                                                             self.handle_settings))
        self.dispatcher.add_handler(CommandHandler('cancel',
                                                   self.handle_cancel))

        # User module commands
        self.dispatcher.add_handler(PermissionCommandHandler('userhelp',
                                                             [self.require_group,
                                                              self.require_privmsg],
                                                             self.users.help))
        self.dispatcher.add_handler(PermissionCommandHandler('usershowprofile',
                                                             [self.require_group,
                                                              self.require_privmsg,
                                                              self.try_register],
                                                             partial(self.users.show_profile, show_profile=True)))
        self.dispatcher.add_handler(PermissionCommandHandler('userhideprofile',
                                                             [self.require_group,
                                                              self.require_privmsg,
                                                              self.try_register],
                                                             partial(self.users.show_profile, show_profile=False)))
        self.dispatcher.add_handler(PermissionCommandHandler('useraddfield',
                                                             [self.require_group,
                                                              self.require_privmsg,
                                                              self.try_register],
                                                             self.users.add_field))
        self.dispatcher.add_handler(PermissionCommandHandler('userrmfield',
                                                             [self.require_group,
                                                              self.require_privmsg,
                                                              self.try_register],
                                                             self.users.remove_field))
        self.dispatcher.add_handler(PermissionCommandHandler('userprofile',
                                                             [self.require_group,
                                                              self.require_privmsg,
                                                              self.try_register],
                                                             self.users.get_fields))

        # Definition module commands
        self.dispatcher.add_handler(PermissionCommandHandler('def',
                                                             [self.require_group,
                                                              self.try_register],
                                                             self.definitions.show))
        self.dispatcher.add_handler(PermissionCommandHandler('deflist',
                                                             [self.require_group,
                                                              self.try_register],
                                                             self.definitions.list))
        self.dispatcher.add_handler(PermissionCommandHandler('defhelp',
                                                             [self.require_group,
                                                              self.require_privmsg,
                                                              self.try_register],
                                                             self.definitions.help))
        self.dispatcher.add_handler(PermissionCommandHandler('defadd',
                                                             [self.require_group,
                                                              self.require_privmsg,
                                                              self.try_register],
                                                             self.definitions.add))
        self.dispatcher.add_handler(PermissionCommandHandler('defrm',
                                                             [self.require_group,
                                                              self.require_privmsg,
                                                              self.try_register],
                                                             self.definitions.rm))

        # Admin commands
        self.dispatcher.add_handler(PermissionCommandHandler('userlist',
                                                             [self.try_register,
                                                              self.require_privmsg,
                                                              partial(self.require_flag, flag="admin")],
                                                             self.users.show_list))
        self.dispatcher.add_handler(PermissionCommandHandler('useraddflag',
                                                             [self.try_register,
                                                              self.require_privmsg,
                                                              partial(self.require_flag, flag="admin")],
                                                             self.users.add_flag))
        self.dispatcher.add_handler(PermissionCommandHandler('userrmflag',
                                                             [self.try_register,
                                                              self.require_privmsg,
                                                              partial(self.require_flag, flag="admin")],
                                                             self.users.remove_flag))
        self.dispatcher.add_handler(PermissionCommandHandler('groupadd',
                                                             [self.try_register,
                                                              self.require_privmsg,
                                                              partial(self.require_flag, flag="admin")],
                                                             self.groups.add_group))
        self.dispatcher.add_handler(PermissionCommandHandler('grouprm',
                                                             [self.try_register,
                                                              self.require_privmsg,
                                                              partial(self.require_flag, flag="admin")],
                                                             self.groups.rm_group))
        self.dispatcher.add_handler(PermissionCommandHandler('outputcommands',
                                                             [self.try_register,
                                                              self.require_privmsg,
                                                              partial(self.require_flag, flag="admin")],
                                                             self.output_commands))

        # On errors, just print to console and hope someone sees it
        self.dispatcher.add_error_handler(self.handle_error)

    def handle_start(self, bot, update):
        user_id = update.message.from_user.id
        start_text = ["Hi! I'm @metafetish_bot, the bot for the Metafetish Telegram Group Network.", ""]
        should_help = False
        if len(self.groups.get_groups()) > 0 and not self.groups.user_in_groups(bot, user_id):
            start_text += ["Before we get started, you'll need to join one of the following groups:"]
            for g in self.groups.get_groups():
                start_text += ["- %s" % (g)]
            start_text += ["Once you've joined, message me with /start again and we can continue!"]
        else:
            start_text += ["It looks like you're in one of my groups, so let's get started!", ""]
            should_help = True

        bot.sendMessage(update.message.chat.id,
                        "\n".join(start_text))
        if should_help:
            self.handle_help(bot, update)

    def handle_help(self, bot, update):
        user_id = update.message.from_user.id
        if (len(self.groups.get_groups()) > 0 and not self.groups.user_in_groups(bot, user_id)) or not self.users.is_valid_user(user_id):
            self.handle_start(bot, update)
            return
        help_text = ["Hi! I'm @metafetish_bot, the bot for the Metafetish Telegram Group Network.",
                     "",
                     "Here's a list of commands I support:",
                     "",
                     self.definitions.commands(),
                     self.users.commands()]
        bot.sendMessage(update.message.chat.id,
                        "\n".join(help_text),
                        parse_mode="HTML")

    def handle_settings(self, bot, update):
        pass

    def handle_error(self, bot, update, error):
        self.logger.warn("Exception thrown! %s", self.error)

    def try_register(self, bot, update):
        user_id = update.message.from_user.id
        if not self.users.is_valid_user(user_id):
            self.users.register(bot, update)
        # Always returns true, as running any command will mean the user is
        # registered. We just want to make sure they're in the DB so flags can
        # be added if needed.
        return True

    def require_group(self, bot, update):
        # Special Case: If the bot has no users yet, we need to let the first
        # user register so they can be an admin. After that, always require
        # membership
        if self.users.get_num_users() == 0:
            return True
        if len(self.groups.get_groups()) == 0:
            return True
        user_id = update.message.from_user.id
        if not self.groups.user_in_groups(bot, user_id):
            bot.sendMessage(update.message.chat.id,
                            text="Please join the 'metafetish' group to use this bot! http://telegram.me/metafetish")
            return False
        return True

    # When used with PermissionCommandHandler, Function requires currying with
    # flag we want to check for.
    def require_flag(self, bot, update, flag):
        user_id = update.message.from_user.id
        if not self.users.has_flag(user_id, flag):
            bot.sendMessage(update.message.chat.id,
                            text="You do not have the required permissions to run this command.")
            return False
        return True

    def require_privmsg(self, bot, update):
        if update.message.chat.id < 0:
            bot.sendMessage(update.message.chat.id,
                            reply_to_message_id=update.message.id,
                            text="Please message that command to me. Only the following commands are allowed in public chats:\n- /def")
            return False
        return True

    def output_commands(self, bot, update):
        command_str = ""
        for m in self.modules:
            command_str += m.commands() + "\n"
        bot.sendMessage(update.message.chat.id,
                        text=command_str)

    def handle_message(self, bot, update):
        # Ignore messages from groups
        if update.message.chat.id < 0:
            return
        if self.conversations.check(bot, update):
            return
        self.try_register(bot, update)
        self.handle_help(bot, update)

    def handle_cancel(self, bot, update):
        if update.message.chat.id < 0:
            return
        if not self.conversations.cancel_conversation(bot, update):
            bot.sendMessage(update.message.chat.id,
                            text="Don't have anything to cancel!")
            self.handle_help(bot, update)
            return
        bot.sendMessage(update.message.chat.id,
                        text="Command canceled!")

    def start_loop(self):
        self.updater.start_polling()
        self.updater.idle()

    def shutdown(self):
        for m in self.modules:
            m.shutdown()


class MetafetishTelegramBotCLI(MetafetishTelegramBot):
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
                tg_token = f.readline().strip()
        except:
            print("Cannot open token file!")
            raise RuntimeError()

        if not args.dbdir or not os.path.isdir(args.dbdir):
            print("Valid database directory required!")
            parser.print_help()
            raise RuntimeError()

        super().__init__(args.dbdir, tg_token)
