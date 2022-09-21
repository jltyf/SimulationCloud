# @Author  : 李玲星
# @Time    : 2022/09/13
# @Function: GSACCLKA_1
# @Scenario: 前车慢行+直道居中行驶、弯道居中行驶
# @Usage   : 自适应巡航+车道保持组合测试一、二、三、四
# @Update  : 2022/09/15

import numpy as np

def get_report(scenario, script_id):
    evaluate_flag = True
    try:
        # lka:
        acc_start_ID = scenario.scenario_data[scenario.scenario_data['longitudinal_acceleration'] < -0.1].index[0]
        lka_start_ID = scenario.scenario_data[scenario.scenario_data['longitudinal_velocity'] > 0].index[0]
        v_max = max(scenario.scenario_data.loc[lka_start_ID:acc_start_ID, 'longitudinal_velocity'])
        v_min = min(scenario.scenario_data.loc[lka_start_ID:acc_start_ID, 'longitudinal_velocity'])
        set_velocity = 80
        v_max_diff = abs(v_max - set_velocity)
        v_min_diff = abs(v_min - set_velocity)
        v_diff_lka = max(v_max_diff, v_min_diff)
        dis_deviation = (scenario.scenario_data['lane_center_offset'].abs()).max()
        distance_LKA = dis_deviation - scenario.lane_width * 0.5 + 1

        # 判断目标车ID
        obj_data = scenario.obj_scenario_data[
            (scenario.obj_scenario_data['object_rel_pos_y'] < 1) & (
                        scenario.obj_scenario_data['object_rel_pos_y'] > -1) & (
                    scenario.obj_scenario_data['object_rel_pos_x'] > 0)]
        min_ID = obj_data.loc[obj_data['object_rel_pos_x'] == obj_data['object_rel_pos_x'].min(), 'object_ID']
        ID = np.array(min_ID)[0]
        obj_data = obj_data[(obj_data['object_ID'] == ID)]
        set_velocity = scenario.get_velocity(obj_data.index.tolist()[0], ID)
        scenario.scenario_data = scenario.scenario_data.tail(50)
        v_max = scenario.get_max_velocity()
        v_min = scenario.get_min_velocity()
        v_max_diff = abs(v_max - set_velocity)
        v_min_diff = abs(v_min - set_velocity)
        v_diff_acc = max(v_max_diff, v_min_diff)
        time_distance = (scenario.scenario_data['object_closest_dist'] / scenario.get_velocity(
            scenario.scenario_data.index[0])) * 3.6
        time_distance_min = time_distance.min()
    except:
        score = -1
        evaluate_flag = False
        evaluate_item = '评分功能发生错误,选择的评分脚本无法对此场景进行评价'
    if evaluate_flag:

        if (1 <= time_distance_min <= 3) and v_diff_acc <= 5 and distance_LKA <= 0 and v_diff_lka <= 2:
            score = 100
            evaluate_item = f'车辆未驶出本车道，维持设定车速且车速变动量不超过2km/h，稳定跟车时，跟车车间时距范围在1-3s，主车与目标车车速差不超过5km/h,得分100'
        elif (1 <= time_distance_min <= 3) and v_diff_acc <= 5 and distance_LKA <= 0 and 2 < v_diff_lka <= 5:
            score = scenario.get_v_interpolation_LKA(v_diff_lka) * 0.5 + 50
            evaluate_item = f'车辆未驶出本车道，维持设定车速且车速变动量在2-5km/h范围内，稳定跟车时，跟车车间时距范围在1-3s，主车与目标车车速差不超过5km/h,得分按照插值处理'
        elif (1 <= time_distance_min <= 3) and 5 < v_diff_acc <= 10 and distance_LKA <= 0 and v_diff_lka <= 2:
            score = scenario.get_v_interpolation_ACC(v_diff_acc) * 0.5 + 50
            evaluate_item = f'车辆未驶出本车道，维持设定车速且车速变动量不超过2km/h,稳定跟车时，跟车车间时距范围在1-3s，主车与目标车车速差在5-10km/h范围内，得分按照插值处理'
        elif (1 <= time_distance_min <= 3) and 5 < v_diff_acc <= 10 and distance_LKA <= 0 and 2 < v_diff_lka <= 5:
            score = scenario.get_v_interpolation_LKA(v_diff_lka) * 0.5 + scenario.get_v_interpolation_ACC(v_diff_acc) * 0.5
            evaluate_item = f'车辆未驶出本车道，维持设定车速且车速变动量在2-5km/h范围内,稳定跟车时，跟车车间时距范围在1-3s，主车与目标车车速差在5-10km/h范围内，得分按照插值处理'
        else:
            score = 0
            evaluate_item = f'其他情况，得分0'

    score_description = '1)  车辆未驶出本车道，维持设定车速且车速变动量不超过2km/h，稳定跟车时，跟车车间时距范围在1-3s，主车与目标车车速差不超过5km/h，得分100;\n' \
                        '2)  车辆未驶出本车道，维持设定车速且车速变动量不超过2km/h，稳定跟车时，跟车车间时距范围在1-3s，主车与目标车车速差在5-10km/h范围内，得分按照插值处理；\n' \
                        '3)  车辆未驶出本车道，维持设定车速且车速变动量在2-5km/h范围内，稳定跟车时，跟车车间时距范围在1-3s，主车与目标车车速差不超过5km/h，得分按照插值进行计算；\n' \
                        '4)  车辆未驶出本车道，维持设定车速且车速变动量在2-5km/h范围内，稳定跟车时，跟车车间时距范围在1-3s，主车与目标车车速差在5-10km/h范围内，得分按照插值进行计算；\n' \
                        '5)  其他情况，得分0。'
    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }
