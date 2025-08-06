import matplotlib.pyplot as plt



def generate_mission_plan(area, clientNameList):
    num_uav = len(clientNameList)
    total_sections = 2 * num_uav  # 不加 1

    waypoint_dict = {}

    # 区域边界
    lat_min = min(p["lat"] for p in area)
    lat_max = max(p["lat"] for p in area)
    lon_min = min(p["lon"] for p in area)
    lon_max = max(p["lon"] for p in area)

    lat_step = (lat_max - lat_min) / 2 if lat_max != lat_min else 0.0001
    lon_step = (lon_max - lon_min) / total_sections if lon_max != lon_min else 0.0001

    for idx, clientName in enumerate(clientNameList):
        # 起飞点为第 2*(idx+1) 块的中心
        start_center_idx = 2 * (idx + 1) - 1  # 因为 index 从 0 开始
        end_center_idx = start_center_idx - 1  # 飞往前一块

        start_lon = lon_min + (start_center_idx + 0.5) * lon_step
        end_lon = lon_min + (end_center_idx + 0.5) * lon_step
        alt = 30 + idx * 5

        waypoints = [
            {"lat": lat_min, "lon": start_lon, "alt": alt},
            {"lat": lat_max, "lon": start_lon, "alt": alt},
            {"lat": lat_max, "lon": end_lon,   "alt": alt},
            {"lat": lat_min, "lon": end_lon,   "alt": alt},
            # {"lat": lat_min, "lon": start_lon, "alt": alt},  # 回到起点闭环
        ]

        waypoint_dict[clientName] = waypoints

    return waypoint_dict



def draw_track(waypoints: dict, flyCommand: dict):
    """
    绘制 UAV 路径，并根据 flyCommand 中的 area 绘制边界框。

    参数:
        waypoints: dict, 每架 UAV 的飞行轨迹
    """
    if "area" not in flyCommand:
        raise ValueError("flyCommand 中缺少 'area' 字段")

    area_corners = flyCommand["area"]
    if len(area_corners) < 4:
        raise ValueError("area 至少应包含四个点")

    plt.figure(figsize=(8, 6))

    #绘制边界框
    border_lats = [p["lat"] for p in area_corners] + [area_corners[0]["lat"]]
    border_lons = [p["lon"] for p in area_corners] + [area_corners[0]["lon"]]
    plt.plot(border_lons, border_lats, 'k--', label="Defined Area")

    # 绘制 UAV 路径
    for uav, points in waypoints.items():
        lats = [p["lat"] for p in points]
        lons = [p["lon"] for p in points]
        plt.plot(lons, lats, marker='o', label=uav)
        plt.text(lons[0], lats[0], f"{uav} Start", fontsize=9, color='green')
        plt.text(lons[-1], lats[-1], f"{uav} End", fontsize=9, color='red')

    # 自动设定边界视图
    lats_all = [p["lat"] for p in area_corners]
    lons_all = [p["lon"] for p in area_corners]
    margin = 0.0003
    plt.xlim(min(lons_all) - margin, max(lons_all) + margin)
    plt.ylim(min(lats_all) - margin, max(lats_all) + margin)

    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("UAV Flight Tracks in Specified Area")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

