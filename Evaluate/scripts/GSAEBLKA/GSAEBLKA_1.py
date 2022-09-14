# @Author  : 李玲星
# @Time    : 2022/09/07
# @Function: GSAEBLKA_1
# @Scenario: 前车静止、前车减速+直道居中行驶、弯道居中行驶
# @Usage   : 自动紧急制动+车道保持组合测试一、二、三、四、五
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
    evaluate_flag = True
    try:
        aeb_start_ID = scenario.scenario_data[scenario.scenario_data['longitudinal_acceleration'] < -0.5].index[0]
    except IndexError:
        score = -1
        evaluate_flag = False
        evaluate_item = 'AEB功能未触发'
    try:
        aeb_start_ID = scenario.scenario_data[scenario.scenario_data['longitudinal_acceleration'] < -0.5].index[0]
        lka_start_ID = scenario.scenario_data[scenario.scenario_data['longitudinal_velocity'] > 0].index[0]
        v_max = max(scenario.scenario_data.loc[lka_start_ID:aeb_start_ID, 'longitudinal_velocity'])
        v_min = min(scenario.scenario_data.loc[lka_start_ID:aeb_start_ID, 'longitudinal_velocity'])
        set_velocity = 80
        v_max_diff = abs(v_max - set_velocity)
        v_min_diff = abs(v_min - set_velocity)
        v_diff = max(v_max_diff, v_min_diff)

        dis_deviation = (scenario.scenario_data['lane_center_offset'].abs()).max()
        distance_LKA = dis_deviation - scenario.lane_width * 0.5 + 1
        # 判断目标车ID
        obj_data = scenario.obj_scenario_data[
        (scenario.obj_scenario_data['object_rel_pos_y'] < 1) & (scenario.obj_scenario_data['object_rel_pos_y'] > -1) & (
                scenario.obj_scenario_data['object_rel_pos_x'] > 0)]
        min_ID = obj_data.loc[obj_data['object_rel_pos_x'] == obj_data['object_rel_pos_x'].min(), 'object_ID']
        ID = np.array(min_ID)[0]
        obj_data = obj_data[(obj_data['object_ID'] == ID)]
        distance_AEB = obj_data['object_rel_pos_x']
        distance_final = pd.DataFrame(distance_AEB).iloc[-1].values
        collision_status_list = scenario.scenario_data['collision_status'].values.tolist()
    except:
        score = -1
        evaluate_flag = False
        evaluate_item = '评分功能发生错误,选择的评分脚本无法对此场景进行评价'

    if evaluate_flag:
        if distance_LKA <= 0 and v_diff <= 2 and distance_final > 5 and CollisionStatus.collision.value not in collision_status_list:
            score = 100
            evaluate_item = f'车辆未驶出本车道，维持设定车速且车速变动量不超过2km/h；前方车辆静止时，自车制动后与前车车距不小于5米，得100分。'
        elif distance_LKA <= 0 and v_diff <= 2 and distance_final <= 5 and CollisionStatus.collision.value not in collision_status_list:
            score = 75
            evaluate_item = '车辆未驶出本车道，维持设定车速且车速变动量不超过2km/h；前方车辆静止时，自车制动后与前车车距小于5米，得75分。'
        elif distance_LKA <= 0 and 2 < v_diff <= 5 and distance_final > 5 and CollisionStatus.collision.value not in collision_status_list:
            score = get_v_interpolation(v_diff) * 0.5 + 50
            evaluate_item = f'车辆未驶出本车道，维持设定车速且车速变动量在2-5km/h范围内，前方车辆静止时，自车制动后与前车车距不小于5米,得{score}分。'
        elif distance_LKA <= 0 and 2 < v_diff <= 5 and distance_final <= 5 and CollisionStatus.collision.value not in collision_status_list:
            score = get_v_interpolation(v_diff) * 0.5 + 25
            evaluate_item = f'车辆未驶出本车道，维持设定车速且车速变动量在2-5km/h范围内，前方车辆静止时，自车制动后与前车车距小于5米,得{score}分。'
        elif distance_LKA > 0 or v_diff > 5 or CollisionStatus.collision.value in collision_status_list:
            score = 0
            evaluate_item = f'车辆未驶出本车道，但未维持设定车速（车速变动量>=5km/h）；或车辆驶出本车道；或前方车辆静止时发生碰撞，得0分。'
    score_description = '1) 车辆未驶出本车道，但未维持设定车速（车速变动量>=5km/h）；或车辆驶出本车道；或前方车辆静止时发生碰撞，得0分；\n' \
                        '2）车辆未驶出本车道，维持设定车速且车速变动量在2-5km/h内;前方车辆静止时，自车与前方车辆未发生碰撞，得分按照插值进行计算;\n' \
                        '3) 车辆未驶出本车道，维持设定车速且车速变动量<=2km/h；前方车辆静止时，自车制动后与前车车距小于5米，得75分；\n' \
                        '4) 车辆未驶出本车道，维持设定车速且车速变动量<=2km/h；前方车辆静止时，自车制动后与前车车距不小于5米，得100分。'
    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description,
    }
