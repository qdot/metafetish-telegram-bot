from .pickledb import pickledb
import os
import logging


class GroupManager(object):
    def __init__(self, dbdir):
        groupsdir = os.path.join(dbdir, "groups")
        if not os.path.isdir(groupsdir):
            os.makedirs(groupsdir)
        self.db = pickledb(os.path.join(groupsdir, "groups.db"), True)
        self.logger = logging.getLogger(__name__)
        self.group_name = self.db.get("group_name")
        self.logger.warn("Now watching group %s" % (self.group_name))
        if not self.db.get("users"):
            self.db.dcreate("users")

    def set_group(self, bot, update):
        group_name = update.message.text.partition(" ")[2].strip().lower()
        try:
            bot.getChat(group_name)
            self.group_name = group_name
            self.db.set("group_name", group_name)
            self.db.dump()
            bot.sendMessage(update.message.chat_id,
                            text='Group %s set!' % (group_name))

        except:
            bot.sendMessage(update.message.chat_id,
                            text='Group %s not found!' % (group_name))

    def user_in_group(self, bot, user_id):
        self.logger.warn("Checking for user %d in group %s" % (user_id, self.group_name))
        try:
            user_status = self.db.dget("users", user_id)
            if user_status in ["creator", "administrator", "member"]:
                return True
        except:
            pass
        member = bot.getChatMember(self.group_name, user_id)
        self.db.dadd("users", (user_id, member.status))
        if member.status in ["creator", "administrator", "member"]:
            return True
        return False

    def update_group_list(self, bot, user_id):
        users = self.db.dkeys("users")
        for u in users:
            user_status = self.db.dget("users", u)
            member = bot.getChatMember(self.group_name, u)
            if user_status is not member.status:
                self.db.dadd("users", u, member.status)
