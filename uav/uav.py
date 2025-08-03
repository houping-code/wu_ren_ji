from modules import message
from modules.UAV import UAV
from flight_control import flightControl

if __name__ == "__main__":
    message.init()
    uav = UAV(jumpTrustStart=True)
    flightControl.init(uav)