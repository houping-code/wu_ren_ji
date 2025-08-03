import json
from modules import logger
from modules.HttpServer import HttpServer
from modules import message
from modules import flightControl

if __name__ == "__main__":
    with open("config.json", "r") as fp:
        config = json.loads(fp.read())

        serviceName = config.get("name")

        logFileName = config.get("logger").get("fileName")
        logLevel = config.get("logger").get("level")

        rabbitMQHost = config.get("rabbitMQ").get("host")
        rabbitMQPort = config.get("rabbitMQ").get("port")
        rabbitMQUserName = config.get("rabbitMQ").get("userName")
        rabbitMQPassword = config.get("rabbitMQ").get("password")

        httpServerHost = config.get("http").get("host")
        httpServerPort = config.get("http").get("port")

    # 初始化log模块
    logger.init(logFileName, logLevel)

    # 初始化消息队列
    message.init(rabbitMQHost, rabbitMQPort, rabbitMQUserName, rabbitMQPassword, serviceName)
    #
    # # 初始化飞行控制服务
    flightControl.init()

    # 初始化http服务器，必须在最后
    HttpServer.init(httpServerHost, httpServerPort)
