# @Author  : 张璐
# @Time    : 2022/08/23
# @Function: FSRA_2-1-1
# @Scenario: 前车从左车道切入
# @Usage   : 评分细则4.2.1
# @Update  : 2022/08/29


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

        if (max_dec <= acceleration < 0) and (max_lon_acc_roc <= max_dec_roc):
            return True
        else:
            return False
    elif ego_v < 18:
        if (-5 <= acceleration < 0) and max_lon_acc_roc <= 5:
            return True
        else:
            return False
    else:
        if (-3.5 <= acceleration < 0) and max_lon_acc_roc <= 2.5:
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

    # 判断目标车ID
    obj_data = scenario.obj_scenario_data[
        (scenario.obj_scenario_data['object_rel_pos_y'] < 5) & (scenario.obj_scenario_data['object_rel_pos_y'] > 0) & (
                    scenario.obj_scenario_data['object_rel_pos_x'] > 0)]    # 横向距离，左为正
    min = obj_data['object_rel_pos_x'].min()
    min_ID = obj_data.loc[obj_data['object_rel_pos_x'] == min, 'object_ID']
    if len(min_ID) == 1:
        ID = int(min_ID)
    else:
        ID = np.array(min_ID)[0]
    obj_data = obj_data[(obj_data['object_ID'] == ID)]
    obj_start_v = scenario.get_velocity(obj_data.index.tolist()[0], ID)

    scenario.scenario_data = scenario.scenario_data.loc[15:]  # 读取15秒（稳定跟车）后自车数据
    distance = (scenario.scenario_data['object_closest_dist'].iloc[0] / scenario.get_velocity(
        scenario.scenario_data.index[0]))*3.6  # 车头时距
    collision_status_list = scenario.scenario_data['collision_status'].values.tolist()

    end_v = scenario.get_velocity(scenario.scenario_data.index.tolist()[-1])

    v_diff = abs(obj_start_v - end_v)

    standard_1 = '自车行驶速度≤18km/h时，最大加速度值≤4m/s²、最大减速度值≤5m/s2、最大减速度变化率≤5m/s³；自车行驶速度≧72km/h时，' \
                 '最大加速度值≤2m/s²、最大减速度值≤3.5m/s2、最大减速度变化率≤2.5m/s³；自车行驶速度在18km/h至72km/h区间时，' \
                 '最大加速度值为 2-4m/s2之间插值、最大减速度值为3.5-5m/s2之间插值、最大减速度变化率为2.5-5m/s³之间插值'

    if CollisionStatus.collision.value not in collision_status_list and (1 < distance < 2.2) and v_diff < 2:
        if condition_flag:
            score = 100
            evaluate_item = f'自车减速后稳定跟随目标车辆行驶，且稳定跟车时距为1-2.2s，且减速过程中满足条件“{standard_1}”，即该FSRA系统在有前车切入时，能从定速巡航模式自动变换为跟车模式，且有较好的舒适性，得分100'
        elif not condition_flag:
            score = 60
            evaluate_item = f'自车减速后稳定跟随目标车辆行驶，且稳定跟车时距不在1-2.2s之间，但减速过程中不满足条件“{standard_1}”，即该FSRA系统在有前车切入时，能从定速巡航模式自动变换为跟车模式，但舒适性较差，得分60'
    else:
        score = 0
        evaluate_item = '其他情况，即该FSRA系统在有前车切入时功能异常，得0分'

    score_description = '1) 自车减速后稳定跟随目标车辆行驶，且稳定跟车时距为1-2.2s，且减速过程中满足条件“{standard_1}”，即该FSRA系统在有前车切入时，能从定速巡航模式自动变换为跟车模式，且有较好的舒适性，得分100；\n' \
                        '2) 自车减速后稳定跟随目标车辆行驶，且稳定跟车时距不在1-2.2s之间，但减速过程中不满足条件“{standard_1}”，即该FSRA系统在有前车切入时，能从定速巡航模式自动变换为跟车模式，但舒适性较差，得分60；\n' \
                        '3) 其他情况，即该FSRA系统在有前车切入时功能异常，得0分。'

    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }
