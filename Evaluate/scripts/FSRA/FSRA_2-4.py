# @Author  : 张璐
# @Time    : 2022/08/23
# @Function: FSRA_2-4
# @Scenario: 前车切出后前方无车辆

import numpy as np
from enumerations import CollisionStatus


def get_dec_interpolation(ego_v):
    p1 = [18, -5]
    p2 = [72, -3.5]
    k = (p1[1] - p2[1]) / (p1[0] - p2[0])
    b = (p1[0] * p2[1] - p1[1] * p2[0]) / (p1[0] - p2[0])
    dec_interpolation = k * ego_v + b
    return dec_interpolation


def get_dec_roc_interpolation(ego_v):
    p1 = [18, 5]
    p2 = [72, 2.5]
    k = (p1[1] - p2[1]) / (p1[0] - p2[0])
    b = (p1[0] * p2[1] - p1[1] * p2[0]) / (p1[0] - p2[0])
    dec_roc_interpolation = k * ego_v + b
    return dec_roc_interpolation


def get_acc_interpolation(ego_v):
    p1 = [18, 4]
    p2 = [72, 2]
    k = (p1[1] - p2[1]) / (p1[0] - p2[0])
    b = (p1[0] * p2[1] - p1[1] * p2[0]) / (p1[0] - p2[0])
    acc_interpolation = k * ego_v + b
    return acc_interpolation


def conditions(scenario, index):
    # 实际值
    ego_v = scenario.get_velocity(index)
    acceleration = scenario.scenario_data.loc[index]['longitudinal_acceleration']
    max_lon_acc_roc = scenario.get_lon_acc_roc(index)
    # max_acc = first_stage['longitudinal_acceleration'].max()
    # max_dec = third_stage['longitudinal_acceleration'].min()
    if 18 < ego_v < 72:
        # 标准值
        max_dec = get_dec_interpolation(ego_v)
        max_dec_roc = get_dec_roc_interpolation(index)
        max_acc = get_acc_interpolation(ego_v)

        if (max_dec <= acceleration < max_acc) and (max_lon_acc_roc <= max_dec_roc):
            return True
        else:
            return False
    elif ego_v < 18:
        if (-5 <= acceleration < 4) and max_lon_acc_roc <= 5:
            return True
        else:
            return False
    else:
        if (-3.5 <= acceleration < 2) and max_lon_acc_roc <= 2.5:
            return True
        else:
            return False


def get_report(scenario, script_id):
    condition_flag = True
    index_list = scenario.scenario_data.index.values.tolist()
    for index in index_list:
        condition_flag = conditions(scenario, index)
        if not condition_flag:
            break

    start_v = scenario.get_velocity(scenario.scenario_data.index.tolist()[0])
    scenario.scenario_data = scenario.scenario_data.loc[15:]  # 读取15秒(稳定行驶）后自车数据
    end_v = scenario.get_velocity(scenario.scenario_data.index.tolist()[-1])
    v_diff = abs(end_v - start_v)

    standard_1 = '自车行驶速度≤18km/h时，最大加速度值≤4m/s²、最大减速度值≤5m/s2、最大减速度变化率≤5m/s³；自车行驶速度≧72km/h时，' \
                 '最大加速度值≤2m/s²、最大减速度值≤3.5m/s2、最大减速度变化率≤2.5m/s³；自车行驶速度在18km/h至72km/h区间时，' \
                 '最大加速度值为 2-4m/s2之间插值、最大减速度值为3.5-5m/s2之间插值、最大减速度变化率为2.5-5m/s³之间插值'

    if v_diff <= 2 and condition_flag:
        score = 100
        evaluate_item = f'自车按照当前速度行驶，且减速过程中满足条件“{standard_1}”，即前车切出后，自车FSRA功能正常，且具备较好的舒适性，得分100'
    else:
        score = 0
        evaluate_item = f'其他情况，即前车切出后，自车FSRA功能异常，得分0'

    score_description = '1) 自车按照当前速度行驶，且减速过程中满足条件“{standard_1}”，即前车切出后，自车FSRA功能正常，且具备较好的舒适性，得分100；\n' \
                        '2) 其他情况，即前车切出后，自车FSRA功能异常，得分0。'

    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }