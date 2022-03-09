import copy
import math
from copy import deepcopy
from functools import reduce
import pandas as pd
from scenariogeneration import xosc


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
        # e_offset = -trail['trail'].at[0, position_e]
        # n_offset = -trail['trail'].at[0, position_n]
        e_offset = trail['trail'].iloc[-1][position_e] - trail['trail'].iloc[0][position_e]
        n_offset = trail['trail'].iloc[-1][position_n] - trail['trail'].iloc[0][position_n]
    else:
        e_offset = trail['trail'].iloc[-1][position_e] - trail['trail_next'].iloc[0][position_e]
        n_offset = trail['trail'].iloc[-1][position_n] - trail['trail_next'].iloc[0][position_n]
    trail_new[position_e] += e_offset
    trail_new[position_n] += n_offset
    deg = math.degrees(rad)
    new_position_e, new_position_n = rotate(trail_new[position_e], trail_new[position_n],
                                            trail_new.iloc[0][position_e], trail_new.iloc[0][position_n], deg)
    trail_new[position_e] = new_position_e
    trail_new[position_n] = new_position_n
    trail_new['headinga'] += deg
    return trail_new


def corTransform(trail1, trail2, e, n, rad, trail_new):
    e_offset = trail1.at[len(trail1) - 1, e] - trail2.at[0, e]
    n_offset = trail1.at[len(trail1) - 1, n] - trail2.at[0, n]
    trail_new[e] += e_offset
    trail_new[n] += n_offset
    a, b = rotate(trail_new[e], trail_new[n], trail_new.at[0, e], trail_new.at[0, n], rad)
    trail_new[e] = a
    trail_new[n] = b
    return trail_new


def corTransform_init(trail, e, n, h, *args, init_e=0, init_n=0, init_h=0):
    e_offset = init_e - trail.at[0, e]
    n_offset = init_n - trail.at[0, n]
    deg = trail.at[0, h] - init_h
    rad = math.radians(deg)

    for rotate_tuple in args[0]:
        trail[rotate_tuple[0]] += e_offset
        trail[rotate_tuple[1]] += n_offset
        a, b = rotate(trail[rotate_tuple[0]], trail[rotate_tuple[1]], 0, 0, rad)
        trail[rotate_tuple[0]] = a
        trail[rotate_tuple[1]] = b
    trail[h] -= deg
    return trail


def concatTrails(trail1, trail2, *args):
    trail_new = trail2.copy()
    deg = trail1.at[len(trail1) - 1, 'headinga'] - trail_new.at[0, 'headinga']
    rad = math.radians(-deg)
    for rotate_tuple in args[0]:
        trail_new = corTransform(trail1, trail2, rotate_tuple[0], rotate_tuple[1], rad, trail_new)

    trail_new['headinga'] += deg
    return trail_new


def generateFinalTrail(name, lista, e, n, h, *args, init_e=0, init_n=0, init_h=0):
    '将一个轨迹list里的多个元素拼接为一条轨迹'
    if lista:
        ego_trail = []
        # 初始轨迹坐标为原点，headingAngle为0
        ego_trail.append(corTransform_init(lista[0], 'ego_e', 'ego_n', 'headinga', args[0], 0, 0, 0))
        if len(lista) == 1:
            print(name, "不需要拼接")
        elif len(lista) > 1:
            for index in range(1, len(lista)):
                ego_trail.append(concatTrails(ego_trail[-1], lista[index], args[0]))
        # 将所有的轨迹数据合并为一条轨迹
        uniondata = lambda x, y: pd.concat([x, y])
        ego_merge_trail = reduce(uniondata, ego_trail)
        ego_merge_trail = ego_merge_trail.reset_index(drop=True)
        return ego_merge_trail
    else:
        return lista


def getEgoPosition(egodata, t, e, n, h):
    position = []
    time = []
    egodata = egodata[[t, e, n, h]]
    egodata = egodata.reset_index(drop=True)
    egodata[t] = egodata.index / 10

    for row in egodata.iterrows():
        position.append(xosc.WorldPosition(x=float(row[1][e]), y=float(row[1][n]), h=math.radians(float(row[1][h]))))
        time.append(float(row[1]['Time']))
    return position, time


def rotate_trail(trail, headinga, *args):
    """
    轨迹要求：1.已经经过平移(自车在原点，目标车经过平移)2时间戳经过重新采样长度符合分段轨迹持续时间
    函数功能：1args的参数全部按照headinga旋转至
            以自车起点为原点
            以自车起点朝向角为y轴的坐标系
            2按照轨迹分段持续时间重新为轨迹时间赋值
            3将轨迹朝向角度调整为自车起始位置的朝向角
    :param trail:需要旋转的轨迹
    :param headinga:此轨迹中自车第一帧的朝向角度
    :param args:需要旋转的列名(如ego_e,ego_n,left_e,left_n)
    :return:旋转过后的轨迹
    """
    ego_init_rad = math.radians(headinga)
    start_time = trail.iloc[0]['Time']
    init_data = [headinga, trail.iloc[0]['Time']]
    temp_trail = deepcopy(trail)
    trail['Time'] = (trail['Time'] - start_time) / 1000
    trail['headinga'] = trail['headinga'] - init_data[0]
    for rotate_tuple in args[0]:
        trail[rotate_tuple[0]] = temp_trail[[rotate_tuple[0], rotate_tuple[1]]].apply(
            lambda x: x[rotate_tuple[0]] * math.cos(ego_init_rad) + x[rotate_tuple[1]] * math.sin(ego_init_rad), axis=1)
        trail[rotate_tuple[1]] = temp_trail[[rotate_tuple[0], rotate_tuple[1]]].apply(
            lambda x: -x[rotate_tuple[0]] * math.sin(ego_init_rad) + x[rotate_tuple[1]] * math.cos(ego_init_rad),
            axis=1)
    return trail


def resample_by_time(data, minnum, dt, flag=True):
    """
    resample by time window
    return first value of resampled data
    :param data: 输入数据，dataframe
    :param minnum: 按几分钟resample，float
    :param dt: 日期时间变量名，str
    :param flag: True 向下采样; False 向上采样
    :return: 输出结果，dataframe
    """
    data.index = dt
    if minnum == 0:
        minnum = 1
    if flag:
        if isinstance(minnum, int):
            scale = str(minnum) + 'T'
            r = data.resample(scale).first()
            return r
        elif isinstance(minnum, float):

            scale = str(3) + 'S'  # 3s 为基准
            r = data.resample(scale).interpolate()
            scale = str(round(60 * minnum)) + 'S'  # 速度扩大minnum倍
            r = r.resample(scale).interpolate()
            return r
    else:
        scale = str(minnum) + 'S'
        r = data.resample(scale).interpolate()
        return r


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


def get_connect_trail(trails_list, trajectory):
    """
    用于物体不同形态轨迹之间连接
    @param trails_list: 多段轨迹形成的列表
    @param trajectory: 物体运动轨迹形态的标志位
    @return
    position_trail_list:已经连接好的传物体轨迹形态列表
    """
    trails_list[0], trails_list[1] = connect_trail(trails_list[0], trails_list[1], trajectory)
    if len(trails_list) > 2:
        get_connect_trail(trails_list[1:], trajectory)
    else:
        return trails_list
    return trails_list


def connect_trail(front_trail, behind_trail, trajectory):
    # print(front_trail, behind_trail, trajectory)
    # for b_single_trail in behind_trail:
    #     b_single_trail.diff(periods=1, axis=0)
    reset_tuple = ((1, 2), (2, 3), (3, 4))

    for f_single_trail in front_trail:
        end_x = f_single_trail.iloc[-1]['ego_e']
        end_y = f_single_trail.iloc[-1]['ego_n']
        end_heading_angle = f_single_trail.iloc[-1]['headinga']
        end_speed = f_single_trail.iloc[-1]['vel_filtered']

        end_point = Point(end_x, end_y)

    return front_trail, behind_trail


def multiple_uniform_trail(trail, multiple, *args):
    for rotate_tuple in args[0]:
        trail.loc[1:, rotate_tuple[0]] = trail.loc[1:, rotate_tuple[0]] * multiple
        trail.loc[1:, rotate_tuple[1]] = trail.loc[1:, rotate_tuple[1]] * multiple
    trail['vel_filtered'] = trail['vel_filtered'] * multiple
    return trail
