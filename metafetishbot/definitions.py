from telegram.ext import CommandHandler
from .base import MetafetishPickleDBBase
import cgi


class DefinitionManager(MetafetishPickleDBBase):
    def __init__(self, dbdir):
        super().__init__(__name__, dbdir, "definitions", True)

    def register_with_dispatcher(self, dispatcher):
        dispatcher.add_handler(CommandHandler('def', self.show))
        dispatcher.add_handler(CommandHandler('def_show', self.show))
        dispatcher.add_handler(CommandHandler('def_add', self.add))
        dispatcher.add_handler(CommandHandler('def_rm', self.rm))

    def help(self, bot, update):
        bot.sendMessage(update.message.chat_id,
                        text="""
<b>Definitions Module</b>

The definitions module allows users to create definitions for words or phrases. This feature can used to reduce repeated questions about channel topics, or provide extra information in a persistent way.

Entering a new definition is as easy as using the /defadd command, though in order to curtail abuse, users will need special administrator granted permissions to add or remove definitions. The word or phrase being defined should contain no whitespace, but can contain any characters, even unicode or emoji.

Each word/phrase can have multiple definitions provided by multiple users.

For instance, to add a definition, the command would be:

/defadd DefiningDefinition This is a Definition

If we then showed the definition using:

/def DefiningDefinition

We'd get:

Definitions for <i>DefiningDefinition</i>:
<b>1.</b> This is a Definition

To remove that definition:

/defrm DefiningDefinition 1

Note that definition names are case insensitive for search, but will display as entered.

<b>Commands</b>

%s""" % (self.commands()),
                        parse_mode="HTML")

    def commands(self):
        return """/defhelp - Display definitions help message.
/def - Parameters: [word or phrase, no whitespace]. Show definition, if one exists.
/defadd - Parameters: [word or phrase, no whitespace] [definition]. Add or extend a definition.
/defrm - Parameters: [word or phrase, no whitespace] [index]. Remove a definition."""

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
                        parse_mode="HTML",
                        disable_web_page_preview=True)

    def add(self, bot, update):
        command = update.message.text.partition(" ")[2]
        (def_name, def_part, def_add) = command.partition(" ")
        def_name = cgi.escape(def_name.strip().lower())
        def_add = cgi.escape(def_add.strip())
        if self.db.get(def_name) is None:
            bot.sendMessage(update.message.chat_id,
                            text='Adding definition:\n<i>%s</i>\n for term <i>%s</i>.' %
                            (def_add, def_name),
                            parse_mode="HTML",
                            disable_web_page_preview=True)
            self.db.lcreate(def_name)
        else:
            bot.sendMessage(update.message.chat_id,
                            text='Definition for <i>%s</i> already exists, extending with definition <i>%s</i>.' %
                            (def_name, def_add),
                            parse_mode="HTML",
                            disable_web_page_preview=True)
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

    def list(self, bot, update):
        def_list = ", ".join([x for x in self.db.getall()])
        bot.sendMessage(update.message.chat_id,
                        text='Words/Phrases with definitions:\n%s' %
                        (def_list),
                        parse_mode="HTML",
                        disable_web_page_preview=True)
