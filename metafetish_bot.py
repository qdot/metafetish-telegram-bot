from telegram.ext import Updater, CommandHandler
import logging
import time
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="I'm a bot, please talk to me!")


def main():
    try:
        with open("token.txt", "r") as f:
            tg_token = f.readline()[0:-1]
    except:
        print("Cannot open token file, exiting!")
        return 0

    updater = Updater(token=tg_token)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    try:
        updater.start_polling()
        while True:
            time.sleep(1000)
    except KeyboardInterrupt:
        pass
    updater.stop()
    print("Shutting down bot")


if __name__ == "__main__":
    main()
