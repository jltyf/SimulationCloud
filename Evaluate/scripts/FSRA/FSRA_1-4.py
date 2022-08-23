# @Author  : 张璐
# @Time    : 2022/08/18
# @Function: FSRA_1-4
# @Scenario: 目标车辆识别与跟车加速
import numpy as np
import pandas as pd


def get_report(scenario, script_id):
    scenarios_data = scenario.scenario_data.loc[3:]  # 读取三秒后自车数据
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
    obj_data = obj_data.loc[5:]  # 读取5秒后目标车数据
    obj_rel_vel_lon = obj_data['object_rel_vel_x'].iloc[0]  # 目标车相对纵向速度

    # 相邻车道前车数据
    distance_max = scenario.obj_scenario_data['object_rel_pos_y'].abs().max()
    ID = int(scenario.obj_scenario_data.loc[
                 abs(scenario.obj_scenario_data['object_rel_pos_y']) == distance_max, 'object_ID'])
    scenario.obj_nei_scenario_data = scenario.obj_scenario_data[(scenario.obj_scenario_data['object_ID'] == ID)]
    distance_lon_nei = scenario.obj_nei_scenario_data['object_rel_pos_x']
    distance_lon_nei = pd.DataFrame(distance_lon_nei).iloc[-1]

    if obj_rel_vel_lon < 2 and distance_lon_nei < 0:  # 5秒后目标车的相对纵向速度小于2，并且与相邻车道前车的距离为负
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
