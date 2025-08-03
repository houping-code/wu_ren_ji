import json
import random
import queue
import base64
import threading
from modules import logger
from modules import message
from modules import database
from modules import sm4

clientPool = {}


def init():
    # 启动消息接收线程
    threading.Thread(target=messageRecvService).start()

    logger.info("飞行控制服务初始化成功！")


def messageRecvService():
    while True:
        messageBytes = message.recv()
        messagePackage = json.loads(messageBytes.decode())

        clientName = messagePackage.get("clientName")
        dataType = messagePackage.get("dataType")
        dataPackage = messagePackage.get("dataPackage")

        if clientName not in clientPool:
            clientPool[clientName] = {"dataQueue": queue.Queue(), "exit": False}
            logger.info(f"{clientName}成功连接！")

        dataQueue = clientPool.get(clientName).get('dataQueue')
        dataQueue.put(dataPackage)


def messageSend(clientName, dataType, data):
    sendData = {"dataType": dataType, "dataPackage": data}
    message.send(clientName, sendData)

def flightControl(clientName, flyCommand, isEncrypt, isPlan=False): #修改flightControl方法，添加isPlan参数
    if isEncrypt:
        key = database.queryIdentityKey(clientName)
        if key:
            flyCommandBytes = json.dumps(flyCommand).encode()
            encryptedDataBytes = sm4.encrypt(key.encode(), flyCommandBytes)
            encryptedData = base64.b64encode(encryptedDataBytes).decode()

            flyCommand = {"data": encryptedData, "encrypt": True}
            messageSend(clientName, "service", flyCommand)
            result = {"clientName": clientName, "status": "success", "msg": "成功发送加密飞行控制指令！",
                      "time": random.random()}
        else:
            logger.error(f"未查询到{clientName}的密钥，已自动切换为未加密模式！")

            flyCommand = {"data": flyCommand, "encrypt": False}
            messageSend(clientName, "service", flyCommand)
            result = {"clientName": clientName, "status": "error", "msg": "未查询到密钥，自动切换为未加密模式！",
                      "time": random.random()}
    else:
        if isPlan:  #如果为任务规划任务
            flyCommand = {"data": flyCommand, "encrypt": False}
            logger.info(f"已发送任务控制指令：{flyCommand}")
            messageSend(clientName, "plan", flyCommand)
            result = {"clientName": clientName, "status": "success", "msg": "执行成功！", "time": random.random()}
        else:
            logger.info("成功到了飞机控制处")
            flyCommand = {"data": flyCommand, "encrypt": False}
            messageSend(clientName, "service", flyCommand)
            logger.info("消息发送到了无人机端")
            result = {"clientName": clientName, "status": "success", "msg": "执行成功！", "time": random.random()}

    return result

