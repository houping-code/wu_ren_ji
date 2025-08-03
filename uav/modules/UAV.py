import time
from pymavlink import mavutil
from trust_start import trustStart


class UAV:
    def __init__(self, rate=4, jumpTrustStart=False):
        """
        初始化无人机连接和参数

        参数:
            rate (int): 数据流速率，默认值为4
            jumpTrustStart (bool): 是否跳过可信启动流程，默认值为False
        """
        if jumpTrustStart:
            self.controlMavlink = mavutil.mavlink_connection("/dev/ttyACM1")
            self.dataMavlink = mavutil.mavlink_connection("/dev/ttyACM0")

            self.wait_heartbeat()

            self.controlMavlink.mav.request_data_stream_send(self.controlMavlink.target_system,
                                                             self.controlMavlink.target_component,
                                                             mavutil.mavlink.MAV_DATA_STREAM_ALL,
                                                             rate,
                                                             1)
            self.dataMavlink.mav.request_data_stream_send(self.dataMavlink.target_system,
                                                          self.dataMavlink.target_component,
                                                          mavutil.mavlink.MAV_DATA_STREAM_ALL,
                                                          rate,
                                                          1)
            self.inAir = False
            self.clear_mission()
        else:
            # 可信启动成功前不连接无人机，每秒检查一次可信启动状态
            while trustStart.getTrustStartStatus() is None:
                time.sleep(1)

            # 可信启动后更新无人机状态
            if trustStart.getTrustStartStatus() == "success":
                time.sleep(2)  # 等待固件初始化
                self.controlMavlink = mavutil.mavlink_connection("/dev/ttyACM1")
                self.dataMavlink = mavutil.mavlink_connection("/dev/ttyACM0")
                self.wait_heartbeat()
                self.controlMavlink.mav.request_data_stream_send(self.controlMavlink.target_system,
                                                                 self.controlMavlink.target_component,
                                                                 mavutil.mavlink.MAV_DATA_STREAM_ALL,
                                                                 rate,
                                                                 1)
                self.dataMavlink.mav.request_data_stream_send(self.dataMavlink.target_system,
                                                              self.dataMavlink.target_component,
                                                              mavutil.mavlink.MAV_DATA_STREAM_ALL,
                                                              rate,
                                                              1)
                self.inAir = False
                self.clear_mission()

    def wait_heartbeat(self):
        """等待第一个心跳包"""
        print("等待心跳包...")
        self.controlMavlink.wait_heartbeat()
        self.dataMavlink.wait_heartbeat()
        print("已收到心跳包!")

    def get_current_mode(self):
        """
        获取当前飞行模式

        返回:
            str: 当前飞行模式名称，如果获取失败则返回None
        """
        try:
            # 定义飞行模式映射（custom_mode值到模式名称的映射）
            mode_mapping = {
                0: 'STABILIZE',
                3: 'AUTO',
                4: 'GUIDED',
                5: 'LOITER',
                6: 'RTL',
                9: 'LAND'
            }

            for _ in range(5):
                # 获取心跳包
                msg = self.controlMavlink.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
                if msg:
                    # 获取custom_mode值并映射到对应的模式名称
                    mode = mode_mapping.get(msg.custom_mode)
                    if mode:
                        return mode
                    else:
                        print(f"未知的飞行模式值: {msg.custom_mode}")
                        return None
            # 未能获取飞行模式
            return None

        except Exception as e:
            print(f"获取飞行模式失败: {str(e)}")
            return None

    def arm_and_takeoff(self, target_altitude):
        """
        解锁并起飞到目标高度

        参数:
            target_altitude (float): 目标高度(米)
        返回:
            bool: 是否起飞成功
        """
        try:
            print("准备起飞...")

            self.controlMavlink.set_mode_apm("GUIDED")

            # 检查GPS状态
            gps = self.dataMavlink.recv_match(type='GPS_RAW_INT', blocking=True, timeout=1)
            if not gps or gps.fix_type < 3:
                print("GPS信号不足，无法起飞")
                return False

            # 解锁
            print("解锁电机...")
            if not self.controlMavlink.motors_armed():
                self.controlMavlink.arducopter_arm()
                self.controlMavlink.motors_armed_wait()
            print("电机已解锁")

            # 起飞命令
            print(f"开始起飞，目标高度 {target_altitude} 米...")
            self.controlMavlink.mav.command_long_send(
                self.controlMavlink.target_system,
                self.controlMavlink.target_component,
                mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
                0, 0, 0, 0, 0, 0, 0, target_altitude
            )

            # 等待到达目标高度
            print("等待到达目标高度...")
            timeout = time.time() + 30  # 30秒超时
            last_alt = 0
            while True:
                if time.time() > timeout:
                    print("起飞超时")
                    return False

                sensorsData = self.getSensorsData()
                if sensorsData:
                    current_altitude = sensorsData['gps']['relative_alt']
                    # 只在高度变化超过0.5米时打印
                    if abs(current_altitude - last_alt) > 0.5:
                        print(f"当前高度: {current_altitude:.1f}m")
                        last_alt = current_altitude

                    if abs(current_altitude - target_altitude) < 0.5:  # 允许0.5米误差
                        break
                time.sleep(0.5)

            print(f"已到达目标高度 {target_altitude} 米")
            self.inAir = True
            return True

        except Exception as e:
            print(f"起飞过程出错: {str(e)}")
            return False

    def land(self):
        """
        降落到地面

        返回:
            bool: 是否降落成功
        """
        try:
            print("开始降落...")

            # 发送降落命令
            self.controlMavlink.mav.command_long_send(
                self.controlMavlink.target_system,
                self.controlMavlink.target_component,
                mavutil.mavlink.MAV_CMD_NAV_LAND,
                0, 0, 0, 0, 0, 0, 0, 0
            )

            # 等待降落完成
            timeout = time.time() + 120  # 120秒超时
            last_alt = 999
            while True:
                if time.time() > timeout:
                    print("降落超时")
                    return False

                sensorsData = self.getSensorsData()
                if sensorsData:
                    current_altitude = sensorsData['gps']['relative_alt']

                    # 只在高度变化超过0.5米时打印
                    if abs(current_altitude - last_alt) > 0.5:
                        print(f"当前高度: {current_altitude:.1f}m")
                        last_alt = current_altitude

                    # 检测是否着陆
                    if current_altitude < 0.3:  # 高度小于0.3米认为已着陆
                        # 等待电机停止
                        time.sleep(2)
                        if not self.controlMavlink.motors_armed():
                            break

                time.sleep(0.5)

            print("降落完成")
            self.inAir = False
            return True

        except Exception as e:
            print(f"降落过程出错: {str(e)}")
            return False

    def move_continuous(self, event, forward=0, right=0, down=0):
        """
        持续移动无人机直到用户输入停止
        参数:
            forward (float): 前进速度(米/秒),正值前进,负值后退
            right (float): 右移速度(米/秒),正值右移,负值左移
            down (float): 下降速度(米/秒),正值下降,负值上升
        """
        self.controlMavlink.set_mode_apm("GUIDED")

        print(f"无人机将以速度前进{forward}米/秒，右移{right}米/秒，下降{down}米/秒")
        type_mask = 0b010111000111  # 使用速度控制
        while event.is_set():
            self.controlMavlink.mav.set_position_target_local_ned_send(
                0,  # 时间戳
                self.controlMavlink.target_system,  # 目标系统
                self.controlMavlink.target_component,  # 目标组件
                mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED,  # 坐标系
                type_mask,  # 类型掩码
                0, 0, 0,  # x, y, z位置
                forward, right, down,  # x, y, z速度
                0, 0, 0,  # x, y, z加速度
                0, 0  # 偏航角,偏航角速率
            )
            time.sleep(0.1)
        self.controlMavlink.mav.set_position_target_local_ned_send(
            0,  # 时间戳
            self.controlMavlink.target_system,  # 目标系统
            self.controlMavlink.target_component,  # 目标组件
            mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED,  # 坐标系
            type_mask,  # 类型掩码
            0, 0, 0,  # x, y, z位置
            0, 0, 0,  # x, y, z速度
            0, 0, 0,  # x, y, z加速度
            0, 0  # 偏航角,偏航角速率
        )

    def move_relative(self, forward=0, right=0, down=0):
        """
        相对当前位置移动无人机
        参数:
            forward (float): 前进距离(米),正值前进,负值后退
            right (float): 右移距离(米),正值右移,负值左移
            down (float): 下降距离(米),正值下降,负值上升
        """
        self.controlMavlink.set_mode_apm("GUIDED")
        print(f"无人机将向前进{forward}米，右移{right}米，下降{down}米")
        type_mask = 0b010111111000  # 使用位置控制
        self.controlMavlink.mav.set_position_target_local_ned_send(
            0,  # 时间戳
            self.controlMavlink.target_system,  # 目标系统
            self.controlMavlink.target_component,  # 目标组件
            mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED,  # 坐标系
            type_mask,  # 类型掩码
            forward, right, down,  # x, y, z位置
            0, 0, 0,  # x, y, z速度
            0, 0, 0,  # x, y, z加速度
            0, 0  # 偏航角,偏航角速率
        )

    def read_mission(self):
        # 验证上传的航点
        print("\n开始读取上传的航点...")
        self.controlMavlink.mav.mission_request_list_send(
            self.controlMavlink.target_system,
            self.controlMavlink.target_component
        )

        msg = self.controlMavlink.recv_match(type=['MISSION_COUNT'], blocking=True)
        if msg:
            count = msg.count
            print(f"总航点数：{count}")

            for i in range(count):
                self.controlMavlink.mav.mission_request_int_send(
                    self.controlMavlink.target_system,
                    self.controlMavlink.target_component,
                    i
                )
                msg = self.controlMavlink.recv_match(type=['MISSION_ITEM_INT'], blocking=True)
                if msg:
                    if msg.command == mavutil.mavlink.MAV_CMD_NAV_TAKEOFF:
                        print(
                            f"航点 {i + 1}: 起飞点 - 纬度={msg.x / 1e7:.7f}, 经度={msg.y / 1e7:.7f}, 高度={msg.z:.1f}米")
                    elif msg.command == mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH:
                        print(f"航点 {i + 1}: RTL (返航点)")
                    else:
                        print(f"航点 {i + 1}: 纬度={msg.x / 1e7:.7f}, 经度={msg.y / 1e7:.7f}, 高度={msg.z:.1f}米")

    def clear_mission(self):
        print("正在清除已有航点任务...")
        self.controlMavlink.mav.mission_clear_all_send(
            self.controlMavlink.target_system,
            self.controlMavlink.target_component
        )
        time.sleep(1)
        print("已有航点任务已清除")

    def upload_mission(self, waypoints, return_to_launch=False):
        """
        上传航点任务

        参数:
            waypoints: 航点列表，每个航点包含 lat(纬度)、lon(经度)、alt(高度)
            return_to_launch: 是否在任务完成后返航
        返回:
            bool: 是否上传成功
        """
        print("开始上传航点任务...")

        # 准备任务项
        mission_items = []

        # 添加起飞点作为第一个航点
        home = {'lat': waypoints[0]['lat'], 'lon': waypoints[0]['lon'], 'alt': 15}
        mission_items.append({
            'command': mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
            'current': 0,
            'autocontinue': True,
            'param1': 0,  # 最小俯仰角
            'param2': 0,  # 空
            'param3': 0,  # 空
            'param4': 0,  # 偏航角
            'x': home['lat'],
            'y': home['lon'],
            'z': home['alt']
        })

        # 添加用户定义的航点
        for wp in waypoints:
            mission_items.append({
                'command': mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                'current': 0,
                'autocontinue': True,
                'param1': 0,  # 停留时间
                'param2': 2,  # 接受半径(m)
                'param3': 0,  # 通过半径(m)
                'param4': float('nan'),  # 期望偏航角(rad)
                'x': wp['lat'],
                'y': wp['lon'],
                'z': wp['alt']
            })

        # 如果需要返航，添加RTL点
        if return_to_launch:
            mission_items.append({
                'command': mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH,
                'current': 0,
                'autocontinue': True,
                'param1': 0,
                'param2': 0,
                'param3': 0,
                'param4': 0,
                'x': 0,
                'y': 0,
                'z': 0
            })

        # 清除已有任务
        self.clear_mission()

        # 设置任务数量
        self.controlMavlink.mav.mission_count_send(
            self.controlMavlink.target_system,
            self.controlMavlink.target_component,
            len(mission_items)
        )

        # 等待mission_request并发送航点
        for i, item in enumerate(mission_items):
            msg = self.controlMavlink.recv_match(type=['MISSION_REQUEST'], blocking=True)
            if msg is None:
                print("上传航点失败：未收到MISSION_REQUEST")
                return False

            self.controlMavlink.mav.mission_item_int_send(
                self.controlMavlink.target_system,
                self.controlMavlink.target_component,
                i,
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                item['command'],
                item['current'],
                item['autocontinue'],
                item['param1'],
                item['param2'],
                item['param3'],
                item['param4'],
                int(item['x'] * 1e7),
                int(item['y'] * 1e7),
                float(item['z'])
            )

        # 等待mission_ack
        msg = self.controlMavlink.recv_match(type=['MISSION_ACK'], blocking=True)
        if msg is None:
            print("上传航点失败：未收到MISSION_ACK")
            return False

        print("\n航点任务上传成功" + (" (任务结束后将返航)" if return_to_launch else ""))
        return True

    def execute_mission(self, takeoff_altitude=10):
        """
        执行已上传的航点任务
        :param takeoff_altitude: 起飞高度
        :return bool: 是否执行成功
        """
        print("等待GPS初始化...")

        # 等待GPS信号
        while True:
            msg = self.dataMavlink.recv_match(type=['GPS_RAW_INT'], blocking=True)
            if msg and msg.fix_type >= 3:
                print("GPS已锁定")
                break
            time.sleep(1)

        if self.arm_and_takeoff(takeoff_altitude):

            self.controlMavlink.set_mode_apm("AUTO")

            # 开始任务
            self.controlMavlink.mav.command_long_send(
                self.controlMavlink.target_system,
                self.controlMavlink.target_component,
                mavutil.mavlink.MAV_CMD_MISSION_START,
                0, 0, 0, 0, 0, 0, 0, 0
            )

            self.inAir = True

            print("航点任务开始执行")
            return True
        else:
            print("无法起飞，任务执行失败")

    def wait_mission_complete(self):
        """
        等待航点任务完成，只有在设定航点结束后自动返回才可以使用

        返回:
            bool: 任务是否成功完成
        """
        print("等待航点任务结束...")

        startMission = 0
        timeout = time.time() + 600  # 10分钟超时

        while True:
            if time.time() > timeout:
                print("任务执行超时")
                return False

            # 获取当前航点信息
            msg = self.dataMavlink.recv_match(type=['MISSION_CURRENT'], blocking=True)
            if msg is None:
                continue

            if msg.get_type() == 'MISSION_CURRENT':
                if msg.seq != 0 and startMission == 0:
                    startMission = 1

                if startMission and msg.seq == 0:
                    print("航点任务已完成")
                    return True

            time.sleep(0.1)

    def getSensorsData(self):
        """
        获取IMU传感器数据(加速度计、陀螺仪和磁力计)和GPS数据
       :return: dict 包含加速度计、陀螺仪、磁力计和GPS数据
       """
        imuData = self.dataMavlink.recv_match(type=['RAW_IMU'], blocking=True)
        gpsData = self.dataMavlink.recv_match(type=['GLOBAL_POSITION_INT'], blocking=True)
        if imuData is not None and gpsData is not None:
            return {
                "curTime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
                'accel': {
                    'x': imuData.xacc / 1000.0,  # 转换为g
                    'y': imuData.yacc / 1000.0,
                    'z': imuData.zacc / 1000.0
                },
                'gyro': {
                    'x': imuData.xgyro / 1000.0,  # 转换为rad/s
                    'y': imuData.ygyro / 1000.0,
                    'z': imuData.zgyro / 1000.0
                },
                'mag': {
                    'x': imuData.xmag,
                    'y': imuData.ymag,
                    'z': imuData.zmag
                },
                'gps': {
                    'lat': formatFloat(gpsData.lat / 1e7),  # 转换为度
                    'lon': formatFloat(gpsData.lon / 1e7),
                    'relative_alt': formatFloat(gpsData.relative_alt / 1000.0)  # 转换为米
                }
            }
        else:
            return None

    def get_data_periodically(self, interval=1):
        """
        以指定的时间间隔获取IMU数据和GPS数据
        :param interval: 获取数据的时间间隔（秒）
        """
        while True:
            sensorsData = self.getSensorsData()
            if sensorsData:
                print(f"传感器数据: {sensorsData}")
            time.sleep(interval)

    def get_current_mode_periodically(self, interval=1):
        while True:
            mode = self.get_current_mode()
            if mode:
                print(f"当前飞行模式: {mode}")
            time.sleep(interval)


def formatFloat(floatNum):
    """
    调整经纬度和高度，保证其长度在12字符以内
    :param floatNum:
    :return:
    """
    # 首先将数字转换为字符串
    numStr = str(floatNum)
    if len(numStr) <= 12:
        return floatNum

    # 如果数字中有负号，我们需要计算在内
    sign = '-' if floatNum < 0 else ''
    numStr = numStr.lstrip('-')

    if sign:
        maxLength = 11
    else:
        maxLength = 12

    # 分离整数部分和小数部分
    if '.' in numStr:
        integerPart, decimalPart = numStr.split('.')
    else:
        integerPart, decimalPart = numStr, ''

    # 如果整数部分长度大于或等于maxLength，那么我们只能保留整数部分并截断到maxLength个字符
    if len(integerPart) > maxLength:
        return sign + integerPart[:maxLength]

    # 否则，我们需要截断小数部分以确保总长度为11
    allowed_decimal_length = maxLength - len(integerPart) - 1  # 减1是为了考虑小数点
    formatted_num = f"{sign}{integerPart}.{decimalPart[:allowed_decimal_length]}"

    # 返回格式化后的数字，包含符号
    return float(formatted_num)


if __name__ == "__main__":
    uav = UAV(jumpTrustStart=True)

    waypoints = [
        {'lat': -35.36221784, 'lon': 149.16503088, 'alt': 15},
        {'lat': -35.36200450, 'lon': 149.16675199, 'alt': 20},
        {'lat': -35.36078056, 'lon': 149.16438375, 'alt': 10}
    ]

    # 上传航点任务并设置任务完成后返航
    if uav.upload_mission(waypoints, return_to_launch=True):
        uav.execute_mission()
