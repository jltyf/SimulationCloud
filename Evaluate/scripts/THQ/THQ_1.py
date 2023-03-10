# @Author           : 汤宇飞
# @Time             : 2023/03/10
# @Function         : THQ_1
# @Scenario         : 太和桥园区自适应巡航
# @Usage            : 太和桥园区
# @UpdateTime       : 2022/03/10
# @UpdateUser       : 汤宇飞
from enumerations import CollisionStatus


def get_report(scenario, script_id):
    try:
        collision_status_list = scenario.scenario_data['collision_status'].values.tolist()

        # 碰撞
        if CollisionStatus.collision.value in collision_status_list:
            score = 0
            evaluate_item = '行驶过程中发生碰撞,得0分'
            raise RuntimeError
        start_index = 0
        end_index = 300
        for i in range(1, len(scenario.scenario_data) // 300 + 1):
            cut_df = scenario.scenario_data.iloc[start_index:end_index:]
            start_velocity = scenario.get_velocity(cut_df.index.values.tolist()[0])
            end_velocity = scenario.get_velocity(cut_df.index.values.tolist()[-1])
            if isinstance(start_velocity, str) and '错误' in start_velocity:
                evaluate_item = start_velocity.split('错误:')[1]
                raise RuntimeError
            elif isinstance(end_velocity, str) and '错误' in end_velocity:
                evaluate_item = end_velocity.split('错误:')[1]
                raise RuntimeError
            elif abs(start_velocity) <= 0.5 and abs(start_velocity) <= 0.5:
                score = 0
                evaluate_item = '车辆长时间停车，得0分'
                raise RuntimeError
            start_index = end_index
            end_index = start_index + 300
            if end_index >= len(scenario.scenario_data):
                end_index = len(scenario.scenario_data)

        # 驶出道路判断
        if True:
            score = 100
            evaluate_item = '车辆顺利到达终点，得100分'

    except RuntimeError:
        pass
    except:
        score = -1
        evaluate_item = '评分功能发生错误,选择的评分脚本无法对此场景进行评价'
    finally:
        score = round(score, 2)
        score_description = '1)  若车辆发生碰撞，测试未通过得0分;\n' \
                            '2)  若车辆长时间停车，测试未通过得0分;\n' \
                            '3)  若车辆驶出道路，测试未通过得0分;\n' \
                            '4)  车辆未发生异常且顺利到达终点，测试通过得100分。'
        return {
            'unit_scene_ID': script_id,
            'unit_scene_score': score,
            'evaluate_item': evaluate_item,
            'score_description': score_description
        }
