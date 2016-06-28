from telegram.ext import MessageHandler, Filters
from nptelegrambot import NPTelegramBot, ConversationHandler, PermissionCommandHandler
from nptelegrambot.chats import ChatFilters
from functools import partial


class MetafetishTelegramBot(NPTelegramBot):
    def __init__(self, config):
        super().__init__(config)

    def setup_commands(self):
        super().setup_commands()
        self.dispatcher.add_handler(MessageHandler([Filters.sticker],
                                                   self.handle_message),
                                    group=1)
        # self.dispatcher.add_handler(MessageHandler([Filters.text,
        #                                             Filters.sticker],
        #                                            self.chats.run_join_checks), group=4)

        # On errors, just print to console and hope someone sees it
        self.dispatcher.add_error_handler(self.handle_error)

    def handle_help(self, bot, update):
        help_text = ["Hi! I'm @metafetish_bot. I don't do much. Ignore me."]
        bot.sendMessage(update.message.chat.id,
                        "\n".join(help_text),
                        parse_mode="HTML",
                        disable_web_page_preview=True)


def create_webhook_bot(config):
    bot = MetafetishTelegramBot(config)
    bot.setup_commands()
    bot.start_webhook_thread()
    return bot
