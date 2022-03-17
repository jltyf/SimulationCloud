import math
from copy import deepcopy
from functools import reduce
from sklearn import metrics
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from scenariogeneration import xosc
import os
import json
from enumerations import DataType


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


def corTransform(trail1, trail2, e, n, rad, trail_new):
    '''
    依据trail1, 通过平移和旋转功能调整trail2

    Parameters
    ----------
    trail1 : 基准轨迹, dataframe
    trail2 : 待操作轨迹, dataframe
    e : e列名, str
    n : n列名, str
    rad : 旋转角度，弧度值
    trail_new : 待返回的轨迹, dataframe
    trail_new是复制trail2的, 防止对trail2操作影响了后续轨迹
    Returns
    -------
    通过平移和旋转功能调整的trail_new

    '''

    e_offset = trail1.at[len(trail1) - 1, e] - trail2.at[0, e]
    n_offset = trail1.at[len(trail1) - 1, n] - trail2.at[0, n]
    trail_new[e] += e_offset
    trail_new[n] += n_offset
    a, b = rotate(trail_new[e], trail_new[n], trail_new.at[0, e], trail_new.at[0, n], rad)
    trail_new[e] = a
    trail_new[n] = b
    return trail_new


def corTransform_init(trail, e, n, h, *args, init_e=0, init_n=0, init_h=0):
    '根据给定初始的位置和角度调整一条轨迹'
    e_offset = init_e - trail.at[0, e]
    n_offset = init_n - trail.at[0, n]
    deg = trail.at[0, h] - init_h
    rad = math.radians(deg)

    for rotate_tuple in args[0]:
        trail[rotate_tuple[0]] += e_offset
        trail[rotate_tuple[1]] += n_offset
        a, b = rotate(trail[rotate_tuple[0]], trail[rotate_tuple[1]], init_e, init_n, rad)
        trail[rotate_tuple[0]] = a
        trail[rotate_tuple[1]] = b
    trail[h] -= deg
    return trail


def concatTrails(trail1, trail2, *args):
    '根据前一条轨迹trail1的末尾位置和角度调整下一条轨迹trail2, 主要的平移和旋转功能是corTransform实现的'
    trail_new = trail2.copy()
    deg = trail1.at[len(trail1) - 1, 'headinga'] - trail_new.at[0, 'headinga']
    rad = math.radians(-deg)
    for rotate_tuple in args[0]:
        trail_new = corTransform(trail1, trail2, rotate_tuple[0], rotate_tuple[1], rad, trail_new)

    trail_new['headinga'] += deg
    trail_new = trail_new.reset_index(drop=True)
    trail_new = trail_new.drop([0])
    return trail_new


def generateFinalTrail(name, lista, e, n, h, *args, init_e=0, init_n=0, init_h=0):
    '将一个轨迹list里的多个元素拼接为一条轨迹'
    if lista:
        ego_trail = []
        # 初始轨迹坐标为原点，headingAngle为0
        ego_trail.append(corTransform_init(lista[0], e, n, h, args[0], init_e=init_e, init_n=init_n, init_h=init_h))
        if len(lista) == 1:
            print(name, "找到一条完整轨迹不需要拼接")
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


def trailModify(ego_trail, t, e, h):
    '轨迹微调，根据最后一帧航向角偏离的程度，按插值比例偏移回中线位置'
    max_h = ego_trail.at[len(ego_trail) - 1, h] - ego_trail.at[0, h]
    max_time = ego_trail.index.tolist()[-1]
    max_e = ego_trail.at[len(ego_trail) - 1, e] - ego_trail.at[0, e]
    ego_trail[e] = ego_trail.apply(lambda x: x[e] - max_e * x.name / max_time, axis=1)
    ego_trail[h] = ego_trail.apply(lambda x: x[h] - max_h * x.name / max_time, axis=1)

    return ego_trail


def getXoscPosition(egodata, t, e, n, h, offset_x, offset_y, offset_h):
    '将dataframe的轨迹转换为场景文件的轨迹数据'

    position = []
    time = []
    egodata = egodata[[t, e, n, h]]
    egodata = egodata.reset_index(drop=True)
    egodata[t] = egodata.index / 10
    egodata[e] = egodata[e] + offset_x
    egodata[n] = egodata[n] + offset_y
    egodata[h] = egodata[h] + offset_h

    lasth = float(egodata.at[0, h])
    init_flag = True

    for row in egodata.iterrows():
        hhh = math.radians(row[1][h])
        if init_flag:
            position.append(xosc.WorldPosition(x=float(row[1][e]), y=float(row[1][n]), z=0, h=hhh, p=0, r=0))
            init_flag = False
        else:
            if float(row[1][h]) - lasth > 300:
                hhh = math.radians(float(row[1][h]) - 360)
            elif float(row[1][h]) - lasth < -300:
                hhh = math.radians(float(row[1][h]) + 360)
            position.append(xosc.WorldPosition(x=float(row[1][e]), y=float(row[1][n]), z=0, h=hhh, p=0, r=0))
            lasth = hhh
        time.append(float(row[1][t]))
    return position, time


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


def multiple_uniform_trail(trail, multiple, *args):
    if multiple - 0 < 0.01:
        return trail
    else:
        for rotate_tuple in args[0]:
            trail.loc[:, rotate_tuple[0]] = trail.loc[:, rotate_tuple[0]] * multiple
            trail.loc[:, rotate_tuple[1]] = trail.loc[:, rotate_tuple[1]] * multiple
        trail['vel_filtered'] = trail['vel_filtered'] * multiple
        return trail


def get_cal_model(scenario_dict):
    """
    通过计算,完整的场景配置
    :param scenario_dict: 单个场景参数(已泛化)
    :return: 已经完全泛化的场景配置列表，每个元素为泛化的一个场景配置
    """
    for key, values in scenario_dict['generalization_type'].items():
        if values == DataType.calculative.value:
            ep_x = change_factor_type(scenario_dict['ego_start_x']) if key != 'ego_start_x' else ''
            ep_y = change_factor_type(scenario_dict['ego_start_y']) if key != 'ego_start_y' else ''
            ev = change_factor_type(scenario_dict['ego_start_velocity']) if key != 'ego_start_velocity' else ''
            ev_t = scenario_dict['ego_velocity_time'] if key != 'ego_velocity_time' else ''
            et_t = scenario_dict['ego_trajectory_time'] if key != 'ego_trajectory_time' else ''
            if scenario_dict['obs_start_x']:
                op_x = change_factor_type(scenario_dict['obs_start_x']) if key != 'obs_start_x' else ''
                op_y = change_factor_type(scenario_dict['obs_start_y']) if key != 'obs_start_y' else ''
                ov = change_factor_type(
                    scenario_dict['obs_start_velocity']) if key != 'obs_start_velocity' else ''
                ov_t = eval(scenario_dict['obs_velocity_time'][0]) if key != 'obs_velocity_time' else ''
                ot_t = eval(scenario_dict['obs_trail_time'][0]) if key != 'obs_trail_time' else ''
                ov_t = ov_t if isinstance(ov_t, list) else [ov_t]
                ot_t = ot_t if isinstance(ot_t, list) else [ot_t]
            formula = str(scenario_dict[key])
            if "'" in formula:
                formula = formula.split("'")[1]
            if len(scenario_dict[key]) > 1:
                other_obj = scenario_dict[key][1:]
                formula = [eval(formula)] + other_obj
            else:
                formula = [eval(formula)]
            scenario_dict[key] = formula
    return scenario_dict


def change_factor_type(factor):
    if isinstance(factor, list):
        factor = change_factor_type(factor[0])
    return float(factor)


def getLabel(output_path, func_ind, func_name):
    '''
    生成label.json文件
    '''
    labeljson = {}
    labeljson['functional_module'] = [func_ind]
    labeljson['scene_type'] = func_name
    labeljson['rode_type'] = "城市普通道路"
    labeljson['rode_section'] = "路段"
    with open(os.path.join(output_path, output_path.split('/')[-1] + '.json'), 'w', encoding='utf-8') as f:
        json.dump(labeljson, f, indent=4, ensure_ascii=False)


def get_ped_data(ped_trail):
    """
    输入行人轨迹组成的df,按照不同轨迹分类,然后用最小二乘法计算出行人轨迹的航向角
    :param ped_trail:行人轨迹的dataframe
    :return:分类好的dataframe
    """
    ped_columns_list = ped_trail.columns.tolist() + ['part']
    sketch_columns_list = ['start', 'stop', 'period', 'part']
    new_pd = pd.DataFrame(columns=ped_columns_list)
    ped_trail_sketch_df = pd.DataFrame(columns=sketch_columns_list)
    trail_count = 1
    for key, value in ped_trail.groupby('flag'):
        single_trails_group = value.groupby((abs(value.Time - value.Time.shift()) > 2000).cumsum())
        # 计算出行人轨迹的heading angle
        for index, trail in single_trails_group:
            if len(trail) > 15 and trail['ObjectAbsVel'].max() < 10 and trail['ObjectAbsVel'].mean() > 1:
                x_array = np.array(trail.ped_e.values.tolist())
                y_array = np.array(trail.ped_n.values.tolist())
                m = len(y_array)
                x_bar = np.mean(x_array)
                sum_yx = 0
                sum_x2 = 0
                sum_delta = 0
                for i in range(m):
                    x = x_array[i]
                    y = y_array[i]
                    sum_yx += y * (x - x_bar)
                    sum_x2 += x ** 2
                w = sum_yx / (sum_x2 - m * (x_bar ** 2))
                for i in range(m):
                    x = x_array[i]
                    y = y_array[i]
                    sum_delta += (y - w * x)
                b = sum_delta / m
                pred_y = w * x_array + b

                mse = metrics.mean_squared_error(y_array, pred_y)
                # 通过方差判断行人轨迹是否笔直,还需要再设置阈值
                if mse < 0.15:
                    if (y_array[-1] - y_array[0]) > 0:
                        rad = math.atan(w)
                    else:
                        rad = math.atan(w) + math.pi
                    if rad < 0:
                        rad = 2 * math.pi + rad
                    heading_angle = math.degrees(rad)
                    trail['part'] = trail_count
                    trail['headinga'] = heading_angle
                    temp_df = pd.DataFrame({
                        "start": [trail.iloc[0]['Time']],
                        'stop': [trail.iloc[-1]['Time']],
                        'period': [round((trail.iloc[-1]['Time'] - trail.iloc[0]['Time']) / 1000, 2)],
                        'part': [trail.iloc[0]['part']]
                    })
                    if trail_count == 0:
                        new_pd = pd.concat([new_pd, trail], axis=0)
                        ped_trail_sketch_df = (pd.concat([ped_trail_sketch_df, temp_df], axis=0)).reset_index(drop=True)
                        trail_count += 1
                    else:
                        if not temp_df.iloc[0]['start'] in ped_trail_sketch_df['start'].values:
                            new_pd = pd.concat([new_pd, trail], axis=0)
                            ped_trail_sketch_df = (pd.concat([ped_trail_sketch_df, temp_df], axis=0)).reset_index(
                                drop=True)
                            trail_count += 1
    return new_pd, ped_trail_sketch_df
