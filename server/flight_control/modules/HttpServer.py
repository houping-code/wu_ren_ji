from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from modules import logger
from modules import flightControl
from modules.mission_plan import draw_track, generate_mission_plan

import matplotlib.pyplot as plt
mission_cache = {}  # 格式：{ "uav01": [waypoint1, waypoint2, ...], ... }

class HttpServer(BaseHTTPRequestHandler):
    @classmethod
    def init(cls, host, port):
        httpd = HTTPServer((host, port), HttpServer)
        logger.info("http服务器初始化成功")
        httpd.serve_forever()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/favicon.ico':
            # 忽略 favicon.ico 请求
            self.send_response(200)
            self.send_header('Content-type', 'image/x-icon')
            self.end_headers()
            return

    def do_POST(self):
        try:
            params = self.rfile.read(int(self.headers['content-length']))
            params = json.loads(params)

            logger.info(f"接收到前端请求：{params}")

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
            self.end_headers()

            command = params.get("command")
            clientNameList = params.get("clientNameList")
            flyCommand = params.get("flyCommand")
            isEncrypt = params.get("encrypt")

            resultList = []
            if command == "start" or command == "stop":
                # 遍历列表，逐个处理
                for clientName in clientNameList:
                    result = flightControl.flightControl(clientName, flyCommand, isEncrypt)
                    resultList.append(result)
            if command == "plan":
                for clientName in clientNameList:
                    result = flightControl.flightControl(clientName, flyCommand, isEncrypt, isPlan=True)
                    resultList.append(result)
            if command == "mission_plan":
                area = flyCommand.get("area")
                waypoint_dict = generate_mission_plan(area, clientNameList)
                for client_name, waypoints in waypoint_dict.items():
                     mission_cache[client_name] = waypoints
                # draw_track(waypoint_dict,flyCommand)
                resultList = {
                    "status": "success",
                    "msg": "任务规划成功！",
                    "waypoints": waypoint_dict
                }
            if command == "mission_start":
                success = 0
                for clientName in clientNameList:
                    flyCommand_single = {
                        "waypoints": mission_cache[clientName]
                    }
                    result = flightControl.flightControl(clientName, flyCommand_single, isEncrypt, isPlan=True)
                    if result.get("status") == "success":
                        success = success + 1
                if success == len(clientNameList):
                    resultList.append({
                        "status": "success",
                        "msg": "执行成功！"
                    })
                else:
                    resultList.append({
                        "status": "failed",
                        "msg": "未连接到服务器！"
                    })

            self.wfile.write(json.dumps(resultList).encode('utf-8'))
            logger.info(f"响应前端：{json.dumps(resultList).encode('utf-8')}")
        except Exception as e:
            logger.error(f"处理POST请求时发生异常: {e}")
            self.send_response(400)
            self.end_headers()



