import logging
from logging.handlers import RotatingFileHandler


class Logger:
    def __init__(self, logFileName, logLevel):
        # 创建 logger
        self.logger = logging.getLogger(logFileName)

        if logLevel == "info":
            self.logger.setLevel(logging.INFO)
        elif logLevel == "debug":
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.WARNING)

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
        self.logger.addHandler(handler)

        self.logger.info("日志模块初始化成功")

    # 提供一些方便的函数
    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)
