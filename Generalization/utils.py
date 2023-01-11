import ast
import math
from configparser import ConfigParser
from copy import deepcopy
from functools import reduce
from pathlib import Path
from math import sin
from math import cos
from math import pi

from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator
from sklearn import metrics
import numpy as np
import pandas as pd
from scenariogeneration import xosc
import os
import json
from enumerations import DataType, TrailMotionType, RoadType, ObjectType
from scenariogeneration.xodr import RoadSide, Object, Dynamic, Orientation
import xml.etree.ElementTree as ET


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


def extractTrail(trails, start_time, end_time):
    '从原始轨迹中提取一段数据'
    single_trail = (trails[(trails['Time'].values <= end_time)
                           & (trails['Time'].values >= start_time)]).reset_index(drop=True)
    # single_partID = single_trail.at[0, 'partID']
    single_partID = single_trail.partID.value_counts().idxmax()
    single_trail = single_trail[single_trail['partID'] == single_partID]
    single_trail = single_trail.reset_index(drop=True)
    return single_trail


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
    trail = trail.reset_index(drop=True)
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
    trail1 = trail1.reset_index(drop=True)
    trail2 = trail2.reset_index(drop=True)
    trail_new = trail2.copy()
    deg = trail1.at[len(trail1) - 1, 'headinga'] - trail_new.at[0, 'headinga']
    rad = math.radians(-deg)
    for rotate_tuple in args[0]:
        trail_new = corTransform(trail1, trail2, rotate_tuple[0], rotate_tuple[1], rad, trail_new)

    trail_new['headinga'] += deg
    trail_new = trail_new.reset_index(drop=True)
    trail_new = trail_new.drop([0])
    trail_new = trail_new.reset_index(drop=True)
    return trail_new


def generateFinalTrail(name, lista, e, n, h, *args, init_e=0, init_n=0, init_h=0):
    '将一个轨迹list里的多个元素拼接为一条轨迹'
    if lista:
        trail = []
        # 初始轨迹坐标为原点，headingAngle为0
        trail.append(corTransform_init(lista[0], e, n, h, args[0], init_e=init_e, init_n=init_n, init_h=init_h))
        if len(lista) == 1:
            print(name, "找到一条完整轨迹不需要拼接")
        elif len(lista) > 1:
            for index in range(1, len(lista)):
                trail.append(concatTrails(trail[-1], lista[index], args[0]))
        # 将所有的轨迹数据合并为一条轨迹
        uniondata = lambda x, y: pd.concat([x, y])
        merge_trail = reduce(uniondata, trail)
        merge_trail = merge_trail.reset_index(drop=True)
        return merge_trail
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


def getXoscPosition(egodata, t, e, n, h, offset_x, offset_y, offset_h, offset_z=0):
    '将dataframe的轨迹转换为场景文件的轨迹数据'
    position = []
    time = []
    egodata = egodata[[t, e, n, h]]
    egodata = egodata.reset_index(drop=True)
    egodata[t] = egodata.index / 10
    egodata[n], egodata[e] = rotate(egodata[n], egodata[e], 0, 0, math.radians(offset_h-90))
    # tmp_data = egodata
    # egodata[n] = tmp_data[e] * math.cos(math.radians(offset_h-(90-offset_h)/6)) + tmp_data[n] * math.sin(math.radians(offset_h-(90-offset_h)/6))
    # egodata[e] = tmp_data[n] * math.cos(math.radians(offset_h-(90-offset_h)/6)) - tmp_data[e] * math.sin(math.radians(offset_h-(90-offset_h)/6))
    egodata[e] = egodata[e] + offset_x
    egodata[n] = egodata[n] + offset_y
    egodata[h] = egodata[h] + offset_h
    # egodata[h] += 180

    lasth = float(egodata.at[0, h])
    init_flag = True

    for row in egodata.iterrows():
        hhh = math.radians(row[1][h])
        if init_flag:
            position.append(xosc.WorldPosition(x=float(row[1][e]), y=float(row[1][n]), z=offset_z, h=hhh, p=0, r=0))
            init_flag = False
        else:
            if float(row[1][h]) - lasth > 300:
                hhh = math.radians(float(row[1][h]) - 360)
            elif float(row[1][h]) - lasth < -300:
                hhh = math.radians(float(row[1][h]) + 360)
            position.append(xosc.WorldPosition(x=float(row[1][e]), y=float(row[1][n]), z=offset_z, h=hhh, p=0, r=0))
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
            r = data.resample(scale).interpolate(method='linear')
            scale = str(round(60 * minnum)) + 'S'  # 速度扩大minnum倍
            r = r.resample(scale).interpolate()
            return r
    else:
        scale = str(minnum) + 'S'
        r = data.resample(scale).interpolate(method='linear')
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
    range_flag = True
    cal_list = list()
    for key, values in scenario_dict['generalization_type'].items():
        if values == DataType.calculative.value:
            cal_list.append(key)
        elif values > 10:
            for obj_index in range(len(str(values))):
                if int(str(values)[obj_index]) == DataType.calculative.value:
                    cal_list.append(key)
    for key, values in scenario_dict['generalization_type'].items():
        obj_param = list()
        if values > 10:
            for obj_index in range(len(str(values))):
                obj_param.append(int(str(values)[obj_index]))
        else:
            obj_param = [values]
        for obj_index in range(len(obj_param)):
            values = obj_param[obj_index]
            if values == DataType.calculative.value or values == DataType.generalizable_limit.value:
                ep_x = change_factor_type(scenario_dict['ego_start_x'])
                ep_y = change_factor_type(scenario_dict['ego_start_y'])
                ev = change_factor_type(scenario_dict['ego_start_velocity'])
                ev_t = scenario_dict['ego_velocity_time']
                et_t = scenario_dict['ego_trajectory_time']
                if scenario_dict['scenario_road_type'] == RoadType.city_curve_left.value \
                        or scenario_dict['scenario_road_type'] == RoadType.city_curve_right.value:
                    rc = scenario_dict['scenario_radius_curvature'][0]
                if scenario_dict['obs_start_x']:
                    # op_x = change_factor_type(scenario_dict['obs_start_x'])
                    # op_y = change_factor_type(scenario_dict['obs_start_y'])
                    # # ov = change_factor_type(
                    # #     scenario_dict['obs_start_velocity']) if key != 'obs_start_velocity' else ''
                    # ov = change_factor_type(scenario_dict['obs_start_velocity'])
                    # ov_t = eval(scenario_dict['obs_velocity_time'][0])
                    # ot_t = eval(scenario_dict['obs_trail_time'][0])
                    # ov_t = ov_t if isinstance(ov_t, list) else [ov_t]
                    # ot_t = ot_t if isinstance(ot_t, list) else [ot_t]
                    # op_x = list(map(float, scenario_dict['obs_start_x'])) if 'obs_start_x' not in cal_list else [
                    #                                                                                                 ''] * len(
                    #     obj_param)
                    # op_y = list(map(float, scenario_dict['obs_start_y'])) if 'obs_start_y' not in cal_list else [
                    #                                                                                                 ''] * len(
                    #     obj_param)
                    # ov = change_factor_type(
                    #     scenario_dict['obs_start_velocity']) if key != 'obs_start_velocity' else ''
                    # ov = list(
                    #     map(float, scenario_dict['obs_start_velocity'])) if 'obs_start_velocity' not in cal_list else [
                    #                                                                                                       ''] * len(
                    #     obj_param)
                    op_x = format_obs_data('obs_start_x', scenario_dict, cal_list)
                    op_y = format_obs_data('obs_start_y', scenario_dict, cal_list)
                    ov = format_obs_data('obs_start_velocity', scenario_dict, cal_list)
                    # if values == DataType.generalizable_limit.value:
                    #     ov[obj_index] = scenario_dict['obs_start_velocity'][obj_index]
                    ov_t = scenario_dict['obs_velocity_time']
                    ot_t = scenario_dict['obs_trail_time']
                    ov_t = ov_t if isinstance(ov_t, list) else [ov_t]
                    ot_t = ot_t if isinstance(ot_t, list) else [ot_t]
                if values == DataType.calculative.value:
                    constant_count = len(scenario_dict[key]) - 1
                    for obj_data in scenario_dict[key]:
                        if isinstance(obj_data, (int, float)):
                            constant_count -= 1
                    formula = str(scenario_dict[key])
                    if "'" in formula:
                        a = formula.split("'")
                        if len(scenario_dict[key]) > 1:
                            formula = formula.split("'")[2 * constant_count + obj_index]
                        else:
                            formula = formula.split("'")[1]
                    # if not isinstance(scenario_dict[key], str) and len(scenario_dict[key]) > 1:
                    #     other_obj = scenario_dict[key][1:]
                    #     formula = [eval(formula)] + other_obj
                    else:
                        formula = [eval(formula)]
                    if 'obs' in key:
                        scenario_dict[key][obj_index] = eval(formula)
                    else:
                        scenario_dict[key] = formula
                elif values == DataType.generalizable_limit.value:
                    formula = scenario_dict[key + f'{obj_index}_limit']
                    if eval(formula):
                        range_flag = True
                    else:
                        range_flag = False
                        return scenario_dict, range_flag
            if 'ego' in key and isinstance(scenario_dict[key], list):
                scenario_dict[key] = change_factor_type(scenario_dict[key][0])

    return scenario_dict, range_flag


def change_factor_type(factor):
    if isinstance(factor, list):
        try:
            factor = change_factor_type(factor[0])
        except:
            factor = ''
    try:
        return float(factor)
    except:
        return factor


def format_obs_data(data_name, scenario_dict, cal_list):
    format_data = list(map(float, scenario_dict[data_name])) if data_name not in cal_list else [''] * len(
        scenario_dict[data_name])
    # obs_amount = len(obs_data)
    for boj in scenario_dict[data_name]:
        index = scenario_dict[data_name].index(boj)
        try:
            format_data[scenario_dict[data_name].index(boj)] = float(scenario_dict[data_name][index])
        except:
            format_data[scenario_dict[data_name].index(boj)] = scenario_dict[data_name][index]
    return format_data


def getLabel_local(output_path, func_ind, func_name, max_time=20):
    '''
    生成label.json文件
    '''
    labeljson = {}
    # labeljson['functional_module'] = [func_ind]
    # labeljson['scene_type'] = func_name
    # labeljson['rode_type'] = "城市普通道路"
    # labeljson['rode_section'] = "路段"
    labeljson['场景名称'] = func_ind
    labeljson['法规类型'] = 'anting'
    labeljson['标准类型'] = func_name
    labeljson['xodr'] = 'antingnewtown_1031_2.xodr'
    labeljson['osgb'] = 'anting_new_town.opt.osgb'
    labeljson['max_time'] = max_time
    with open(os.path.join(output_path, os.path.basename(output_path) + '.json'), 'w', encoding='utf-8') as f:
        json.dump(labeljson, f, indent=4, ensure_ascii=False)


def getLabel(output_path, func_ind, func_name):
    '''
    生成label.json文件
    '''
    labeljson = {}
    labeljson['functional_module'] = [func_ind]
    labeljson['scene_type'] = func_name
    labeljson['rode_type'] = "城市普通道路"
    labeljson['rode_section'] = "路段"
    with open(os.path.join(output_path, os.path.basename(output_path) + '.json'), 'w', encoding='utf-8') as f:
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
                        rad = math.atan(w) - 0.5 * math.pi
                    else:
                        rad = math.atan(w) + 0.5 * math.pi
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
    new_pd['ego_e'] = new_pd['ped_n']
    new_pd['ego_n'] = new_pd['ped_e']
    return new_pd, ped_trail_sketch_df


def create_static_object(road, object_dict):
    for single_object in object_dict:
        for k, v in ObjectType.__members__.items():
            if k == single_object.attrib['type']:
                single_object.attrib['type'] = v
                break

        road_object = Object(
            s=single_object.attrib['s'],
            t=single_object.attrib['t'],
            Type=single_object.attrib['type'],
            dynamic=Dynamic.no,
            id=single_object.attrib['id'],
            name=single_object.attrib['name'],
            zOffset=single_object.attrib['zOffset'],
            validLength=single_object.attrib['validLength'],
            orientation=Orientation.none,
            length=single_object.attrib['length'],
            width=single_object.attrib['width'],
            height=single_object.attrib['height'],
            pitch=single_object.attrib['pitch'],
            roll=single_object.attrib['roll']
        )

        # 判断此object是否是重复的元素
        repeat = single_object.find('repeat')
        if repeat is not None:
            road.add_object_roadside(road_object_prototype=road_object, repeatDistance=0, side=RoadSide.left,
                                     tOffset=1.75)
            road.add_object_roadside(road_object_prototype=road_object, repeatDistance=0, side=RoadSide.right,
                                     tOffset=-1.755)
        else:
            road.add_object(road_object)
    return road


def change_CDATA(filepath):
    '行人场景特例，对xosc文件内的特殊字符做转换'
    f = open(filepath, "r", encoding="UTF-8")
    txt = f.readline()
    all_line = []
    # txt是否为空可以作为判断文件是否到了末尾
    while txt:
        txt = txt.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&quot;", '"').replace(
            "&apos;", "'")
        all_line.append(txt)
        # 读取文件的下一行
        txt = f.readline()
    f.close()
    f1 = open(filepath, 'w', encoding="UTF-8")
    for line in all_line:
        f1.write(line)
    f1.close()


def path_changer(xosc_path, xodr_path, osgb_path):
    """
    provided by Dongpeng Ding
    :param xosc_path:
    :param xodr_path:
    :param osgb_path:
    :return:
    """
    tree = ET.parse(xosc_path)
    treeRoot = tree.getroot()

    # for OpenScenario v0.9, v1.0
    for RoadNetwork in treeRoot.findall('RoadNetwork'):

        for Logics in RoadNetwork.findall('LogicFile'):
            Logics.attrib['filepath'] = xodr_path
        for SceneGraph in RoadNetwork.findall('SceneGraphFile'):
            SceneGraph.attrib['filepath'] = osgb_path

        for Logics in RoadNetwork.findall('Logics'):
            Logics.attrib['filepath'] = xodr_path
        for SceneGraph in RoadNetwork.findall('SceneGraph'):
            SceneGraph.attrib['filepath'] = osgb_path

    # for VTD xml
    for Layout in treeRoot.findall('Layout'):
        Layout.attrib['File'] = xodr_path
        Layout.attrib['Database'] = osgb_path

    tree.write(xosc_path, xml_declaration=True)


def readXML(xoscPath):
    xodrFileName = ""
    osgbFileName = ""

    tree = ET.parse(xoscPath)
    treeRoot = tree.getroot()

    for RoadNetwork in treeRoot.findall('RoadNetwork'):

        for Logics in RoadNetwork.findall('LogicFile'):
            xodrFileName = Logics.attrib['filepath']
        for SceneGraph in RoadNetwork.findall('SceneGraphFile'):
            osgbFileName = SceneGraph.attrib['filepath']

        for Logics in RoadNetwork.findall('Logics'):
            xodrFileName = Logics.attrib['filepath']
        for SceneGraph in RoadNetwork.findall('SceneGraph'):
            osgbFileName = SceneGraph.attrib['filepath']

    return xodrFileName[xodrFileName.rindex("/") + 1:], osgbFileName[osgbFileName.rindex("/") + 1:]


def formatThree(rootDirectory, xodr_path, osgb_path):
    """
    xodr and osgb file path are fixed
    :return:
    """
    for root, dirs, files in os.walk(rootDirectory):
        for file in files:
            if ".xosc" == file[-5:]:
                xodrFilePath = Path(xodr_path).as_posix()
                osgbFilePath = Path(osgb_path).as_posix()
                path_changer(root + "/" + file, xodrFilePath, osgbFilePath)
                print("Change success: " + root + "/" + file)


def formatTwo(rootDirectory):
    """
    data format:
    simulation
        file.xosc
        file.xodr
        file.osgb
    :return:
    """
    for root, dirs, files in os.walk(rootDirectory):
        for file in files:
            if ".xosc" == file[-5:]:

                xodrFilePath = ""
                osgbFilePath = ""

                for odrFile in os.listdir(root):
                    if ".xodr" == odrFile[-5:]:
                        xodrFilePath = root + "/" + odrFile
                        break

                for osgbFile in os.listdir(root):
                    if ".osgb" == osgbFile[-5:]:
                        osgbFilePath = root + "/" + osgbFile
                        break

                path_changer(root + "/" + file, xodrFilePath, osgbFilePath)
                print("Change success: " + root + "/" + file)


def formatOne(rootDirectory):
    """
    data format:
        openx
            xosc
                file.xosc
            xodr
                file.xodr
            osgb
                file.osgb
    :return:
    """
    for root, dirs, files in os.walk(rootDirectory):
        for file in files:
            if "xosc" == file[-4:]:

                xodrFilePath = ""
                osgbFilePath = ""

                for odrFile in os.listdir(root[:-4] + "xodr"):
                    if "xodr" == odrFile[-4:]:
                        xodrFilePath = root[:-4] + "xodr/" + odrFile
                        break

                for osgbFile in os.listdir(root[:-4] + "osgb"):
                    if "osgb" == osgbFile[-4:]:
                        osgbFilePath = root[:-4] + "osgb/" + osgbFile
                        break

                path_changer(root + "/" + file, xodrFilePath, osgbFilePath)
                print("Change success: " + root + "/" + file)


def chongQingFormat(rootDirectory):
    """
    supporting file format: chong qing folder format
    :return:
    """

    counter = 1

    for root, dirs, files in os.walk(rootDirectory):
        for file in files:
            if "xosc" == file[-4:]:
                if "ver1.0.xosc" == file[-11:]:

                    xodrFileName, osgbFileName = readXML(root + "/" + file)

                    xodrFilePath = "/Xodrs/" + xodrFileName
                    osgbFilePath = "/Databases/" + osgbFileName

                    path_changer(root + "/" + file, xodrFilePath, osgbFilePath)
                    print(counter, "Change success: " + root + "/" + file)
                else:
                    xodrFileName, osgbFileName = readXML(root + "/" + file)

                    xodrFilePath = "/Xodrs/" + xodrFileName
                    osgbFilePath = "/Databases/" + osgbFileName

                    path_changer(root + "/" + file, xodrFilePath, osgbFilePath)
                    print(counter, "Change success: " + root + "/" + file)
                counter += 1


def upload_xosc(minio_client, bucket_name, bucket_path, file_path):
    """
    泛化后将xosc文件上传到minio
    :param minio_client: 已初始化的minioclient
    :param bucket_name: 储存桶名
    :param bucket_path: 在储存桶种的路径
    :param file_path: 本地文件路径
    :return: 上传文件的结果
    """
    result = minio_client.fput_object(bucket_name, bucket_path, file_path)
    return result


def get_plt(ego_trail, obs_trail_list=None):
    """
    测试用,绘制轨迹的路线
    :param aspect:
    :param obs_trail_list: 如果有目标车 目标车的轨迹dataframe_list
    :param ego_trail: 轨迹的dataframe
    :return:
    """
    t = ego_trail
    ax = plt.gca()
    plt.figure()
    plt.xlabel("E")  #
    plt.ylabel("N")  # Y

    x_major_locator = MultipleLocator(1)
    y_major_locator = MultipleLocator(1)
    ax.xaxis.set_major_locator(x_major_locator)
    ax.yaxis.set_major_locator(y_major_locator)

    X = np.array(t.ego_e.values.tolist())
    Y = np.array(t.ego_n.values.tolist())
    plt.plot(X, Y)  # 绘制曲线图
    if obs_trail_list:
        for obs_trail in obs_trail_list:
            X = np.array(obs_trail.ego_e.values.tolist())
            Y = np.array(obs_trail.ego_n.values.tolist())
        plt.plot(X, Y)  # 绘制曲线图
    plt.axis('auto')
    plt.xlim(-7, 7)
    plt.show()


def get_entity_properties(object_type_list):
    object_model = list()
    for index, object_type in enumerate(object_type_list):
        object_type = int(object_type)
        if object_type == ObjectType.vehicle.value:
            name = 'Audi_A3_2009_red'
            if index == 0:
                name = 'Audi_A3_2009_black'
            vehicle_type = xosc.VehicleCategory.car
            bounding_box = xosc.BoundingBox(width=1.776, length=4.3, height=1.423, x_center=1.317, y_center=0,
                                            z_center=0.8)
            front_axle = xosc.Axle(maxsteer=27.5, wheeldia=0.641, track_width=1.456, xpos=1.317, zpos=0.8)
            rear_axle = xosc.Axle(maxsteer=0, wheeldia=0.641, track_width=1.456, xpos=1.317, zpos=0.8)
            max_speed = 210
            max_acceleration = 7
            max_deceleration = 9.5
            car = xosc.Vehicle(name=name, vehicle_type=vehicle_type, boundingbox=bounding_box,
                               frontaxle=front_axle, rearaxle=rear_axle, max_speed=max_speed,
                               max_acceleration=max_acceleration, max_deceleration=max_deceleration)
            car.add_property(name='controller', value='external')
            object_model.append(car)
        elif object_type == ObjectType.bus.value:
            name = 'MB_Citaro_2007_yellow'
            if index == 0:
                name = 'MB_Citaro_2007_red'
            vehicle_type = xosc.VehicleCategory.bus
            bounding_box = xosc.BoundingBox(width=2.56, length=11.957, height=3.14, x_center=2.5525, y_center=0,
                                            z_center=1.6)
            front_axle = xosc.Axle(maxsteer=27.5, wheeldia=1, track_width=2.07, xpos=3.5525, zpos=1.6)
            rear_axle = xosc.Axle(maxsteer=0, wheeldia=1, track_width=2.07, xpos=2.5525, zpos=1.6)
            max_speed = 109.8
            max_acceleration = 3
            max_deceleration = 9.5
            bus = xosc.Vehicle(name=name, vehicle_type=vehicle_type, boundingbox=bounding_box,
                               frontaxle=front_axle, rearaxle=rear_axle, max_speed=max_speed,
                               max_acceleration=max_acceleration, max_deceleration=max_deceleration)
            object_model.append(bus)
        elif object_type == ObjectType.truck.value:
            name = 'MANTGS_11_Green'
            if index == 0:
                name = 'MANTGS_11_LightBlue'
            vehicle_type = xosc.VehicleCategory.truck
            bounding_box = xosc.BoundingBox(width=2.8, length=8.744, height=3.78, x_center=2.028, y_center=0,
                                            z_center=1.8)
            front_axle = xosc.Axle(maxsteer=27.5, wheeldia=1.1, track_width=2.32, xpos=2.025, zpos=1.8)
            rear_axle = xosc.Axle(maxsteer=0, wheeldia=1.1, track_width=2.321, xpos=2.028, zpos=1.8)
            max_speed = 95.04
            max_acceleration = 3
            max_deceleration = 9.5
            truck = xosc.Vehicle(name=name, vehicle_type=vehicle_type, boundingbox=bounding_box,
                                 frontaxle=front_axle, rearaxle=rear_axle, max_speed=max_speed,
                                 max_acceleration=max_acceleration, max_deceleration=max_deceleration)
            object_model.append(truck)
        elif object_type == ObjectType.special_vehicle.value:
            name = 'VW_PassatVariant_2011_Police_green'
            if index == 0:
                name = 'VW_PassatVariant_2011_Police_blue'
            vehicle_type = xosc.VehicleCategory.car
            bounding_box = xosc.BoundingBox(width=1.798, length=4.749, height=1.468, x_center=1.2645, y_center=0,
                                            z_center=0.9)
            front_axle = xosc.Axle(maxsteer=27.5, wheeldia=1.1, track_width=1.473, xpos=1.2645, zpos=0.9)
            rear_axle = xosc.Axle(maxsteer=0, wheeldia=1.1, track_width=1.473, xpos=1.2645, zpos=0.9)
            max_speed = 212.4
            max_acceleration = 7
            max_deceleration = 9.5
            police_car = xosc.Vehicle(name=name, vehicle_type=vehicle_type, boundingbox=bounding_box,
                                      frontaxle=front_axle, rearaxle=rear_axle, max_speed=max_speed,
                                      max_acceleration=max_acceleration, max_deceleration=max_deceleration)
            object_model.append(police_car)
        elif object_type == ObjectType.motorcycle.value:
            name = 'Kawasaki_ZX-9R_white'
            if index == 0:
                name = 'Kawasaki_ZX-9R_green'
            vehicle_type = xosc.VehicleCategory.motorbike
            bounding_box = xosc.BoundingBox(width=0.85, length=2.076, height=1.928, x_center=0.618, y_center=0,
                                            z_center=0.9)
            front_axle = xosc.Axle(maxsteer=28.65, wheeldia=1.1, track_width=1.473, xpos=0.618, zpos=0.6)
            rear_axle = xosc.Axle(maxsteer=0, wheeldia=1.1, track_width=1.473, xpos=0.618, zpos=0.6)
            max_speed = 45
            max_acceleration = 7
            max_deceleration = 10
            moto = xosc.Vehicle(name=name, vehicle_type=vehicle_type, boundingbox=bounding_box,
                                frontaxle=front_axle, rearaxle=rear_axle, max_speed=max_speed,
                                max_acceleration=max_acceleration, max_deceleration=max_deceleration)
            object_model.append(moto)
        elif object_type == ObjectType.bicycle.value:
            # 暂时没有自行车模型 用摩托车代替
            name = 'Kawasaki_ZX-9R_white'
            if index == 0:
                name = 'Kawasaki_ZX-9R_green'
            vehicle_type = xosc.VehicleCategory.motorbike
            bounding_box = xosc.BoundingBox(width=0.85, length=2.076, height=1.928, x_center=0.618, y_center=0,
                                            z_center=0.9)
            front_axle = xosc.Axle(maxsteer=28.65, wheeldia=1.1, track_width=1.473, xpos=0.618, zpos=0.6)
            rear_axle = xosc.Axle(maxsteer=0, wheeldia=1.1, track_width=1.473, xpos=0.618, zpos=0.6)
            max_speed = 45
            max_acceleration = 7
            max_deceleration = 10
            bicycle = xosc.Vehicle(name=name, vehicle_type=vehicle_type, boundingbox=bounding_box,
                                   frontaxle=front_axle, rearaxle=rear_axle, max_speed=max_speed,
                                   max_acceleration=max_acceleration, max_deceleration=max_deceleration)
            object_model.append(bicycle)
        elif object_type == ObjectType.pedestrian.value:
            bounding_box = xosc.BoundingBox(width=0.7, length=0.6, height=1.8, x_center=0, y_center=0, z_center=0)
            male_ped = xosc.Pedestrian(name='Christian', model='male_adult', mass=70,
                                       category=xosc.PedestrianCategory.pedestrian, boundingbox=bounding_box)
            object_model.append(male_ped)

    return object_model
