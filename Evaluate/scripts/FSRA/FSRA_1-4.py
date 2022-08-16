# @Author  : 张璐
# @Time    : 2022/08/05
# @Function: FSRA_1-4
# @Scenario: 目标车辆识别与跟车加速
import pandas as pd


def get_report(scenario, script_id):
    scenario.scenario_data = scenario.scenario_data.tail(-143)  # 读取三秒后自车数据
    scenario.obj_scenario_data = scenario.obj_scenario_data.tail(-143)  # 读取三秒后目标车数据
    acc_mean = scenario.scenario_data['longitudinal_acceleration'].mean()
    acc_obj = scenario.get_obj_acc(scenario.obj_scenario_data.index.tolist()[0])

    distance_max = scenario.obj_scenario_data['object_rel_pos_y'].abs().max()
    ID = int(scenario.obj_scenario_data.loc[abs(scenario.obj_scenario_data['object_rel_pos_y']) == distance_max, 'object_ID'])
    scenario.obj_nei_scenario_data = scenario.obj_scenario_data[(scenario.obj_scenario_data['object_ID'] == ID)]
    distance_lon_nei = scenario.obj_nei_scenario_data['object_rel_pos_x']
    distance_lon_nei = pd.DataFrame(distance_lon_nei).iloc[-1]

    if acc_mean >= acc_obj and distance_lon_nei < 0:
        score = 100
        evaluate_item = '自车跟随目标车辆加速行驶，并超过相邻车道的前车，即该系统可以准确识别目标车辆，得100分'
    else:
        score = 0
        evaluate_item = f'该系统不能识别正确的目标车辆或功能异常，得分0'

    score_description = '1) 自车跟随目标车辆加速行驶，并超过相邻车道的前车，即该系统可以准确识别目标车辆，得100分；\n' \
                        '2) 其他情况，即该系统不能识别正确的目标车辆或功能异常，得分0。'
    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }