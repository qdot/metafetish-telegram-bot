from .pickledb import pickledb
import os
import logging


class MetafetishModuleBase(object):
    def __init__(self, dbdir, moduledbdir, logger_name, save_on_modify):
        self.logger = logging.getLogger(logger_name)
        finaldbdir = os.path.join(dbdir, moduledbdir)
        if not os.path.isdir(finaldbdir):
            os.makedirs(finaldbdir)
        dbpath = os.path.join(finaldbdir, moduledbdir + ".db")
        self.logger.debug("Opening db at %s" % dbpath)
        self.db = pickledb(dbpath, save_on_modify)

    def commands(self):
        return ""

    def shutdown(self):
        self.db.dump()
