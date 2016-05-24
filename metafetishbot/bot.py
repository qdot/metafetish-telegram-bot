from telegram.ext import Updater
from .definitions import DefinitionManager


class MetafetishTelegramBot(object):
    def __init__(self):
        try:
            with open("token.txt", "r") as f:
                tg_token = f.readline()[0:-1]
        except:
            print("Cannot open token file, exiting!")
            return 0

        self.updater = Updater(token=tg_token)
        self.dispatcher = self.updater.dispatcher
        self.definer = DefinitionManager(self.dispatcher)

    def start_loop(self):
        self.updater.start_polling()
        self.updater.idle()

    def shutdown(self):
        self.definer.shutdown()
