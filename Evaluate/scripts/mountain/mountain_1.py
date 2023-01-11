# @Author           : 汤宇飞
# @Time             : 2022/11/25
# @Function         : mountain_1
# @Scenario         : 矿区场景避撞
# @Usage            : 矿区场景1
# @UpdateTime       : 2022/11/25
# @UpdateUser       : 汤宇飞

from enumerations import CollisionStatus


def get_report(scenario, script_id):
    try:
        collision_status_list = scenario.scenario_data['collision_status'].values.tolist()

        # 碰撞
        if CollisionStatus.collision.value in collision_status_list:
            score = 0
            evaluate_item = '矿车行进时发生碰撞,得0分'
        # 没碰撞
        else:
            score = 100
            evaluate_item = '矿车行进时未发生碰撞,得100分'
    except:
        score = -1
        evaluate_item = '评分功能发生错误,选择的评分脚本无法对此场景进行评价'
    finally:
        score_description = '1) 未发生碰撞，得分 100；\n2) 发生碰撞，得分 0。'
        return {
            'unit_scene_ID': script_id,
            'unit_scene_score': score,
            'evaluate_item': evaluate_item,
            'score_description': score_description,
        }
