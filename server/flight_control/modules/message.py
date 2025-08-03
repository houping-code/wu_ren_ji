import threading
import queue
import json
from modules.RabbitMQServer import RabbitMQServer
from modules import logger

rabbitMQ = None
g_messageQueue = queue.Queue()
g_serviceType = ""


def init(host, port, userName, password, serviceType):
    global rabbitMQ, g_serviceType

    g_serviceType = serviceType
    # 连接到RabbitMQ服务器
    try:
        rabbitMQ = RabbitMQServer(host=host, port=port, userName=userName, password=password, service_type=serviceType)
    except:
        logger.critical("连接RabbitMQ服务器失败")
        exit(0)

    # 启动消息接收线程
    threading.Thread(target=rabbitMQ.receive, args=(messageReceiveCallBack,)).start()
    logger.info("RabbitMQ服务初始化成功")


def send(clientName, data):
    """
    数据发送方法
    :param clientName: Python字符串类型，形如“UAV01”
    :param data: Python字典类型，形如{"dataType": dataType, "dataPackage": dataPackage}
    :return: 无
    """
    data["serviceType"] = g_serviceType
    dataBytes = json.dumps(data).encode()
    rabbitMQ.send(clientName, dataBytes)
    logger.info(f"向{clientName}发送消息：{data}")


def recv():
    clientData = g_messageQueue.get()
    return clientData


def messageReceiveCallBack(ch, method, properties, body):
    g_messageQueue.put(body)
    logger.info(f"接收到客户端消息：{body}")
