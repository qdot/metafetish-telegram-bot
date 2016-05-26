import os
from telegram.ext import CommandHandler
from .pickledb import pickledb
import cgi


class DefinitionManager(object):
    def __init__(self, dbdir):
        defsdir = os.path.join(dbdir, "definitions")
        if not os.path.isdir(defsdir):
            os.makedirs(defsdir)
        self.db = pickledb(os.path.join(defsdir, "definitions.db"), True)

    def register_with_dispatcher(self, dispatcher):
        dispatcher.add_handler(CommandHandler('def', self.show))
        dispatcher.add_handler(CommandHandler('def_show', self.show))
        dispatcher.add_handler(CommandHandler('def_add', self.add))
        dispatcher.add_handler(CommandHandler('def_rm', self.rm))

    def help(self, bot, update):
        bot.sendMessage(update.message.chat_id,
                        text="This is not helpful.")

    def show(self, bot, update):
        def_name = cgi.escape(update.message.text.partition(" ")[2].strip().lower())
        if self.db.get(def_name) is None:
            bot.sendMessage(update.message.chat_id,
                            text='No definition available for %s' %
                            (def_name),
                            parse_mode="HTML")
            return
        def_str = "Definition for <i>%s</i>:\n" % (def_name)
        i = 1
        def_text = self.db.lgetall(def_name)
        for d in def_text:
            def_str += "<b>%d.</b> %s\n" % (i, d["desc"])
            i += 1
        bot.sendMessage(update.message.chat_id,
                        text=def_str,
                        parse_mode="HTML")

    def add(self, bot, update):
        command = update.message.text.partition(" ")[2]
        (def_name, def_part, def_add) = command.partition(" ")
        def_name = cgi.escape(def_name.strip().lower())
        def_add = cgi.escape(def_add.strip())
        if self.db.get(def_name) is None:
            bot.sendMessage(update.message.chat_id,
                            text='Adding definition:\n<i>%s</i>\n for term <i>%s</i>.' %
                            (def_add, def_name),
                            parse_mode="HTML")
            self.db.lcreate(def_name)
        else:
            bot.sendMessage(update.message.chat_id,
                            text='Definition for <i>%s</i> already exists, extending with definition <i>%s</i>.' %
                            (def_name, def_add),
                            parse_mode="HTML")
        d = {"user": update.message.from_user.id,
             "desc": def_add.strip()}
        self.db.ladd(def_name, d)

    def rm(self, bot, update):
        command = update.message.text.partition(" ")[2]
        (def_name, def_part, def_rm) = command.partition(" ")
        def_name = cgi.escape(def_name.strip().lower())
        if self.db.get(def_name) is None:
            bot.sendMessage(update.message.chat_id,
                            text='No definition available for <i>%s</i>' %
                            (def_name),
                            parse_mode="HTML")
            return
        try:
            def_id = int(def_rm) - 1
            self.db.lpop(def_name, def_id)
        except:
            bot.sendMessage(update.message.chat_id,
                            text='Index %s is not valid for definition <i>%s</i>.' %
                            (def_rm, def_name),
                            parse_mode="HTML")
            return
        if self.db.llen(def_name) is 0:
            self.db.lrem(def_name)
        bot.sendMessage(update.message.chat_id,
                        text='Index %s for definition <i>%s</i> deleted.' %
                        (def_rm, def_name),
                        parse_mode="HTML")

    def shutdown(self):
        self.db.dump()
