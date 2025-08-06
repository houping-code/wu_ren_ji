from modules import message
from modules.UAV import UAV
from flight_control import flightControl

if __name__ == "__main__":
    message.init()

    print("无人机的message初始化成功")

    uav = UAV(jumpTrustStart=True)

    print("无人机的uav初始化成功")

    flightControl.init(uav)

    print("无人机的飞行器初始化成功")