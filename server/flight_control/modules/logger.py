import logging
from logging.handlers import RotatingFileHandler

# 创建 logger
logger = logging.getLogger()


def init(logFileName, logLevel):
    global logger

    if logLevel == "info":
        logger.setLevel(logging.INFO)
    elif logLevel == "debug":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

    # 创建 RotatingFileHandler 并设置编码为 UTF-8
    handler = RotatingFileHandler(
        logFileName,
        maxBytes=1024 * 1024 * 5,  # 5MB
        backupCount=3,  # 最多保留3个备份文件
        encoding='utf-8'  # 设置编码为 UTF-8
    )

    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # 添加 handler 到 logger
    logger.addHandler(handler)

    logger.info("日志模块初始化成功")


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
