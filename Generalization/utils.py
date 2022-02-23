import copy
import itertools
import math
from copy import deepcopy

import pandas as pd


class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


def dump_json(trails_label_json):
    """
    Parameters
    JSON格式
    "carID": "dongfeng",
    "start": 1616577524353.0,
    "stop": 1616577525353.0,
    "startHeadinga": 175.1166073108493,
    "stopHeadinga": 176.21322211682332,
    "startSpeed": 1.736722031318881,
    "stopSpeed": 0.000153704950162519,
    "longituteType": "Stop",
    "longituteOffset": 0.29471901585877686,
    "lateralType": "No change lane",
    "lateralOffset": 0.0,
    "crossPoint": 0,
    "carTrailPath": "/media/lxj/cicv_008/carTrails.csv",
    "pedTrailPath": "/media/lxj/cicv_008/pedTrails.csv"

    Returns: 返回包含所有轨迹的dict{k(变道情况):v(加速情况{[单条轨迹,]})}
    """
    motion_fromkeys = ('No change lane', 'Left change lane', 'Right change lane', 'crossing turn_right normal',
                       'crossing turn_left normal', 'uturn_left', 'uturn_right')
    trails_label_json_dict = {}.fromkeys(motion_fromkeys, {})
    velocity_fromkeys = ('Accelerate', 'Decelerate', 'Uniform speed', 'Various speed', 'no type', 'Start', 'Stop')
    for motion in motion_fromkeys:
        trails_label_json_dict[motion] = {key: [] for key in velocity_fromkeys}
    for trails_json in trails_label_json:
        # 有一部分轨迹变道情况不在默认值内
        if trails_json['lateralType'] not in motion_fromkeys:
            trails_label_json_dict[trails_json['lateralType']] = {key: [] for key in velocity_fromkeys}
        trails_label_json_dict[trails_json['lateralType']][trails_json['longituteType']].append(deepcopy(trails_json))
    return trails_label_json_dict


def rotate(x_list, y_list, ox, oy, rad):
    """
    position_list (list): a list of tuples; (x, y, z, h, p, r)
    deg: clock-wise radius
    ox: rotate center point x coordination
    oy: rotate center point y coordination
    """
    x_res = []
    y_res = []
    for index in range(len(x_list)):
        x = (x_list[index] - ox) * math.cos(rad) + (y_list[index] - oy) * math.sin(rad) + ox
        y = - (x_list[index] - ox) * math.sin(rad) + (y_list[index] - oy) * math.cos(rad) + oy
        x_res.append(x)
        y_res.append(y)

    return x_res, y_res


def spin_trans_form(position_e, position_n, trail_new, rad=0, trails_count=1, **trail):
    """
    根据trail对trail_new做旋转变换

    Parameters
    trail : TYPE
        要拼接的轨迹.
    e : TYPE
        e列名称.
    n : TYPE
        n列名称.
    rad : TYPE
        旋转角度，弧度值.
    trail_new : TYPE
        处理后的trail2.

    Returns
    -------
    trail_new : TYPE
        处理后的trail2.

    """
    if trails_count == 1:
        e_offset = trail['trail'].iloc[-1][position_e] - trail['trail'].iloc[0][position_e]
        n_offset = trail['trail'].iloc[-1][position_n] - trail['trail'].iloc[0][position_n]
    else:
        e_offset = trail['trail'].iloc[-1][position_e] - trail['trail_next'].iloc[0][position_e]
        n_offset = trail['trail'].iloc[-1][position_n] - trail['trail_next'].iloc[0][position_n]
    trail_new[position_e] += e_offset
    trail_new[position_n] += n_offset
    deg = math.degrees(rad)
    new_position_e, new_position_n = rotate(trail_new[position_e], trail_new[position_n],
                                            trail_new.iloc[0][position_e], trail_new.iloc[0][position_n], rad)
    trail_new[position_e] = new_position_e
    trail_new[position_n] = new_position_n
    trail_new['headinga'] += deg
    return trail_new


def resample_by_time(data, minutes, datetime, flag=True):
    """
    resample by time window
    return first value of resampled data
    :param data: 输入数据，dataframe
    :param minutes: 按几分钟resample，float
    :param datetime: 日期时间变量名，str
    :param flag: True 向下采样; False 向上采样
    :return: 输出结果，dataframe
    """
    data.index = datetime
    if minutes == 0:
        minutes = 1
    if flag:
        scale = str(minutes) + 'T'
        r = data.resample(scale).first()
    else:
        scale = str(minutes) + 'S'
        r = data.resample(scale).interpolate()
    return r.reset_index(drop=True)


def get_adjust_trails(trails_count, **trail):
    """
    想要将trail2拼接到trail1之后，保证拼接部位平滑，需要对trail2做平移和旋转变换，返回处理后的trail2

    Parameters
    ----------
    trail : TYPE
        轨迹的数据.
    trails_count:
    1:单挑轨迹增加
    2：两条轨迹拼

    Returns
    -------
    trail_new : TYPE
        处理后的trail.

    """
    if trails_count == 1:
        trail_new = copy.deepcopy(trail['trail'])
        deg = 0

    else:
        trail_new = copy.deepcopy(trail['trail'])
        deg = trail['trail'].iloc[-1]['headinga'] - trail_new.at[0, 'headinga']

    trail['trail'] = trail['trail'].reset_index(drop=True)
    # deg = -trail_new.at[0, 'headinga']
    rad = math.radians(deg)
    for col in (('ego_e', 'ego_n'), ('left_e', 'left_n'), ('right_e', 'right_n')):
        trail_new = spin_trans_form(*col, trail_new, rad, trails_count, **trail)
    trail_new['headinga'] += deg
    return trail_new


def get_lane_distance(trail, trail_frame, required_change_distance):
    """
    @param trail: 轨迹
    @param trail_frame: 轨迹当中的某一帧
    @param required_change_distance: 如果要达到变道的效果，在这条车道中需要移动的距离
    @return: 这一帧中移动的距离减去达到变道效果需要移动的距离
    """
    offset_e = math.fabs(trail_frame['ego_e'] - trail.at[0, 'ego_e'])
    return math.fabs(offset_e - required_change_distance)


def get_finale_trail(merge_trail, period, turning_angle):
    spin_trail = (spin_trans_form(position_e='ego_e', position_n='ego_n',
                                  trail_new=merge_trail.copy(),
                                  trails_count=1, trail=merge_trail).iloc[::-1])[1:]
    merge_trail = pd.concat([merge_trail, spin_trail], axis=0).reset_index(drop=True)
    frame = math.ceil(period * 10 / len(merge_trail))
    merge_trail = spin_trans_form(position_e='ego_e', position_n='ego_n',
                                  trail_new=merge_trail.copy(),
                                  deg=turning_angle, trails_count=1, trail=merge_trail)

    merge_trail.loc[merge_trail.index[-1], 'Time'] = merge_trail.iloc[-2]['Time'] + (
            merge_trail.iloc[-2]['Time'] - merge_trail.iloc[-3]['Time'])
    static_time = pd.date_range('2021-01-01 00:00:00', periods=len(merge_trail), freq='T')
    if frame > 1:
        sample = math.floor(60 / frame)
        merge_trail = resample_by_time(merge_trail, sample, static_time, False)
    else:
        sample = math.floor(len(merge_trail) / (period * 10))
        merge_trail = resample_by_time(merge_trail, sample, static_time, True)
    start_point = Point(merge_trail.at[0, 'ego_e'], merge_trail.at[0, 'ego_n'])
    merge_trail['ego_e'] -= start_point.x
    merge_trail['ego_n'] -= start_point.y
    merge_trail.reset_index(drop=True)
    return merge_trail


def get_connect_trail(position_trail_list, trajectory):
    """
    用于物体不同形态轨迹之间连接
    @param position_trail_list: 二维数组，第一维以轨迹形态划分，第二位以单个轨迹划分
    @param trajectory: 物体运动轨迹形态的标志位
    @return
    position_trail_list:已经连接好的传物体轨迹形态列表
    road_list:根据轨迹生成的road_list
    """
    road_list = list()
    behind_motion_trail_list = position_trail_list[1]
    position_trail_list[0], position_trail_list[1], road_list = connect_trail(
        position_trail_list[0], behind_motion_trail_list, trajectory, road_list)
    if len(position_trail_list) > 2:
        get_connect_trail(position_trail_list[1:], trajectory)
    else:
        return position_trail_list
    return position_trail_list, road_list


def connect_trail(front_trail, behind_trail, trajectory, road_list):
    for f_single_trail in front_trail:
        end_x = f_single_trail.iloc[-1]['ego_e']
        end_y = f_single_trail.iloc[-1]['ego_n']
        end_heading_angle = f_single_trail.iloc[-1]['headinga']
        end_speed = f_single_trail.iloc[-1]['vel_filtered']

        end_point = Point(end_x, end_y)
        road_list.append(end_point)

        return front_trail, behind_trail, road_list


def change_speed(scenario_speed):
    if not type(scenario_speed) == list:
        changed_speed = scenario_speed * 3.6
    else:
        changed_speed = [speed * 3.6 for speed in scenario_speed]
    return changed_speed


def multiple_uniform_trail(trail, multiple, start_speed):
    trail['vel_filtered'] = start_speed
    trail.loc[1:, 'ego_e'] = trail.loc[1:, 'ego_e'] * multiple
    trail.loc[1:, 'ego_n'] = trail.loc[1:, 'ego_n'] * multiple
    return trail


def format_straight_trail(trail):
    headinga_avg = trail['headinga'].mean()
    trail['headinga'] = 0
    trail['ego_e'] = 0
    trail['ego_n'] = trail['ego_n'] / (math.cos(math.radians(headinga_avg)))
    return trail