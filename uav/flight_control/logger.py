from modules.Logger import Logger


def init(path, logLevel):
    global logger
    logger = Logger(path, logLevel)


# 提供一些方便的函数
def debug(message):
    logger.debug(message)


def info(message):
    print(message)
    logger.info(message)


def warning(message):
    print(message)
    logger.warning(message)


def error(message):
    print(message)
    logger.error(message)


def critical(message):
    print(message)
    logger.critical(message)
