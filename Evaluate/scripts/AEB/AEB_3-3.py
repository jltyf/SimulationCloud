# @Author  : 张璐
# @Time    : 2022/02/17
# @Function: AEB_3-3
# @Scenario: 前方摩托车与自车同向行驶
# @Usage   : 评分细则4.2.2
# @Update  : 2022/08/24

from enumerations import CollisionStatus


def get_report(scenario, script_id):
    collision_status_list = scenario.scenario_data['collision_status'].values.tolist()
    # 碰撞
    if CollisionStatus.collision.value in collision_status_list:
        score = 0
        evaluate_item = '前方摩托车与自车同向行驶时发生碰撞,得0分'
    # 没碰撞
    else:
        score = 100
        evaluate_item = '前方摩托车与自车同向行驶时未发生碰撞,得100分'

    score_description = '1) 未发生碰撞，得分 100；\n2) 发生碰撞，得分 0。'

    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }
