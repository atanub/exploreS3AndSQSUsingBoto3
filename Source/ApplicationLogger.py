import sys

from ApplicationProperties import applicationConfig
from log4py import Logger


class AppLogger():
    def __init__(self, name):
        l = Logger(customconfigfiles="log4py.conf")

        self.__logger = l.get_instance(name)
        self.__logger.set_target(applicationConfig.logFilePath)
        self.__logger.add_target(sys.stdout)
        # self.__logger.set_formatstring(log4py.FMT_DEBUG)
        # self.__logger.set_loglevel(log4py.LOGLEVEL_DEBUG)
        # self.__logger.set_loglevel(log4py.LOGLEVEL_ERROR)
        # self.__logger.set_formatstring(log4py.FMT_LONG)

        # handler = RotatingFileHandler(app_properties.logFilePath, maxBytes=20, backupCount=5)
        # l.addHandler(handler)

    @property
    def logger(self):
        return self.__logger
