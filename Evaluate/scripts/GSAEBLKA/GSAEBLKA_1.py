# @Author  : 李玲星
# @Time    : 2022/09/07
# @Function: GSAEBLKA_1
# @Scenario: 前车静止、前车减速+直道居中行驶、弯道居中行驶
# @Usage   : 自动紧急制动+车道保持组合测试一：
# @Update  : 2022/09/07

import numpy as np
import pandas as pd
from enumerations import CollisionStatus


def get_v_interpolation(v_diff):
    p1 = [2, 100]
    p2 = [5, 0]
    k = (p1[1] - p2[1]) / (p1[0] - p2[0])
    b = (p1[0] * p2[1] - p1[1] * p2[0]) / (p1[0] - p2[0])
    v_interpolation = k * v_diff + b
    return v_interpolation


def get_report(scenario, script_id):
    # AEB:
    v_max = scenario.get_max_velocity()
    v_min = scenario.get_min_velocity()
    set_velocity = 80
    v_max_diff = abs(v_max - set_velocity)
    v_min_diff = abs(v_min - set_velocity)
    v_diff = max(v_max_diff, v_min_diff)

    dis_deviation = (scenario.scenario_data['lane_center_offset'].abs()).max()
    road_width = 3.75
    distance = dis_deviation - road_width * 0.5 + 1

    if distance <= 0 and v_diff <= 2:
        LKA_score = 50
        evaluate_item_1 = f'车辆未驶出本车道，维持设定车速且车速变动量不超过2km/h，车道保持得分50。'
    elif distance <= 0 and 2 < v_diff <= 5:
        LKA_score = get_v_interpolation(v_diff) * 0.5
        evaluate_item_1 = f'车辆未驶出本车道，维持设定车速且车速变动量在2-5km/h范围内，车道保持得分按照插值进行计算。'
    elif distance > 0 or v_diff > 5:
        LKA_score = 0
        evaluate_item_1 = f'车辆未驶出本车道，维持设定车速且车速变动量在5km/h范围外，或车辆驶出本车道，车道保持得分0。'

    # score_description = '1) 车辆未驶出本车道，维持设定车速且车速变动量不超过2km/h，得分50；\n' \
    # '2) 车辆未驶出本车道，维持设定车速且车速变动量在2-5km/h范围内，得分按照插值进行计算；\n' \
    # '3) 车辆未驶出本车道，维持设定车速且车速变动量在5km/h范围外，或车辆驶出本车道，得分0。'

    # LKA:
    # 判断目标车ID
    obj_data = scenario.obj_scenario_data[
        (scenario.obj_scenario_data['object_rel_pos_y'] < 1) & (scenario.obj_scenario_data['object_rel_pos_y'] > -1) & (
                scenario.obj_scenario_data['object_rel_pos_x'] > 0)]
    min = obj_data['object_rel_pos_x'].min()
    min_ID = obj_data.loc[obj_data['object_rel_pos_x'] == min, 'object_ID']
    if len(min_ID) == 1:
        ID = int(min_ID)
    else:
        ID = np.array(min_ID)[0]
    obj_data = obj_data[(obj_data['object_ID'] == ID)]

    distance = obj_data['object_rel_pos_x']
    distance_final = pd.DataFrame(distance).iloc[-1].values

    collision_status_list = scenario.scenario_data['collision_status'].values.tolist()
    # 碰撞
    if CollisionStatus.collision.value in collision_status_list:
        AEB_score = 0
        evaluate_item_2 = '前方车辆静止时发生碰撞，自动紧急制动得0分。'
    # 没碰撞
    elif distance_final <= 5 and CollisionStatus.collision.value not in collision_status_list:
        AEB_score = 25
        evaluate_item_2 = '前方车辆静止时，自车制动后与前车车距小于5米，自动紧急制动得25分。'
    elif distance_final > 5 and CollisionStatus.collision.value not in collision_status_list:
        AEB_score = 50
        evaluate_item_2 = '前方车辆静止时，自车制动后与前车车距不小于5米，自动紧急制动得50分。'

    if LKA_score == 0 or AEB_score == 0:
        score = 0
        score_description = '车辆未驶出本车道，维持设定车速且车速变动量在5km/h范围外，或车辆驶出本车道，车道保持得分0;\n' \
                            '或前方车辆静止时发生碰撞，自动紧急制动得0分;自动紧急制动和车道保持有一项得0分，则总分为0。'
    else:
        score = LKA_score + AEB_score
        score_description = '车道保持:1) 车辆未驶出本车道，维持设定车速且车速变动量不超过2km/h，得分50；\n' \
                            '2) 车辆未驶出本车道，维持设定车速且车速变动量在2-5km/h范围内，得分按照插值进行计算；\n' \
                            '3) 车辆未驶出本车道，维持设定车速且车速变动量在5km/h范围外，或车辆驶出本车道，得分0。' \
                            '自动紧急制动:1) 前方车辆静止时，自车制动后与前车车距不小于5米，得50分；\n2) 前方车辆静止时，自车制动后与前车车距小于5米，得25分；\n' \
                            '3)前方车辆静止时发生碰撞，得0分。' \
                            '总分为自动紧急制动评分与车道保持评分之和'
    evaluate_item = evaluate_item_1 + evaluate_item_2

    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description,
    }
