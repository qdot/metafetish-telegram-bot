from telegram.ext import Updater, CommandHandler
import logging
import pickledb

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class DefinitionManager(object):

    def __init__(self, dispatcher):
        self.db = pickledb.load("defines.db", True)

        dispatcher.add_handler(CommandHandler('def', self.def_show))
        dispatcher.add_handler(CommandHandler('def_show', self.def_show))
        dispatcher.add_handler(CommandHandler('def_add', self.def_add))
        dispatcher.add_handler(CommandHandler('def_rm', self.def_rm))

    def _contains_special_chars(self, defstr):
        """Returns True if string contains *[]()_`"""
        # Should probably do this as a regexp but eh.
        if any(c in defstr for c in ['(', ')', '*', '[', ']', '_', '`']):
            return True
        return False

    def send_char_error(self, bot, update):
        bot.sendMessage(update.message.chat_id,
                        text='The following characters are not allowed in definition queries: []()*_`')

    def def_show(self, bot, update):
        def_name = update.message.text.partition(" ")[2].strip()
        if self._contains_special_chars(def_name):
            self.send_char_error(bot, update)
            return
        if self.db.get(def_name) is None:
            bot.sendMessage(update.message.chat_id,
                            text='No definition available for %s' %
                            (def_name),
                            parse_mode="Markdown")
            return
        def_str = "Definition for _%s_:\n" % (def_name)
        i = 1
        def_text = self.db.lgetall(def_name)
        for d in def_text:
            def_str += "*%d.* %s\n" % (i, d["desc"])
            i += 1
        bot.sendMessage(update.message.chat_id,
                        text=def_str,
                        parse_mode="Markdown")

    def def_add(self, bot, update):
        command = update.message.text.partition(" ")[2]
        (def_name, def_part, def_add) = command.partition(" ")
        def_name = def_name.strip()
        def_add = def_add.strip()
        if (self._contains_special_chars(def_name) or self._contains_special_chars(def_add)):
            self.send_char_error(bot, update)
            return
        if self.db.get(def_name) is None:
            bot.sendMessage(update.message.chat_id,
                            text='Adding definition:\n_%s_\n for term _%s_.' %
                            (def_add,def_name),
                            parse_mode="Markdown")
            self.db.lcreate(def_name)
        else:
            bot.sendMessage(update.message.chat_id,
                            text='Definition for _%s_ already exists, extending with definition _%s_.' %
                            (def_name, def_add),
                            parse_mode="Markdown")
        d = {"user": update.message.from_user.id,
             "desc": def_add.strip()}
        self.db.ladd(def_name, d)

    def def_rm(self, bot, update):
        command = update.message.text.partition(" ")[2]
        (def_name, def_part, def_rm) = command.partition(" ")
        def_name = def_name.strip()
        if self._contains_special_chars(def_name):
            self.send_char_error(bot, update)
            return
        if self.db.get(def_name) is None:
            bot.sendMessage(update.message.chat_id,
                            text='No definition available for _%s_' %
                            (def_name),
                            parse_mode="Markdown")
            return
        try:
            def_id = int(def_rm) - 1
            self.db.lpop(def_name, def_id)
        except:
            bot.sendMessage(update.message.chat_id,
                            text='Index %s is not valid for definition _%s_.' %
                            (def_rm, def_name),
                            parse_mode="Markdown")
            return
        if self.db.llen(def_name) is 0:
            self.db.lrem(def_name)
        bot.sendMessage(update.message.chat_id,
                        text='Index %s for definition _%s_ deleted.' %
                        (def_rm, def_name),
                        parse_mode="Markdown")

    def shutdown(self):
        self.db.dump()


class MetafetishTelegramBot(object):

    def __init__(self):
        self.db = pickledb.load("bot.db", False)
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
        self.db.dump()
        self.definer.shutdown()


def main():
    print("Starting up bot")
    bot = MetafetishTelegramBot()
    bot.start_loop()
    bot.shutdown()
    print("Shutting down bot")


if __name__ == "__main__":
    main()
