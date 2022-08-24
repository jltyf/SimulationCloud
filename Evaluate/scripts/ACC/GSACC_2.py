# @Author  : 张璐
# @Time    : 2022/08/16
# @Function: GSACC_2
# @Scenario: 前车慢行
# @Usage   : 全国职业院校技能大赛自适应巡航测试二
# @Update  : 2022/08/24

import numpy as np


def get_v_interpolation(v_diff):
    p1 = [5, 100]
    p2 = [10, 0]
    k = (p1[1] - p2[1]) / (p1[0] - p2[0])
    b = (p1[0] * p2[1] - p1[1] * p2[0]) / (p1[0] - p2[0])
    v_interpolation = k * v_diff + b
    return v_interpolation


def get_report(scenario, script_id):
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

    set_velocity = scenario.get_velocity(obj_data.index.tolist()[0], ID)

    scenario.scenario_data = scenario.scenario_data.tail(50)
    v_max = scenario.get_max_velocity()
    v_min = scenario.get_min_velocity()

    v_max_diff = abs(v_max - set_velocity)
    v_min_diff = abs(v_min - set_velocity)
    v_diff = max(v_max_diff, v_min_diff)

    distance = scenario.scenario_data['object_closest_dist'] / scenario.get_velocity(scenario.scenario_data.index[0])
    distance_max = distance.max()

    if (1 <= distance_max <= 2):
        if v_diff <= 5:
            score = 100
            evaluate_item = f'稳定跟车时，跟车车间时距范围在1-2s，主车与目标车车速差不超过5km/h，得分100'
        elif 5 < v_diff <= 10:
            score = get_v_interpolation(v_diff)
            evaluate_item = f'稳定跟车时，跟车车间时距范围在1-2s，主车与目标车车速差在5-10km/h范围内，得分按照插值处理'
    else:
        score = 0
        evaluate_item = f'其他情况，得分0'

    score_description = '1) 稳定跟车时，跟车车间时距范围在1-2s，主车与目标车车速差不超过5km/h，得分100;\n' \
                        '2) 稳定跟车时，跟车车间时距范围在1-2s，主车与目标车车速差在5-10km/h范围内，得分按照插值处理；\n' \
                        '3) 其他情况，得分0。'
    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }
