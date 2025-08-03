import base64
import json
import threading
from modules import message
from modules.DataBase import DataBase
from flight_control import logger
from flight_control import sm4

with open("config.json", "r") as fp:
    config = json.loads(fp.read())
    serviceName = config.get("service").get("flightControl").get("rabbitMQName")

    clientName = config.get("clientName")
    defaultTakeOffAltitude = config.get("service").get("flightControl").get("defaultTakeOffAltitude")

database = DataBase()
g_uav = None
continueEvent = threading.Event()
continueEvent.set()


def init(uav):
    global g_uav
    g_uav = uav

    with open("config.json", "r") as fp:
        config = json.loads(fp.read())

        path = config.get("service").get("flightControl").get("logger").get("path")
        logLevel = config.get("service").get("flightControl").get("logger").get("level")

    # 初始化log模块
    logger.init(path, logLevel)

    # 启动消息接收线程
    threading.Thread(target=messageRecvService).start()

    logger.info("飞行控制服务初始化成功！")


def messageRecvService():
    while True:
        messagePackage = message.recv(serviceName)

        dataType = messagePackage.get("dataType")
        dataPackage = messagePackage.get("dataPackage")

        if dataType == "service":
            logger.info(f"接收到服务器发送的控制指令：{dataPackage}")
            checkAndDecryptPackage(dataPackage)
        if dataType == "plan":  # 如果为任务规划，直接执行missionPlan
            logger.info(f"接收到服务器发送的任务规划指令：{dataPackage}")
            missionPlan(dataPackage)


def messageSend(dataType, data):
    sendData = json.dumps({"clientName": clientName, "dataType": dataType, "dataPackage": data}).encode()
    message.send(serviceName, sendData)


def checkAndDecryptPackage(dataPackage):
    """
    检查控制数据包是否加密。如果为加密数据包，则进行解密；如果为不加密数据包，则直接执行。
    :param dataPackage: 数据包
    :return: 无
    """
    data = dataPackage.get("data")
    isEncrypt = dataPackage.get("encrypt")
    if isEncrypt:
        key = database.queryIdentityKey(clientName)
        if key:
            key = key.encode()

            encryptedDataBytes = base64.b64decode(data.encode())
            decryptedDataBytes = sm4.decrypt(key, encryptedDataBytes)
            if decryptedDataBytes:
                decryptedData = json.loads(decryptedDataBytes.decode())
                flightControl(decryptedData)
            else:
                logger.error("解密控制指令失败，请检查密钥是否相同！")
        else:
            logger.error("未查询到加密密钥，解密控制指令失败！")
    else:
        flightControl(data)


def flightControl(flyCommand):
    """
    无人机飞行控制
    :param flyCommand:
    :return:
    """
    x = flyCommand.get("x")
    y = flyCommand.get("y")
    z = flyCommand.get("z")
    specialInstruction = flyCommand.get("specialInstruction")

    if specialInstruction == "takeOff":
        if g_uav.inAir:
            logger.error("无人机已经起飞，请不要再下达起飞指令！")
        else:
            ##g_uav.arm_and_takeoff(defaultTakeOffAltitude)
            logger.info("无人机成功起飞！")

    elif specialInstruction == "land":
        g_uav.land()
    elif specialInstruction == "continue start":
        logger.info(f"无人机将持续飞行，X方向：{x}，Y方向：{z}，Z方向：{z}")
        continueEvent.set()
        threading.Thread(target=g_uav.move_continuous, args=(continueEvent, x, y, z)).start()  # 向前飞1米
    elif specialInstruction == "continue stop":
        logger.info(f"无人机将停止持续飞行")
        continueEvent.clear()
    else:
        logger.info(f"无人机将飞行，X方向：{x}，Y方向：{z}，Z方向：{z}")
        g_uav.move_relative(x, y, z)


def missionPlan(dataPackage):  # 任务规划方法
    data = dataPackage.get("data").get("waypoints")
    if g_uav.upload_mission(data, return_to_launch=True):
        g_uav.execute_mission()
        g_uav.wait_mission_complete()
