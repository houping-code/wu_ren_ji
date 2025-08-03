import json
import threading
import queue
from modules.RabbitMQClient import RabbitMQClient

rabbitMQ = None
recvQueueDict = {}
sendQueue = queue.Queue()


def init():
    global rabbitMQ, recvQueueDict
    with open("config.json", "r") as fp:
        config = json.loads(fp.read())
        clientName = config.get("clientName")
        rabbitMQHost = config.get("service").get("message").get("rabbitMQ").get("host")
        rabbitMQPort = config.get("service").get("message").get("rabbitMQ").get("port")
        rabbitMQUserName = config.get("service").get("message").get("rabbitMQ").get("userName")
        rabbitMQPassword = config.get("service").get("message").get("rabbitMQ").get("password")
        serviceTypeList = list(config["service"].keys())

    # 创建rabbitMQ对象
    rabbitMQ = RabbitMQClient(host=rabbitMQHost, port=rabbitMQPort, userName=rabbitMQUserName,
                              password=rabbitMQPassword,
                              client_name=clientName)
    for serviceType in serviceTypeList:
        recvQueueDict[serviceType] = queue.Queue()

    # 开启消息接收线程
    threading.Thread(target=rabbitMQ.receive, args=(dataReceiveCallBack,)).start()

    # 开启消息发送线程
    threading.Thread(target=dataSendService).start()


def dataReceiveCallBack(ch, method, properties, body):
    messagePackage = json.loads(body.decode())

    serviceType = messagePackage.get("serviceType")

    recvQueueDict[serviceType].put(messagePackage)


def dataSendService():
    """
    持续从发送队列中获取数据并调用rabbitmq的send方法发送。
    :return: 无
    """
    while True:
        serviceType, data = sendQueue.get()
        rabbitMQ.send(serviceType, data)


def send(serviceType, data):
    """
    外部调用的发送数据方法，将其加入发送队列
    :param serviceType:
    :param data:
    :return:
    """
    sendQueue.put((serviceType, data))


def recv(serviceType):
    return recvQueueDict[serviceType].get()
