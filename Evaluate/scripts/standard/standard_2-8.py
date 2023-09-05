# @Author           : zhang yu
# @Time             : 2023/06/06
# @Function         : standard_1plusX
# @Scenario         : 算法控制下到达终点总用时(实际用时+罚时)
# @Usage            : 算法比赛评分规则
# @UpdateTime       : 2023/06/06
# @UpdateUser       : zhang yu
import math
import traceback
import pandas as pd
import warnings
import json
from scipy.spatial.distance import euclidean
import logging

destination_x = -96
destination_y = -29  # 日新楼东南角到日新楼西门
path_point_x1 = 37
path_point_y1 = -26
path_point_x2 = -10
path_point_y2 = -51
path_point_x3 = -65
path_point_y3 = -80
path_point_x4 = -84
path_point_y4 = -52

t_min = 60
t_max = 2 * t_min

RDB_OBJECT_TYPE_PLAYER_CAR = 1
RDB_OBJECT_TYPE_PLAYER_PEDESTRIAN = 5
RDB_OBJECT_TYPE_BARRIER = 9
RDB_OBJECT_TYPE_PLAYER_MOTORBIKE = 13
RDB_OBJECT_TYPE_OTHER = 29

speed_limit_information = {
    "signalId": {
        1: 122638,
        2: 804261,
        3: 122646,
        4: 122748,
        5: 122627,
        6: 122644,
        7: 122750,
        8: 122641,
    },
    "roadId": {
        1: 8388783,
        2: 8388770,
        3: 8388764,
        4: 8388781,
        5: 8388784,
        6: 8388789,
        7: 8388829,
        8: 8388836,
    },
    "posX": {
        1: 166.493,
        2: -117.1,
        3: -73.2,
        4: 167.7,
        5: 68.2,
        6: 136.3,
        7: -277.8,
        8: 242.4,
    },
    "posY": {
        1: 35.72,
        2: -42.3,
        3: 85.7,
        4: 96.9,
        5: -5.8,
        6: 220.3,
        7: -61.4,
        8: 87.5,
    },
    "speedLimit": {
        1: 5,
        2: 5,
        3: 20,
        4: 20,
        5: 20,
        6: 20,
        7: 20,
        8: 20,
    }
}
stop_sign_information = {
    "signalId": {
        1: 122634,
    },
    "roadId": {
        1: 8388758,
    },
    "posX": {
        1: -50.6,
    },
    "posY": {
        1: 100.8,
    }
}
traffic_light_information = {
    "signalId": {
        1: 25166130,
        2: 25166134,
        3: 25166131,
        4: 25166132,
        5: 25166127,
        6: 25166133,
        7: 25166128,
        8: 25166129,
    },
    "ctrlRoadId": {
        1: 8388836,
        2: 8388789,
        3: 8388788,
        4: 8388839,
        5: 8388841,
        6: 8388758,
        7: 8388769,
        8: 8388767,
    },
    "nextRoad": {
        1: 8388752,
        2: 8388634,
        3: 8388753,
        4: 8388632,
        5: 8388757,
        6: 8388764,
        7: 8388628,
        8: 8388627,
    },
}


def timestamp(func):
    def wrapper(*args, **kwargs):
        global speed_limit_information
        global stop_sign_information
        global traffic_light_information
        global RDB_OBJECT_TYPE_PLAYER_CAR, RDB_OBJECT_TYPE_PLAYER_PEDESTRIAN, RDB_OBJECT_TYPE_BARRIER, \
            RDB_OBJECT_TYPE_PLAYER_MOTORBIKE, RDB_OBJECT_TYPE_OTHER
        global destination_x, destination_y, t_min, t_max
        # global path_point_x1, path_point_y1, path_point_x2, path_point_y2, path_point_x3, path_point_y3, path_point_x4, path_point_y4
        # destination_x = -82
        # destination_y = 76 #日新楼北侧停车让行标识牌处
        # path_point_x1 = destination_x
        # path_point_y1 = destination_y
        # path_point_x2 = destination_x
        # path_point_y2 = destination_y
        # path_point_x3 = destination_x
        # path_point_y3 = destination_y
        # path_point_x4 = destination_x
        # path_point_y4 = destination_y

        # destination_x = -98.4563
        # destination_y = -24.38786  # 日新楼东南角到日新楼西门
        # path_point_x1 = 37
        # path_point_y1 = -26
        # path_point_x2 = -10
        # path_point_y2 = -51
        # path_point_x3 = -65
        # path_point_y3 = -80
        # path_point_x4 = -84
        # path_point_y4 = -52
        #
        # t_min = 60
        # t_max = 2 * t_min
        #
        # RDB_OBJECT_TYPE_PLAYER_CAR = 1
        # RDB_OBJECT_TYPE_PLAYER_PEDESTRIAN = 5
        # RDB_OBJECT_TYPE_BARRIER = 9
        # RDB_OBJECT_TYPE_PLAYER_MOTORBIKE = 13
        # RDB_OBJECT_TYPE_OTHER = 29
        #
        # speed_limit_information = {
        #     "signalId": {
        #         1: 122638,
        #         2: 804261,
        #         3: 122646,
        #         4: 122748,
        #         5: 122627,
        #         6: 122644,
        #         7: 122750,
        #         8: 122641,
        #     },
        #     "roadId": {
        #         1: 8388783,
        #         2: 8388770,
        #         3: 8388764,
        #         4: 8388781,
        #         5: 8388784,
        #         6: 8388789,
        #         7: 8388829,
        #         8: 8388836,
        #     },
        #     "posX": {
        #         1: 166.493,
        #         2: -117.1,
        #         3: -73.2,
        #         4: 167.7,
        #         5: 68.2,
        #         6: 136.3,
        #         7: -277.8,
        #         8: 242.4,
        #     },
        #     "posY": {
        #         1: 35.72,
        #         2: -42.3,
        #         3: 85.7,
        #         4: 96.9,
        #         5: -5.8,
        #         6: 220.3,
        #         7: -61.4,
        #         8: 87.5,
        #     },
        #     "speedLimit": {
        #         1: 5,
        #         2: 5,
        #         3: 20,
        #         4: 20,
        #         5: 20,
        #         6: 20,
        #         7: 20,
        #         8: 20,
        #     }
        # }
        # stop_sign_information = {
        #     "signalId": {
        #         1: 122634,
        #     },
        #     "roadId": {
        #         1: 8388758,
        #     },
        #     "posX": {
        #         1: -50.6,
        #     },
        #     "posY": {
        #         1: 100.8,
        #     }
        # }
        # traffic_light_information = {
        #     "signalId": {
        #         1: 25166130,
        #         2: 25166134,
        #         3: 25166131,
        #         4: 25166132,
        #         5: 25166127,
        #         6: 25166133,
        #         7: 25166128,
        #         8: 25166129,
        #     },
        #     "ctrlRoadId": {
        #         1: 8388836,
        #         2: 8388789,
        #         3: 8388788,
        #         4: 8388839,
        #         5: 8388841,
        #         6: 8388758,
        #         7: 8388769,
        #         8: 8388767,
        #     },
        #     "nextRoad": {
        #         1: 8388752,
        #         2: 8388634,
        #         3: 8388753,
        #         4: 8388632,
        #         5: 8388757,
        #         6: 8388764,
        #         7: 8388628,
        #         8: 8388627,
        #     },
        # }
        # print("当前时间戳：", time.time())
        return func(*args, **kwargs)

    return wrapper


def broken_line_detec(x):
    if x['type'] == 2:
        return 0
    else:
        return 1


def left_line_detec_correct(x, simFrame):
    if (x['simFrame'] in simFrame) or x['id'] == 2:
        return 0
    else:
        return x['left_line_detec']


def right_line_detec_correct(x, simFrame):
    if (x['simFrame'] in simFrame) or x['id'] == 0:
        return 0
    else:
        return x['right_line_detec']


def flag_red_traffic_light(x, cycleTime, duration_start, duration_end):
    divisor = x['simTime'] / cycleTime
    decimal_part = divisor - int(divisor)
    # decimal_part = divisor % 1
    if duration_start <= decimal_part < duration_end:
        return 1
    else:
        return x["flag_red_traffic_light"]


def normalization_processing(x):
    difference = x["traffic_light_heading_difference"]
    while (difference >= 360):
        difference -= 360
    return difference


def press_lines_detection(roadMark_csv_data):
    warnings.filterwarnings("ignore")
    distance_press_lines = 1  # 规定的压线距离,lateralDist小于该值,认为是压线

    roadMark_csv_df = pd.DataFrame(roadMark_csv_data)
    # print(roadMark_csv_df.columns)
    logging.debug('\nroadMark_csv_df.columns{}'.format(roadMark_csv_df.columns))

    """筛选本车在最左侧车道,和在最右侧车道的数据"""
    roadMark_csv_df["right_line_detec"] = 1  # 新增列,全部置1
    roadMark_csv_df["left_line_detec"] = 1  # 新增列,全部置1
    # print(roadMark_csv_df)
    # logging.debug('{}'.format(roadMark_csv_df))

    """检测是否需要进行边线压线检测,不需要的置为0"""
    roadMark_csv_df['left_line_detec'] = roadMark_csv_df.apply(lambda x: broken_line_detec(x), axis=1)
    roadMark_csv_df['right_line_detec'] = roadMark_csv_df.apply(lambda x: broken_line_detec(x), axis=1)
    mask_lane_left = (roadMark_csv_df['id'] == 4)  # 左侧的左侧车道线
    simFrame = roadMark_csv_df.iloc[:, :][mask_lane_left]["simFrame"].tolist()
    roadMark_csv_df['left_line_detec'] = roadMark_csv_df.apply(lambda x: left_line_detec_correct(x, simFrame), axis=1)
    mask_lane_right = (roadMark_csv_df['id'] == 6)  # 右侧的右侧车道线
    simFrame = roadMark_csv_df.iloc[:, :][mask_lane_right]["simFrame"].tolist()
    roadMark_csv_df['right_line_detec'] = roadMark_csv_df.apply(lambda x: right_line_detec_correct(x, simFrame), axis=1)

    # print(roadMark_csv_df)
    # logging.debug('{}'.format(roadMark_csv_df))

    """左边线压线检测"""
    lateralDist = roadMark_csv_df.iloc[:, :][roadMark_csv_df.left_line_detec == 1][roadMark_csv_df.id == 0][
        ['simTime', 'lateralDist']]
    # print(lateralDist)

    detection_time = 0  # 压线检测开始时间
    num_press_lines = 0  # 压线次数为0
    time_press_lines_list = []
    """检测压线次数,间隔8s后算又一次压线"""
    while (not lateralDist.iloc[:, :][roadMark_csv_df.simTime >= detection_time][
        roadMark_csv_df.lateralDist < distance_press_lines].empty):
        num_press_lines += 1
        time_press_lines = lateralDist.iloc[:, :][roadMark_csv_df.simTime >= detection_time][
            roadMark_csv_df.lateralDist < distance_press_lines].simTime.tolist()[0]
        # print("time_press_lines: ",time_press_lines)
        logging.debug('time_press_lines: {}'.format(time_press_lines))
        lateralDist_value = \
            roadMark_csv_df[roadMark_csv_df.simTime == time_press_lines][roadMark_csv_df.id == 0].lateralDist.tolist()[
                0]
        # print("lateralDist: ",lateralDist_value)
        logging.debug('lateralDist_value: {}'.format(lateralDist_value))
        detection_time = time_press_lines + 8  # 间隔8s后再次进行检测
        time_press_lines_list.append(time_press_lines)
    left_num_press_lines = num_press_lines
    left_time_press_lines_list = time_press_lines_list
    # print("left_num_press_lines: ",left_num_press_lines)
    # print("left_time_press_lines_list: ", left_time_press_lines_list)
    logging.debug('left_num_press_lines: {}'.format(left_num_press_lines))
    logging.debug('left_time_press_lines_list: {}'.format(left_time_press_lines_list))
    logging.debug('\n左边线距离lateralDist: {}'.format(lateralDist))

    """右边线压线检测"""
    lateralDist = roadMark_csv_df.iloc[:, :][roadMark_csv_df.right_line_detec == 1][roadMark_csv_df.id == 2][
        ['simTime', 'lateralDist']]
    # print(lateralDist)

    detection_time = 0
    num_press_lines = 0
    time_press_lines_list = []
    """检测压线次数,间隔8s后算又一次压线"""
    while (not lateralDist.iloc[:, :][roadMark_csv_df.simTime >= detection_time][
        abs(roadMark_csv_df.lateralDist) < distance_press_lines].empty):
        num_press_lines += 1
        time_press_lines = lateralDist.iloc[:, :][roadMark_csv_df.simTime >= detection_time][
            abs(roadMark_csv_df.lateralDist) < distance_press_lines].simTime.tolist()[0]
        # print("time_press_lines: ",time_press_lines)
        logging.debug('time_press_lines: {}'.format(time_press_lines))
        lateralDist_value = \
            roadMark_csv_df[roadMark_csv_df.simTime == time_press_lines][roadMark_csv_df.id == 2].lateralDist.tolist()[
                0]
        # print("lateralDist: ", lateralDist_value)
        logging.debug('lateralDist_value: {}'.format(lateralDist_value))
        detection_time = time_press_lines + 8
        time_press_lines_list.append(time_press_lines)
    right_num_press_lines = num_press_lines
    right_time_press_lines_list = time_press_lines_list
    # print("right_num_press_lines: ",right_num_press_lines)
    # print("right_time_press_lines_list: ", right_time_press_lines_list)
    logging.debug('right_num_press_lines: {}'.format(right_num_press_lines))
    logging.debug('right_time_press_lines_list: {}'.format(right_time_press_lines_list))
    logging.debug('\n右边线距离lateralDist: {}'.format(lateralDist))

    """求压线次数之和,左侧+右侧"""
    num_press_lines = right_num_press_lines + left_num_press_lines
    time_press_lines_list = left_time_press_lines_list + right_time_press_lines_list
    # print("num_press_lines: ",num_press_lines)
    # print("time_press_lines_list: ", time_press_lines_list)
    logging.debug('num_press_lines: {}'.format(num_press_lines))
    logging.debug('time_press_lines_list: {}'.format(time_press_lines_list))
    return num_press_lines, time_press_lines_list


def stop_give_way_detection(signboard_df, objState_csv_df, objState_sensor_csv_df, roadPos_csv_df):
    l_stipulate = 30  # 与停车让行牌相距的距离
    signalIdList = signboard_df["signalId"].tolist()
    score_list = []  # debug
    time_penalty_list = [0]  # 停车让行的罚时
    comment = ""  # 评语/注释
    flag_passing_stop_giveway = False
    flag_ego_stop = False
    flag_stop_time_rational = False
    for signalId in signalIdList:
        # print("signalId: ",signalId)
        logging.debug('signalId: {}'.format(signalId))
        signboardId = signalId
        signboardLinkRoadId = signboard_df.iloc[:, :][signboard_df.signalId == signalId]["roadId"].tolist()[0]
        signboardPosX = signboard_df.iloc[:, :][signboard_df.signalId == signalId]["posX"].tolist()[0]
        signboardPosY = signboard_df.iloc[:, :][signboard_df.signalId == signalId]["posY"].tolist()[0]
        """
        ----------------------------------------------------
        # step1：是否进入停车让行标识牌所在道路
        ----------------------------------------------------
        """
        # isEnterRoad = False
        signboardLinkRoadId_uint16 = signboardLinkRoadId % 65536
        ego_roadPos_signboard = roadPos_csv_df.iloc[:, :][roadPos_csv_df.playerId == 1][
            roadPos_csv_df.roadId == signboardLinkRoadId_uint16]
        if ego_roadPos_signboard.empty:
            # print("1：没有进入停车让行标识牌所在道路")
            logging.debug("没有进入停车让行标识牌所在道路")
            score_list.append("1:没有进入停车让行标识牌所在道路")
            continue
        """
        ----------------------------------------------------
        # step2：与标识牌的距离是否小于规定距离
        ----------------------------------------------------
        """
        df_ego = objState_csv_df.iloc[:, :][objState_csv_df.id == 1][objState_csv_df.type == 1]
        df_ego["signboard_distance_absolute"] = df_ego[['posX', 'posY']].apply(
            lambda x: euclidean((signboardPosX, signboardPosY), (x['posX'], x['posY'])), axis=1)
        df_ego["velocity_resultant"] = df_ego[['speedX', 'speedY']].apply(
            lambda x: math.sqrt(x['speedX'] ** 2 + x['speedY'] ** 2) * 3.6, axis=1)
        time_list = df_ego.iloc[:, :][df_ego.signboard_distance_absolute < l_stipulate]["simTime"].tolist()
        # print("time_list: ", time_list)
        logging.debug("\n进入停车让行附近的时间列表time_list: \n{}".format(time_list))
        if time_list == []:
            score_list.append("2:没有出现在停车让行标识牌附近")
            # print("1:没有跟车场景[12]，算法测试失败")
            continue
        else:
            time_start = time_list[0]
            # time_end = time_list[-1]
        """
        ----------------------------------------------------
        # step3：检测停车让行标识牌不在ego车的后方
        ----------------------------------------------------
        """
        Behind_ego_car = objState_sensor_csv_df.iloc[:, :][objState_sensor_csv_df.id == signboardId] \
            [objState_sensor_csv_df.FLU_posY < 0][objState_sensor_csv_df.FLU_posY > -50] \
            [objState_sensor_csv_df.FLU_posX > 0][objState_sensor_csv_df.FLU_posX < 200]
        if Behind_ego_car.empty:
            score_list.append("3:自车不在标识牌后方，识别不到标识牌")
            continue
        """
        ----------------------------------------------------
        # step4：进入停车让行之前最大速度要不为0
        ----------------------------------------------------
        """
        # 防止开始的时候就在附近
        if time_start == 0:
            time_start = 3
        df_ego_speed_before = df_ego.iloc[:, :][df_ego.simTime <= time_start]["velocity_resultant"].tolist()
        if sum(df_ego_speed_before) / len(df_ego_speed_before) == 0:
            score_list.append("4:进入停车让行牌道路之前速度为0")
            continue
        flag_passing_stop_giveway = True

        """
        ----------------------------------------------------
        # step5：检测有没有在停车让行牌前停下
        ----------------------------------------------------
        """
        # 防止开始的时候就在附近
        time_start = time_list[0]
        if time_start == 0:
            time_start = 3
        time_end = time_list[-1]
        df_ego_speed_near_signage = df_ego.iloc[:, :][df_ego.simTime >= time_start][df_ego.simTime <= time_end][
            "velocity_resultant"]
        if df_ego_speed_near_signage.empty:
            logging.debug('没有靠近停车让行标识牌')
            continue
        """ 判断n秒内是否启动 """
        required_startup_time = 3.2  # 要求启动时间,大于该值要被罚时
        ego_velocity_near_signage_min = min(df_ego_speed_near_signage.tolist())
        logging.debug('ego_velocity_near_signage_min: {}'.format(ego_velocity_near_signage_min))
        """ 筛选合速度为0的时刻 """
        ego_detection_velocity_0 = \
            df_ego.iloc[:, :][df_ego.simTime >= time_start][df_ego.simTime <= time_end][df_ego.velocity_resultant == 0][
                "simTime"].tolist()
        if ego_detection_velocity_0 == []:
            logging.debug('在停车让行场景下没有停车')
            time_penalty_no_stop_in_stop_giveway = 20
            time_penalty_list.append(time_penalty_no_stop_in_stop_giveway)
            comment += "{}s~{}s内，经过停车让行牌{}，没有停下,罚时{}s;".format(time_start, time_end, signboardId,
                                                               time_penalty_no_stop_in_stop_giveway)
            continue
        flag_ego_stop = True

        """
        ----------------------------------------------------
        # step6：检测ego车是否继续行驶
        ----------------------------------------------------
        """
        logging.debug("\n速度为0的时间列表: \n{}".format(ego_detection_velocity_0))
        ego_detection_velocity_0_start = ego_detection_velocity_0[0]
        ego_detection_velocity_not_0 = \
            df_ego.iloc[:, :][df_ego.simTime >= ego_detection_velocity_0_start][df_ego.simTime <= time_end][
                df_ego.velocity_resultant != 0][
                "simTime"].tolist()
        if ego_detection_velocity_not_0 != []:
            ego_detection_velocity_0_end = ego_detection_velocity_not_0[0]
        else:
            ego_detection_velocity_0_end = ego_detection_velocity_0[-1]
        if ego_detection_velocity_0_start + required_startup_time + 0.1 < time_end:  # +0.1的目的:防止正好是required_startup_time时间启动
            detection_time_1 = ego_detection_velocity_0_start + required_startup_time + 0.1
        else:
            detection_time_1 = time_end
        detection_time_velocity = df_ego.iloc[:, :][df_ego.simTime >= ego_detection_velocity_0_start] \
            [df_ego.simTime <= detection_time_1]["velocity_resultant"].tolist()
        # print(detection_time_velocity)
        logging.debug("\nDetection_time_velocity: \n{}".format(detection_time_velocity))
        # 看到行人车辆减速到速度值最小值,定义该时刻为t,在[t,t + required_startup_time]内平均速度不为0
        startup_time = round(ego_detection_velocity_0_end - ego_detection_velocity_0_start, 3)
        if (detection_time_velocity != []) and (sum(detection_time_velocity) / len(detection_time_velocity) != 0):
            flag_stop_time_rational = True
            logging.debug("自车启动时间为{}s".format(startup_time))
        else:
            logging.debug("自车停车后 {}s 内没有启动,自车启动时间为{}s".format(required_startup_time, startup_time))
            score_list.append("5:ego车没有快速启动")
            time_penalty_no_stop_giveway = 5
            time_penalty_list.append(time_penalty_no_stop_giveway)
            comment += "自车停车后{}s内没有自启动,自车启动时间为{}s,罚时{}s;".format(required_startup_time,
                                                                 startup_time,
                                                                 time_penalty_no_stop_giveway)
            # print(score_list)
            # continue
    # if flag_passing_stop_giveway == False:  # 没有经过停车让行牌所在道路
    #     time_penalty_no_passing_stop_giveway = 40
    #     time_penalty_list.append(time_penalty_no_passing_stop_giveway)
    #     comment += "没有经过停车让行牌所在道路,罚时{}s;".format(time_penalty_no_passing_stop_giveway)
    #     return time_penalty_list, comment
    # if flag_ego_stop == False:  # 没有在停车让行牌前停下来
    #     time_penalty_no_passing_stop_giveway = 30
    #     time_penalty_list.append(time_penalty_no_passing_stop_giveway)
    #     comment += "没有在停车让行牌前停下,罚时{}s;".format(time_penalty_no_passing_stop_giveway)

    return time_penalty_list, comment


def traffic_light_detection(objState_csv_df,
                            objState_sensor_csv_df, roadPos_csv_df,
                            trafficLight_csv_df, trafficSign_csv_df):
    signboard_df = pd.read_json(json.dumps(traffic_light_information))

    l_stipulate = 40
    ego_df = objState_csv_df.iloc[:, :][objState_csv_df.id == 1][objState_csv_df.type == 1]
    ego_roadPos = roadPos_csv_df.iloc[:, :][roadPos_csv_df.playerId == 1]
    ego_df = ego_df.reset_index(drop=True)
    ego_roadPos = ego_roadPos.reset_index(drop=True)
    ego_df['roadId'] = ego_roadPos['roadId']
    logging.debug("\nego_df: {}".format(ego_df.shape))
    logging.debug("\nego_roadPos: {}".format(ego_roadPos.shape))
    time_penalty_list = [0]
    comment = ""
    description_list = []
    ego_df["velocity_resultant"] = ego_df[['speedX', 'speedY']].apply(
        lambda x: math.sqrt(x['speedX'] ** 2 + x['speedY'] ** 2) * 3.6, axis=1)
    trafficLight_id_list = set(trafficLight_csv_df['id'].tolist())
    is_when_red_on_road = False  # 红灯时没有进入道路
    if trafficLight_id_list == []:  # 没有交通信号灯数据
        # time_penalty_no_data = 100
        # time_penalty_list.append(time_penalty_no_data)
        # comment += "没有交通信号灯数据,罚时{}s".format(time_penalty_no_data)
        return time_penalty_list, comment
    for trafficLight_id in trafficLight_id_list:
        trafficLight_id_uint16 = trafficLight_id % 65536
        trafficLight_position = trafficSign_csv_df.iloc[:, :][trafficSign_csv_df.id == trafficLight_id]
        trafficLight_character = trafficLight_csv_df.iloc[:, :][trafficLight_csv_df.id == trafficLight_id]
        if trafficLight_position.empty:  # trafficSign中没有记录
            continue
        trafficLight_position = trafficLight_position.iloc[:1, :]
        trafficLight_position_x = trafficLight_position['posX'].tolist()[0]
        trafficLight_position_y = trafficLight_position['posY'].tolist()[0]
        trafficLight_position_z = trafficLight_position['posZ'].tolist()[0]
        trafficLight_position_heading = trafficLight_position['posH'].tolist()[0]
        cycleTime = trafficLight_character['cycleTime'].tolist()[0]
        noPhases = trafficLight_character['noPhases'].tolist()[0]
        signboard_setup = signboard_df[signboard_df.signalId == trafficLight_id]
        if signboard_setup.empty:
            continue
        ctrlRoadId = signboard_df[signboard_df.signalId == trafficLight_id]['ctrlRoadId'].tolist()[0]
        nextRoad = signboard_df[signboard_df.signalId == trafficLight_id]['nextRoad'].tolist()[0]

        """ 是否在红绿灯附近,且与红绿灯对向 """
        ego_df["traffic_light_distance_absolute"] = ego_df[['posX', 'posY']].apply( \
            lambda x: euclidean((trafficLight_position_x, trafficLight_position_y), (x['posX'], x['posY'])), axis=1)
        ego_df["traffic_light_heading_difference"] = ego_df.apply(
            lambda x: abs(x['posH'] - trafficLight_position_heading) * 57.3, axis=1)
        ego_df["traffic_light_heading_difference"] = ego_df.apply(
            lambda x: normalization_processing(x), axis=1)  # 归一化到[0,360)之间
        mask_trafftic_light = ((ego_df['traffic_light_heading_difference'] <= 210) & (ego_df[
                                                                                          'traffic_light_heading_difference'] >= 150)) | (
                                      ego_df['traffic_light_heading_difference'] <= 30) | (ego_df[
                                                                                               'traffic_light_heading_difference'] >= 330)
        ego_near_light = ego_df.iloc[:, :][ego_df.traffic_light_distance_absolute <= l_stipulate][mask_trafftic_light]
        if ego_near_light.empty:
            logging.debug("没有到红绿灯附近,或没有与红绿灯正对")
            continue

        """ 当前是否为红灯 """
        ego_near_light["flag_red_traffic_light"] = 0  # 不是红灯
        type_list = trafficLight_character['type'].tolist()[:noPhases]
        duration = trafficLight_character['duration'].tolist()[:noPhases]
        duration_correct = [0] * noPhases
        for number in range(noPhases):
            duration_correct[number] = sum(duration[:number + 1])
            type_current = type_list[number]
            if type_current == 1:  # 当前duration是红灯
                if number == 0:
                    duration_start = 0
                else:
                    duration_start = duration_correct[number - 1]
                duration_end = duration_correct[number]
                ego_near_light["flag_red_traffic_light"] = ego_near_light[['simTime', 'flag_red_traffic_light']].apply(
                    lambda x: flag_red_traffic_light(x, cycleTime, duration_start, duration_end), axis=1)
                # roadMark_csv_df.apply(lambda x: left_line_detec_correct(x, simFrame), axis=1)
        logging.debug("type: {}".format(type_list))
        logging.debug("duration: {}".format(duration_correct))

        ego_redGreen_Light = ego_near_light[ego_near_light.flag_red_traffic_light == 1]
        if ego_redGreen_Light.empty:
            logging.debug("没有遇到红灯")
            continue

        """ 是否在红灯控制车道 """
        ctrlRoadId_uint16 = ctrlRoadId % 65536
        ego_red_light_ctrl_road = ego_redGreen_Light[ego_redGreen_Light.roadId == ctrlRoadId_uint16]
        if ego_red_light_ctrl_road.empty:
            logging.debug("不在红灯控制车道")
            continue

        """ 判断当前道路是否停下 """
        # ego_red_light_ctrl_road["velocity_resultant"] = ego_red_light_ctrl_road[['speedX', 'speedY']].apply(
        #     lambda x: math.sqrt(x['speedX'] ** 2 + x['speedY'] ** 2) * 3.6, axis=1)
        is_when_red_on_road = True  # 红灯时进入道路
        ego_red_light_ctrl_road_speed = ego_red_light_ctrl_road[ego_red_light_ctrl_road.velocity_resultant == 0]
        if not ego_red_light_ctrl_road_speed.empty:
            is_when_red_on_road = True
            logging.debug("未闯道路编号为{}的红灯".format(ctrlRoadId))
            description_list.append("未闯道路编号为{}的红灯;".format(ctrlRoadId))
        else:
            ego_red_light_ctrl_next_road = ego_redGreen_Light[ego_redGreen_Light.roadId == nextRoad]  # 是否进入交叉口
            if ego_red_light_ctrl_next_road.empty:
                logging.debug("未进入交叉口")
                continue
            ego_red_light_ctrl_next_road_startTime = ego_red_light_ctrl_next_road['simTime'].tolist()[0]
            ego_red_light_ctrl_next_road_endTime = ego_red_light_ctrl_next_road_startTime + 1
            ego_intersection_speed = \
                ego_redGreen_Light[ego_redGreen_Light.simTime > ego_red_light_ctrl_next_road_startTime][
                    ego_redGreen_Light.simTime < ego_red_light_ctrl_next_road_endTime][
                    ego_redGreen_Light.velocity_resultant == 0]
            if ego_intersection_speed.empty:
                logging.debug("闯红灯")
                time_penalty_rush_redLight = 80
                time_penalty_list.append(time_penalty_rush_redLight)
                comment += "在道路id={}处闯红灯,罚时{}s;".format(ctrlRoadId, time_penalty_rush_redLight)
                # return time_penalty_list, comment
                continue
            else:
                is_when_red_on_road = True
                logging.debug("未闯道路编号为{}的红灯;".format(ctrlRoadId))
                description_list.append("未闯道路编号为{}的红灯;".format(ctrlRoadId))
    # """ 检测是否有(信号灯是红灯,而且本车进入道路)的情况 """
    # if is_when_red_on_road == False:
    #     time_penalty_no_rational = 80
    #     time_penalty_list.append(time_penalty_no_rational)
    #     logging.debug("没有出现(信号灯是红灯,而且本车进入道路)的情况;")
    #     comment += "没有出现(信号灯是红灯,而且本车进入道路)的情况,不符合测试要求,罚时{}s;".format(
    #         time_penalty_no_rational)
    #     return time_penalty_list, comment
    description_str = ""
    for list_string in description_list:
        description_str += list_string
    comment += description_str
    return time_penalty_list, comment


# @timestamp
def get_report(scenario, script_id):
    try:
        logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')
        # logging.disable(logging.CRITICAL)  # 取消屏幕输出
        warnings.filterwarnings("ignore")
        # 原始数据
        scenario_ego = scenario.scenario_data
        scenario_target = scenario.obj_scenario_data
        # 0609新增数据
        roadMark_csv_data = scenario.other_scenarios_data["road_mark"]
        objState_csv_df = scenario.other_scenarios_data['object_state']
        objState_sensor_csv_df = scenario.other_scenarios_data['object_state_sensor']
        roadPos_csv_df = scenario.other_scenarios_data['road_pos']
        trafficSign_csv_df = scenario.other_scenarios_data['traffic_signal']
        trafficLight_csv_df = scenario.other_scenarios_data['traffic_light']
        score = -1
        evaluate_item = ""
        time_penalty_list = [0]

        # objState_sensor_df = scenario.scenario_data
        """
        step:数据预处理
        """
        time_upper_bound = 900
        time_actual = time_upper_bound
        time_correction = time_upper_bound
        scenario_ego_index = scenario_ego.index
        scenario_ego['time'] = scenario_ego_index

        """
        step:判断是否发生碰撞
        """
        df_ego = objState_csv_df.iloc[:, :][objState_csv_df.id == 1][objState_csv_df.type == 1]
        mask = (objState_csv_df['type'] == RDB_OBJECT_TYPE_PLAYER_CAR) | (
                objState_csv_df['type'] == RDB_OBJECT_TYPE_PLAYER_PEDESTRIAN) | (
                       objState_csv_df['type'] == RDB_OBJECT_TYPE_BARRIER) | (
                       objState_csv_df['type'] == RDB_OBJECT_TYPE_PLAYER_MOTORBIKE) | (
                       objState_csv_df['type'] == RDB_OBJECT_TYPE_OTHER)
        df_target = objState_csv_df.loc[mask]
        df_target_id = set(df_target.iloc[:, :][df_target.id != 1].id.tolist())
        df_target_name = set(df_target.iloc[:, :][df_target.id != 1].name.tolist())
        logging.debug("\ndf_target_id: \n{}".format(df_target_id))
        logging.debug("\ndf_target_name: \n{}".format(df_target_name))
        # print("df_target_id: ", df_target_id)
        for id in df_target_id:
            target_id = objState_csv_df.iloc[:, :][objState_csv_df.id == id].reset_index(drop=True)
            # 修改新列的列名posX改为'ego_posX'
            # df_ego.rename(columns={"posX": 'ego_posX', "posY": 'ego_posY', "posH": 'ego_posH'}, inplace=True)
            ego_posX = df_ego[["posX", "posY", "posH"]].reset_index(drop=True)
            ego_posX.rename(columns={"posX": 'ego_posX', "posY": 'ego_posY', "posH": 'ego_posH'}, inplace=True)
            if target_id.shape[0] + 1 == ego_posX.shape[0]:
                ego_posX = ego_posX.iloc[:-1, :]

            target_id = pd.concat([target_id, ego_posX], axis=1)
            target_id["distance_absolute"] = target_id[['posX', 'posY', 'ego_posX', 'ego_posY']].apply( \
                lambda x: euclidean((x['ego_posX'], x['ego_posY']), (x['posX'], x['posY'])), axis=1)
            # print("target_id.distance_absolute: ",target_id.distance_absolute.tolist())
            # print(min(target_id.distance_absolute.tolist()))
            time_list = target_id.iloc[:, :][target_id.distance_absolute < 0.5][
                "simTime"].tolist()  # 与后轴中心的欧氏距离小于0.5,认为发生碰撞
            # print("time_list: ", time_list)
            if time_list == []:
                pass
            else:
                logging.debug("\ncollision_id: \n{}".format(id))
                logging.debug("\ncollision_time: \n{}".format(time_list))
                score = 0
                evaluate_item = '未正常完成算法测试:在time={}s时发生碰撞,得0分;'.format(time_list)
                return

        """
        step:检测是否冲出车道
        """
        ego_roadPos = roadPos_csv_df.iloc[:, :][roadPos_csv_df.playerId == 1].reset_index(drop=True)
        ego_roadPos_S = ego_roadPos[["roadS", "roadT"]].iloc[:-1, :].reset_index(drop=True)
        ego_roadPos_S.rename(columns={"roadS": 'last_roadS', "roadT": 'last_roadT'}, inplace=True)
        new_row = {'last_roadS': 0, 'last_roadT': 0}
        new_row = pd.DataFrame(new_row, index=[0])
        # ego_roadPos_S = ego_roadPos_S.append(new_row, ignore_index=True)
        ego_roadPos_S = pd.concat([new_row, ego_roadPos_S], axis=0).reset_index(drop=True)
        ego = objState_csv_df.iloc[:, :][objState_csv_df.id == 1].reset_index(drop=True)
        ego_speedX = ego[["speedX", "speedY"]].reset_index(drop=True)
        if ego_speedX.shape[0] == ego_roadPos.shape[0] + 1:
            ego_speedX = ego_speedX.iloc[1:, :].reset_index(drop=True)
        ego_motion = pd.concat([ego_roadPos, ego_roadPos_S, ego_speedX], axis=1)
        ego_motion["delta_roadS"] = ego_motion[['roadS', 'last_roadS']].apply( \
            lambda x: (x['roadS'] - x['last_roadS']), axis=1)
        ego_motion["delta_roadT"] = ego_motion[['roadT', 'last_roadT']].apply( \
            lambda x: (x['roadT'] - x['last_roadT']), axis=1)
        mask_laneOffset = (ego_motion['laneOffset'] >= 1) | (ego_motion['laneOffset'] <= -1)
        mask_ego_speed = (abs(ego_motion['speedX']) >= 0.01) | (abs(ego_motion['speedY']) >= 0.01)
        ego_motion_outLane = ego_motion.iloc[:, :][ego_motion.delta_roadS == 0][ego_motion.delta_roadT == 0] \
            [mask_ego_speed][mask_laneOffset].simTime.tolist()
        if ego_motion_outLane == []:
            pass
        else:
            # print("ego_motion_outLane: ", ego_motion_outLane)
            logging.debug('ego_motion_outLane: {}'.format(ego_motion_outLane))
            outRoad_time = ego_motion_outLane[0]
            score = 0
            evaluate_item = '未正常完成算法测试:在time={}s时冲出车道,得0分;'.format(outRoad_time)
            return

        """
        step:检测运行时间是否超时
        """
        time_run = scenario_ego['time'].tolist()
        if time_run == []:
            score = 0
            evaluate_item = '未正常完成算法测试:没有记录的仿真时间,得0分;'
            return
        else:
            time_run_end = time_run[-1]
            if time_run_end >= time_upper_bound:
                score = 0
                evaluate_item = '未正常完成算法测试:测试总用时超过规定时间15min,得0分;'
                return
            else:
                pass

        """
        step:检测是否压线
        """
        num_press_lines, time_press_lines_list = press_lines_detection(roadMark_csv_data)
        if num_press_lines > 0:
            time_penalty_press_lines = 5  # 压一次线的罚时
            time_penalty_press_lines_total = num_press_lines * time_penalty_press_lines  # 压线总罚时
            time_penalty_list.append(time_penalty_press_lines_total)
            evaluate_item += '压线{}次,压线时间为:{},罚时{}s;'.format(num_press_lines, time_press_lines_list,
                                                            time_penalty_press_lines_total)

        """
        step:检测是否在限速牌相关道路限速通过
        """
        l_stipulate = 50  # 限速牌检测距离
        information = json.dumps(speed_limit_information)
        signboard_df = pd.read_json(information)
        # print(signboard_df)
        logging.debug('\nsignboard_df: {}'.format(signboard_df))

        # ego_df = scenario.scenario_data
        # target_df = scenario.obj_scenario_data
        Passing_speedlimit_sign = 0
        ego_df = objState_csv_df.iloc[:, :][objState_csv_df.id == 1][objState_csv_df.type == 1]
        ego_df["velocity_resultant"] = ego_df[['speedX', 'speedY']].apply(
            lambda x: math.sqrt(x['speedX'] ** 2 + x['speedY'] ** 2) * 3.6, axis=1)
        signalIdList = signboard_df["signalId"].tolist()
        for signalId in signalIdList:
            signboard_Id = signalId
            signboard_LinkRoadId = signboard_df.iloc[:, :][signboard_df.signalId == signalId]["roadId"].tolist()[0]
            signboard_PosX = signboard_df.iloc[:, :][signboard_df.signalId == signalId]["posX"].tolist()[0]
            signboard_PosY = signboard_df.iloc[:, :][signboard_df.signalId == signalId]["posY"].tolist()[0]
            speedLimit = signboard_df.iloc[:, :][signboard_df.signalId == signalId]["speedLimit"].tolist()[0]

            signboardLinkRoadId_uint16 = signboard_LinkRoadId % 65536
            """1)检测是否进入限速标识牌链接道路"""
            # ego_df_reindex = ego_df.reset_index(drop=True)
            if scenario_ego.iloc[:, :][scenario_ego.road_id == signboardLinkRoadId_uint16].empty:
                # print("1:没有进入限速标识牌所在道路:{}".format(signboardLinkRoadId_uint16))
                logging.debug('1:没有进入限速标识牌所在道路: {}'.format(signboardLinkRoadId_uint16))
                continue
            else:
                Passing_speedlimit_sign = 1

            """2)检测自车与标识牌的距离是否小于规定距离"""
            ego_df["signboard_distance_absolute"] = ego_df[['posX', 'posY']].apply( \
                lambda x: euclidean((signboard_PosX, signboard_PosY), (x['posX'], x['posY'])), axis=1)
            time_list = ego_df.iloc[:, :][ego_df.signboard_distance_absolute < l_stipulate]["simTime"].tolist()
            if time_list == []:
                # print("2:没有出现在限速标识牌附近")
                logging.debug('2:没有出现在限速标识牌附近')
                continue

            """3)要求限速标识牌不在ego车的后方(即,自车识别到了限速牌)"""
            Behind_ego_car = objState_sensor_csv_df.iloc[:, :][objState_sensor_csv_df.id == signboard_Id] \
                [objState_sensor_csv_df.FLU_posY < 0][objState_sensor_csv_df.FLU_posY > -50] \
                [objState_sensor_csv_df.FLU_posX > 0][objState_sensor_csv_df.FLU_posX < 200]
            if Behind_ego_car.empty:
                # print("3:不在限速牌的后面,没有识别到限速牌")
                logging.debug('3:不在限速牌的后面,没有识别到限速牌')
                continue

            """4)测试车速度是否符合限速要求，存在大于speedLimit * 0.6，小于speedLimit * 1.2时刻 """
            df_ego_speed = ego_df.iloc[:, :][ego_df.simTime >= time_list[0]][ego_df.simTime <= time_list[-1]] \
                [ego_df.signboard_distance_absolute < l_stipulate] \
                [ego_df.velocity_resultant > speedLimit * 0.6][
                ego_df.velocity_resultant < speedLimit * 1.2]  # 判断在标识牌附近，测试车速度是否符合限速要求
            if df_ego_speed.empty:
                # print("4:车速不符合限速要求")
                logging.debug('4:车速不符合限速要求')
                # 车速不符合限速要求,罚时20s
                time_penalty_no_speed_limit = 20
                time_penalty_list.append(time_penalty_no_speed_limit)
                evaluate_item += "没有在 id = {} 的路上限速通过,罚时{}s;".format(signboardLinkRoadId_uint16,
                                                                     time_penalty_no_speed_limit)
                continue
            else:
                # print("在 id = {} 的路上限速通过".format(signboardLinkRoadId_uint16))
                logging.debug('在 id = {} 的路上限速通过'.format(signboardLinkRoadId_uint16))

        # 如果没有进入限速道路,罚时30s
        # if Passing_speedlimit_sign == 0:
        #     time_penalty_no_passing_speedlimit_road = 30
        #     time_penalty_list.append(time_penalty_no_passing_speedlimit_road)
        #     evaluate_item += "自车没有经过限速道路,不符合要求,罚时{}s;".format(time_penalty_no_passing_speedlimit_road)

        """
        step:检测是否在停车让行牌处停车让行
        """
        stop_sign_information_json = json.dumps(stop_sign_information)
        signboard_stop_sign_df = pd.read_json(stop_sign_information_json)
        time_penalty_list_stop_giveway, comment = stop_give_way_detection(signboard_stop_sign_df, objState_csv_df,
                                                                          objState_sensor_csv_df, roadPos_csv_df)
        time_penalty_list += time_penalty_list_stop_giveway
        evaluate_item += comment

        """
        step:检测是否闯红灯
        """
        time_penalty_list_rush_red_light, comment = traffic_light_detection(objState_csv_df, objState_sensor_csv_df,
                                                                            roadPos_csv_df, trafficLight_csv_df,
                                                                            trafficSign_csv_df)
        time_penalty_list += time_penalty_list_rush_red_light
        evaluate_item += comment

        """
        step:检测有没有经过行驶路线标记点
        """
        l_destination_range = 5.25  # 终点圈定的范围,暂定为1.5倍的道路宽度
        ego_df["destination_distance_absolute"] = ego_df[['posX', 'posY']].apply( \
            lambda x: euclidean((destination_x, destination_y), (x['posX'], x['posY'])), axis=1)
        destination_df = ego_df.iloc[:, :][ego_df.destination_distance_absolute < l_destination_range]
        if destination_df.empty:
            logging.debug('2:没有到达终点')
            evaluate_item = "未正常完成算法测试:没有到达终点位置,得0分;"
            score = 0
            return

        l_path_point_range = 8  # 道路标记点圈定的范围
        ego_df["path_distance_absolute_point1"] = ego_df[['posX', 'posY']].apply( \
            lambda x: euclidean((path_point_x1, path_point_y1), (x['posX'], x['posY'])), axis=1)
        ego_df["path_distance_absolute_point2"] = ego_df[['posX', 'posY']].apply( \
            lambda x: euclidean((path_point_x2, path_point_y2), (x['posX'], x['posY'])), axis=1)
        ego_df["path_distance_absolute_point3"] = ego_df[['posX', 'posY']].apply( \
            lambda x: euclidean((path_point_x3, path_point_y3), (x['posX'], x['posY'])), axis=1)
        ego_df["path_distance_absolute_point4"] = ego_df[['posX', 'posY']].apply( \
            lambda x: euclidean((path_point_x4, path_point_y4), (x['posX'], x['posY'])), axis=1)
        df_path_point1 = ego_df.iloc[:, :][ego_df.path_distance_absolute_point1 < l_path_point_range]
        df_path_point2 = ego_df.iloc[:, :][ego_df.path_distance_absolute_point2 < l_path_point_range]
        df_path_point3 = ego_df.iloc[:, :][ego_df.path_distance_absolute_point3 < l_path_point_range]
        df_path_point4 = ego_df.iloc[:, :][ego_df.path_distance_absolute_point4 < l_path_point_range]
        if df_path_point1.empty:
            logging.debug('没有到达道路标记点1({},{})'.format(path_point_x1, path_point_y1))
            evaluate_item = "未正常完成算法测试:没有到达道路标记点1({},{})附近,得0分;".format(path_point_x1, path_point_y1)
            score = 0
            return
        elif df_path_point2.empty:
            logging.debug('没有到达道路标记点2({},{})'.format(path_point_x2, path_point_y2))
            evaluate_item = "未正常完成算法测试:没有到达道路标记点2({},{})附近,得0分;".format(path_point_x2, path_point_y2)
            score = 0
            return
        elif df_path_point3.empty:
            logging.debug('没有到达道路标记点3({},{})'.format(path_point_x3, path_point_y3))
            evaluate_item = "未正常完成算法测试:没有到达道路标记点3({},{})附近,得0分;".format(path_point_x3, path_point_y3)
            score = 0
            return
        elif df_path_point4.empty:
            logging.debug('没有到达道路标记点4({},{})'.format(path_point_x4, path_point_y4))
            evaluate_item = "未正常完成算法测试:没有到达道路标记点4({},{})附近,得0分;".format(path_point_x4, path_point_y4)
            score = 0
            return
        destination_time_list = destination_df.iloc[:, :][destination_df.velocity_resultant == 0].simTime.tolist()
        # 到达终点位置,没有在规定区域停下来
        if destination_time_list == []:
            time_actual = destination_df["simTime"].tolist()[-1]
            time_penalty_no_park = 10  # 没有在规定区域停下来的惩罚时间
            time_penalty_list.append(time_penalty_no_park)
            evaluate_item += "到达终点位置,但没有在规定区域内速度减为0,罚时{}s;".format(
                time_penalty_no_park)
        else:
            time_actual = destination_time_list[0]
        """
        step:计算总用时
        """
        time_correction = time_actual + sum(time_penalty_list)
        if sum(time_penalty_list) == 0:
            evaluate_item = "到达终点位置,且测试过程无违规，因此无罚时;"
        evaluate_item = "正常完成算法测试!实际用时:{}s,修正后用时:{}s;罚时情况说明:".format(time_actual, time_correction) + evaluate_item
        if score != 0:
            t_team = time_correction

            if t_team > t_max:
                score = 50
            else:
                score = 50 * (t_max / t_team - 1) / (t_max / t_min - 1) + 50
                score = round(score, 2)

    except:
        # print("--------------------")
        traceback.print_exc()
        # print("--------------------")
        time_actual = -1
        time_correction = -1
        score = -1
        evaluate_item = '评分功能发生错误,选择的评分脚本无法对此场景进行评价;'
    finally:
        score_description = "1) 比赛成绩以选手的比赛成绩为准，分数越高排名越高；" \
                            "2) 车辆没有到达终点，此次测试无成绩;  " \
                            "3) 车辆没有按照指定路线行驶，此次测试无成绩;  " \
                            "4) 本车与其他车辆、行人、锥桶等障碍物发生碰撞时，比赛终止，此次测试无成绩; " \
                            "5) 车辆整体驶出道路时，比赛终止，此次测试无成绩； " \
                            "6) 测试总用时超过15min，终止比赛，此次测试无成绩;" \
                            "7) 车辆出现闯红灯行为，罚时80s;" \
                            "8) 在限速道路上没有按照限速牌要求通过,罚时20s; " \
                            "9) 车辆在停车让行牌前未停下，罚时20s;" \
                            "10) 车辆到达终点，但没有在指定区域内完全停车，罚时10s; " \
                            "11) 车辆停车时间过长，包括信号灯红灯变绿后3s内未启动，停车让行停车后3s内未启动，避让障碍物异常停车3s内未启动，罚时5s;" \
                            "12) 车轮压车道实线一次,罚时5s; "
        return {
            'unit_scene_ID': script_id,
            'time_actual': time_actual,
            'time_correction': time_correction,
            'unit_scene_score': score,
            'evaluate_item': evaluate_item,
            'score_description': score_description
        }
