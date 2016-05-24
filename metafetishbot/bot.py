from telegram.ext import Updater
from .definitions import DefinitionManager
import argparse
import os


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

        self.updater = Updater(token=tg_token)
        self.dispatcher = self.updater.dispatcher
        self.definer = DefinitionManager(self.dispatcher, args.dbdir)

    def start_loop(self):
        self.updater.start_polling()
        self.updater.idle()

    def shutdown(self):
        self.definer.shutdown()
