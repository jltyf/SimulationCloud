# @Author  : 张璐
# @Time    : 2022/02/17
# @Function: AEB3-3
def get_report(scenario, script_id):
    collision_status_list = scenario.scenario_data['collision_status'].values.tolist()
    # 碰撞
    if 1 in collision_status_list:
        score = 0
    # 没碰撞
    else:
        score = 100
    score_description = '1) 未发生碰撞，得分 100；\n2) 发生碰撞，得分 0。'
    if score == 100:
        evaluate_item = '前方摩托车与自车同向行驶时未发生碰撞,得100分'
    else:
        evaluate_item = '前方摩托车与自车同向行驶时发生碰撞,得0分'

    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }
