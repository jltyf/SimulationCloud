# @Author           : 张璐
# @Time             : 2022/08/16
# @Function         : GSAES_1
# @Scenario         : 前车静止、前车慢行
# @Usage            : 全国职业院校技能大赛变道避撞测试一、二
# @UpdateTime       : 2023/02/21
# @UpdateUser       : 汤宇飞

from enumerations import CollisionStatus


def get_report(scenario, script_id):
    try:
        collision_status_list = scenario.scenario_data['collision_status'].values.tolist()

        avg_v = scenario.get_velocity_variation(1, 2)

        if CollisionStatus.collision.value in collision_status_list:
            score = 0
            evaluate_item = '前方车辆慢行时发生碰撞,得0分'
        elif avg_v == 0:
            score = 0
            evaluate_item = '未启动算法'
        else:
            score = 100
            evaluate_item = '成功启动算法且未发生碰撞,得100分'

    except:
        score = -1
        evaluate_item = '评分功能发生错误,选择的评分脚本无法对此场景进行评价'

    finally:
        score_description = '1) 成功启动算法且未发生碰撞，得分 100；\n2) 未启动算法或发生碰撞，得分 0。'

        return {
            'unit_scene_ID': script_id,
            'unit_scene_score': score,
            'evaluate_item': evaluate_item,
            'score_description': score_description
        }
