import math
import operator
import copy
import pandas as pd
from functools import reduce
from enumerations import SpeedType, TrailMotionType
from utils import spin_trans_form, Point, resample_by_time, get_adjust_trails, get_lane_distance, get_finale_trail, \
    multiple_trail, rotate_trail, concatTrails, corTransform_init, resample_by_time


def get_uniform_speed_trail(car_trails, trails_json_dict, start_speed, period, turning_angle, trail_section,
                            heading_angle, scenario):
    """
    return:直线轨迹
    从匀速的轨迹库中 分类别取出轨迹
    """

    # 从轨迹库中分离出匀速的轨迹
    uniform_json_dict = dict()
    trails = copy.deepcopy(car_trails)
    for motion in trails_json_dict.keys():
        for trail_speed, trail_value in trails_json_dict[motion].items():
            if trail_value and trail_speed in 'Uniform speed':
                selected_trail_list = []
                for single_trail in trail_value:
                    # 排除数据中初始速度和结束速度小于0的和结束heading angle减去开始heading angle大于0.5度的轨迹
                    if single_trail['startSpeed'] > 0 and single_trail['stopSpeed'] > 0 \
                            and math.fabs(single_trail['stopHeadinga'] - single_trail['startHeadinga'] < 0.5):
                        selected_trail_list.append(single_trail)
                uniform_json_dict[motion] = selected_trail_list

    previous_speed_difference = 100
    # 从挑选的轨迹中找到速度差异最小的轨迹
    for trail_motion in uniform_json_dict:
        uniform_json_dict[trail_motion] = sorted(uniform_json_dict[trail_motion],
                                                 key=operator.itemgetter('startSpeed'), reverse=True)

        for single_json in uniform_json_dict[trail_motion]:
            speed_difference = abs(single_json['startSpeed'] - start_speed)
            if speed_difference < previous_speed_difference:
                final_trail = single_json
                previous_speed_difference = speed_difference

    # 从轨迹数据中获得此轨迹并将其转换为符合场景要求的轨迹
    start_time = final_trail['start']
    end_time = final_trail['stop']
    single_trail = (trails[(trails['Time'].values <= end_time)
                           & (trails['Time'].values >= start_time)]).reset_index(drop=True)
    if len(single_trail) > 10:

        for _ in range(5):
            temp_trail = get_adjust_trails(trails_count=1, trail=single_trail)[1:]
            single_trail = pd.concat([single_trail, temp_trail], axis=0).reset_index(drop=True)
        trail_res = single_trail[:period * 10 + 1]
        start_point = Point(trail_res.at[0, 'ego_e'], trail_res.at[0, 'ego_n'])
        trail_res.loc[::, 'ego_e'] -= start_point.x
        trail_res.loc[::, 'ego_n'] -= start_point.y
        trail_res = trail_res.reset_index(drop=True)
        # 在轨迹拼接后统一处理
        # time_min = trail_res.Time.values.min()
        # for i in range(len(trail_res)):
        #     trail_res.loc[i, 'Time'] = time_min + 100 * i
    multiple = start_speed / trail_res.loc[0, 'vel_filtered']
    coord_heading_angle = trail_res.loc[0, 'headinga'] - heading_angle
    rotate_tuple = ('ego_e', 'ego_n'), ('left_e', 'left_n'), ('right_e', 'right_n')
    trail_res = rotate_trail(trail_res, coord_heading_angle, rotate_tuple)
    trail_res = multiple_trail(trail_res, multiple, rotate_tuple)
    return trail_res, turning_angle


def get_variable_speed_trail(car_trails, trails_json_dict, start_speed, period, speed_status_num, turning_angle,
                             heading_angle, scenario):
    """
    Parameters
    ----------
    car_trails: 原始的轨迹数据
    trails_json_dict:标记所有轨迹类型的json数据
    period: 持续时间
    speed_status_num: 当前需要处理的轨迹属于哪种加速状态
    turning_angle: 跟在有转向的运动后需要转向的角度
    heading_angle: 此轨迹的朝向角，取值范围[0,360]，以真北为基准，顺时针递减
    scenario: 场景参数
    Return 返回多条变速轨迹，如果所能生成的轨迹数量大于max_trails，返回轨迹条数是max_trails
    -------
    """
    if speed_status_num == str(SpeedType.Accelerate.value):
        speed_status = 'Accelerate'
    else:
        speed_status = 'Decelerate'
    variable_json_dict = dict()
    trails = copy.deepcopy(car_trails)
    previous_speed_difference = 100

    # 找到所有比较直的轨迹
    for trail_motion in trails_json_dict.keys():
        if trail_motion == 'No change lane':
            for trail_speed, trail_value in trails_json_dict[trail_motion].items():
                if trail_speed in speed_status:
                    selected_trail_list = []
                    for single_trail in trail_value:
                        if math.fabs(single_trail['stopHeadinga'] - single_trail['startHeadinga']) < 0.5:
                            selected_trail_list.append(single_trail)
                        variable_json_dict = {trail_motion: {trail_speed: selected_trail_list}}

    # 拼接加减速轨迹生成合适的变速轨迹
    for trail_motion in variable_json_dict:
        for trail_value in variable_json_dict[trail_motion].values():
            reverse_flag = ('startSpeed', False) if speed_status == str(SpeedType.Decelerate.value) else (
                'stopSpeed', True)
            temp_list = sorted(trail_value, key=operator.itemgetter(reverse_flag[0]), reverse=reverse_flag[1])

            # 找到所有可以完全拼成一条长轨迹的可能结果,轨迹片段变速间隔小于1
            for index in range(len(temp_list)):
                json_index_list_temp = [index]
                last_index = len(json_index_list_temp) - 1
                for index_temp in range(index + 1, len(trail_value)):
                    if (speed_status_num == str(SpeedType.Accelerate.value) and temp_list[last_index]['stopSpeed'] <=
                        temp_list[index_temp]['startSpeed'] <= temp_list[last_index]['stopSpeed'] + 1) or (
                            speed_status_num == str(SpeedType.Decelerate.value) and temp_list[last_index][
                        'stopSpeed'] >= temp_list[index_temp]['startSpeed'] >= temp_list[last_index][
                                'stopSpeed'] - 1):
                        json_index_list_temp.append(index_temp)

                # 提取轨迹数据
                trails_list = list()
                for section in json_index_list_temp:
                    start_time = temp_list[section]['start']
                    end_time = temp_list[section]['stop']
                    section_trail = (trails[(trails['Time'].values <= end_time)
                                            & (trails['Time'].values >= start_time)]).reset_index(drop=True)

                    # 根据前段轨迹调整本轨迹的位置和方向
                    rotate_tuple = ('ego_e', 'ego_n'), ('left_e', 'left_n'), ('right_e', 'right_n')
                    if trails_list:
                        section_trail = concatTrails(trails_list[-1], section_trail, rotate_tuple)
                    else:
                        section_trail = corTransform_init(section_trail, 'ego_e', 'ego_n', 'headinga', rotate_tuple)

                    trails_list.append(section_trail)

                # 将所有的轨迹数据合并为一条轨迹
                uniondata = lambda x, y: pd.concat([x, y])
                merge_trail = reduce(uniondata, trails_list)
                merge_trail = merge_trail.reset_index(drop=True)

                # 根据轨迹时间长度做重采样
                frame = len(merge_trail) / (period * 10)
                rng = pd.date_range("2020-05-10 00:00:00", periods=len(merge_trail), freq="T")
                if frame >= 1:
                    merge_trail = merge_trail[:period * 10]
                else:
                    merge_trail = resample_by_time(merge_trail, math.ceil(frame * 60), rng, flag=False)[:period * 10]
                    merge_trail['vel_filtered'] = merge_trail['vel_filtered'] * frame
                    merge_trail = merge_trail.reset_index(drop=True)

                # 选取最接近初始速度的轨迹
                speed_difference = abs(merge_trail.at[0, 'vel_filtered'] - start_speed)
                if speed_difference < previous_speed_difference:
                    final_trail = merge_trail
                    previous_speed_difference = speed_difference

    # 根据初始设定速度微调坐标
    multiple = start_speed / final_trail.loc[0, 'vel_filtered']
    final_trail = multiple_trail(final_trail, multiple, rotate_tuple)

    return final_trail, turning_angle


def get_change_lane_trail(car_trails, trails_json_dict, lane_width, start_speed, heading_angle, period, motion_status):
    """
    Parameters
    ----------
    car_trails: 原始的轨迹数据
    trails_json_dict:标记所有轨迹类型的json数据
    lane_width: 车道宽度
    start_speed:需要生成的轨迹的起始速度
    heading_angle:需要旋转的到的角度
    period:持续时间
    motion_status:轨迹运动形态
    Returns 轨迹
    -------
    """

    previous_speed_difference = 100
    trail_res = None

    # 判断需要生成的轨迹的变道类型
    change_lane_json_dict = dict()
    if motion_status == TrailMotionType.lane_change_left.value:
        min_lateral_offset = 2.5
        left_flag = True
    elif motion_status == TrailMotionType.lane_change_right.value:
        min_lateral_offset = 2.5
        left_flag = False
    elif motion_status == TrailMotionType.lane_change_left_twice.value:
        min_lateral_offset = 2.5 + lane_width
        left_flag = True
    else:
        min_lateral_offset = 2.5 + lane_width
        left_flag = False
    trails_data = copy.deepcopy(car_trails)

    # 初步筛选符合转向条件的json文件
    for motion in trails_json_dict:
        if (left_flag and 'Left change lane' in motion) or (not left_flag and 'Right change lane' in motion):
            change_lane_json_dict[motion] = list()
            for speed_status in trails_json_dict[motion]:
                change_lane_json_dict[motion] += trails_json_dict[motion][speed_status]

    # 筛选出移动距离达到变道要求切转向角度小于3度的轨迹
    optional_trails_list = list()
    for motion in change_lane_json_dict:
        change_lane_json_dict[motion] = sorted(change_lane_json_dict[motion], key=operator.itemgetter('startSpeed'),
                                               reverse=True)
        for trail_json in change_lane_json_dict[motion]:
            if (trail_json['stop'] - trail_json['start']) / 1000 < period and abs(
                    trail_json['startHeadinga'] - trail_json['stopHeadinga']) < 3 and (
                    min_lateral_offset < abs(trail_json['lateralOffset']) < 2 * min_lateral_offset):

                trail = trails_data[(trails_data['Time'] <= trail_json['stop']) & (
                        trails_data['Time'] >= trail_json['start'])].reset_index(drop=True)

                # 重新采样获得长度需要的轨迹
                frame = len(trail) / (period * 10)
                rng = pd.date_range("2020-05-10 00:00:00", periods=len(trail), freq="T")
                if frame >= 1:
                    trail = trail[:period * 10]
                else:
                    trail = resample_by_time(trail, period, rng, flag=False)[:period * 10 + 1]
                    trail['vel_filtered'] = trail['vel_filtered'] * frame
                    trail = trail.reset_index(drop=True)

                optional_trails_list.append(trail)

    # 筛选出初始速度最接近的轨迹
    for trail in optional_trails_list:
        speed_difference = abs(trail.loc[0, 'vel_filtered'] - start_speed)
        if speed_difference < previous_speed_difference:
            trail_res = trail
            previous_speed_difference = speed_difference

    rotate_tuple = ('ego_e', 'ego_n'), ('left_e', 'left_n'), ('right_e', 'right_n')

    # 根据初始设定速度微调坐标
    multiple = start_speed / trail_res.loc[0, 'vel_filtered']
    trail_res = multiple_trail(trail_res, multiple, rotate_tuple)

    # 变道场景未转角
    turning_angle = 0
    return trail_res, turning_angle


def get_turn_round_trail(car_trails, trails_json_dict, start_speed, speed_status_num, turn_round_flag, max_trails,
                         period,
                         turning_angle):
    """

    Parameters
    ----------
    car_trails: 原始的轨迹数据
    trails_json_dict:标记所有轨迹类型的json数据
    turn_round_flag: 参考枚举类TrailMotionType
    max_trails: 每种类型最多生成的轨迹数量
    period: 持续时间
    turning_angle: 跟在有转向的运动后需要转向的角度
    Returns：返回List，每个元素是一条轨迹
    -------

    """
    trails = copy.deepcopy(car_trails)
    if turn_round_flag == str(TrailMotionType.turn_left.value):
        turn_round_status = 'crossing turn_left normal'
    elif turn_round_flag == str(TrailMotionType.turn_right.value):
        turn_round_status = 'crossing turn_right normal'
    elif turn_round_flag == str(TrailMotionType.turn_around_left.value):
        turn_round_status = 'uturn_left'
    elif turn_round_flag == str(TrailMotionType.turn_around_right.value):
        turn_round_status = 'uturn_right'
    else:
        raise TypeError('运动轨迹参数错误')

    previous_speed_difference = 100
    angle_threshold = 20
    selected_trail_list = []

    for trail_motion in trails_json_dict.keys():
        if trail_motion == turn_round_status:
            for trail_speed, trail_value in trails_json_dict[trail_motion].items():
                # 不考虑转向轨迹的速度变化情况
                for single_trail in trail_value:
                    if 'crossing turn_left normal' in turn_round_status:
                        # 找到所有角度符合左转向90度的轨迹
                        if single_trail['startHeadinga'] + 90 <= 360:

                            if math.fabs(single_trail['stopHeadinga'] - single_trail['startHeadinga'] - 90) \
                                    < angle_threshold:
                                selected_trail_list.append(single_trail)
                        else:
                            if math.fabs(single_trail['stopHeadinga'] - single_trail['startHeadinga'] + 270) \
                                    < angle_threshold:
                                selected_trail_list.append(single_trail)
                    elif 'crossing turn_right normal' in turn_round_status:
                        # 找到所有角度符合右转向90度的轨迹
                        if single_trail['startHeadinga'] - 90 >= 0:

                            if math.fabs(single_trail['stopHeadinga'] - single_trail['startHeadinga'] + 90) \
                                    < angle_threshold:
                                selected_trail_list.append(single_trail)
                        else:
                            if math.fabs(single_trail['stopHeadinga'] - single_trail['startHeadinga'] - 270) \
                                    < angle_threshold:
                                selected_trail_list.append(single_trail)
                    elif 'uturn_left' in turn_round_status or 'uturn_right' in turn_round_status:
                        # 找到所有角度符合左掉头180度的轨迹,下同
                        if single_trail['startHeadinga'] + 180 <= 360:
                            if math.fabs(single_trail['stopHeadinga'] - single_trail['startHeadinga'] - 180) \
                                    < angle_threshold:
                                selected_trail_list.append(single_trail)
                        else:
                            if math.fabs(single_trail['stopHeadinga'] - single_trail['startHeadinga'] + 180) \
                                    < angle_threshold:
                                selected_trail_list.append(single_trail)

    if selected_trail_list:
        for single_json in selected_trail_list:
            # 提取轨迹数据
            start_time = single_json['start']
            end_time = single_json['stop']
            trail_new = (trails[(trails['Time'].values <= end_time)
                                & (trails['Time'].values >= start_time)]).reset_index(drop=True)

            # 根据轨迹时间长度做重采样
            frame = len(trail_new) / (period * 10)
            rng = pd.date_range("2020-05-10 00:00:00", periods=len(trail_new), freq="T")
            if frame >= 1:
                trail_new = resample_by_time(trail_new, frame, rng, flag=True)
            else:
                trail_new = resample_by_time(trail_new, math.ceil(frame * 60), rng, flag=False)
            trail_new['vel_filtered'] = trail_new['vel_filtered'] * frame
            trail_new = trail_new.reset_index(drop=True)

            # 选取最接近初始速度的轨迹
            speed_difference = abs(trail_new.at[0, 'vel_filtered'] - start_speed)
            if speed_difference < previous_speed_difference:
                final_trail = trail_new
                previous_speed_difference = speed_difference

    # 根据初始设定速度微调坐标
    rotate_tuple = ('ego_e', 'ego_n'), ('left_e', 'left_n'), ('right_e', 'right_n')
    multiple = start_speed / final_trail.loc[0, 'vel_filtered']
    final_trail = multiple_trail(final_trail, multiple, rotate_tuple)

    return final_trail, turning_angle
