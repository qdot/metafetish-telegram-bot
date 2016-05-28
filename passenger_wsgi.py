# Make sure we're using the right python. Assume we're running out of the venv.

import sys
import os

INTERP = os.path.join(os.getcwd(), 'bin', 'python')
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)
    sys.path.append(os.getcwd())

sys.path.append(os.path.join(os.getcwd(), "metafetish-telegram-bot"))

import json

with open("config.json", "r") as f:
    config = json.load(f)

from flask import Flask, request
from metafetishbot import MetafetishTelegramBotThread

import telegram

# CONFIG
TOKEN    = config["token"]
HOST     = config["host"]
PORT     = config["port"]

db_path = os.path.join(os.getcwd(), "dbs")
if not os.path.exists(db_path):
    os.makedirs(db_path)
bot = MetafetishTelegramBotThread(db_path, TOKEN)
application = Flask(__name__)


@application.route('/')
def hello():
    return ""


@application.route('/' + TOKEN, methods=['POST'])
def webhook():
    update = telegram.update.Update.de_json(request.get_json(force=True))
    bot.update_queue.put(update)
    return 'OK'


def setWebhook():
    bot.updater.bot.setWebhook(webhook_url='https://%s/%s' % (HOST, TOKEN))

if __name__ == "__main__":
    setWebhook()
    application.run()
