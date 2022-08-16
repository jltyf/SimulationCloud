# @Author  : 张璐
# @Time    : 2022/08/15
# @Function: GSAEB_1
import pandas as pd

from enumerations import CollisionStatus


def get_report(scenario, script_id):
    # 判断目标车ID
    scenario.obj_data = scenario.obj_scenario_data[(scenario.obj_scenario_data['object_rel_pos_y'] < 1)|(scenario.obj_scenario_data['object_rel_pos_y'] > -1)]
    min = scenario.obj_data['object_rel_pos_x'].min()
    ID = int(scenario.obj_data.loc[abs(scenario.obj_data['object_rel_pos_x']) == min, 'object_ID'])

    scenario.obj_data = scenario.obj_data[(scenario.obj_data['object_ID'] == ID)]
    distance = scenario.obj_data['object_rel_pos_x']
    ditance_final = pd.DataFrame(distance).iloc[-1].values

    collision_status_list = scenario.scenario_data['collision_status'].values.tolist()
    # 碰撞
    if CollisionStatus.collision.value in collision_status_list:
        score = 0
        evaluate_item = '前方车辆静止时发生碰撞，得0分'
    # 没碰撞
    elif ditance_final <= 5 and CollisionStatus.collision.value not in collision_status_list:
        score = 50
        evaluate_item = '前方车辆静止时，自车制动后与前车车距小于5米，得50分'
    elif ditance_final > 5 and CollisionStatus.collision.value not in collision_status_list:
        score = 100
        evaluate_item = '前方车辆静止时，自车制动后与前车车距不小于5米，得100分'

    score_description = '1) 前方车辆静止时，自车制动后与前车车距不小于5米，得100分；\n2) 前方车辆静止时，自车制动后与前车车距小于5米，得50分；\n3)前方车辆静止时发生碰撞，得0分。'

    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }
