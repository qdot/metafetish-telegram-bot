import logging
from metafetishbot import MetafetishTelegramBot

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def main():
    print("Starting up bot")
    bot = MetafetishTelegramBot()
    bot.start_loop()
    bot.shutdown()
    print("Shutting down bot")


if __name__ == "__main__":
    main()
