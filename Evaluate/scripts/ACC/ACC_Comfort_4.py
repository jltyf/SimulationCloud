# @Author           : 汤宇飞
# @Time             : 2022/10/19
# @Function         : ACC_Comfort_4(横摆角速度均方根)
# @Scenario         : 前车慢行/前方无车定速巡航
# @Usage            : 所有国赛ACC场景
# @UpdateTime       : /
# @UpdateUser       : /
import math


def get_report(scenario, script_id):
    try:
        start_index = 0
        end_index = 30
        score = 100
        for i in range(1, len(scenario.scenario_data) // 50 + 1):
            cut_df = scenario.scenario_data.iloc[start_index:end_index:]
            yawrate_rms = math.sqrt(
                sum([x ** 2 for x in cut_df['yawrate'].values.tolist()]) / len(scenario.scenario_data))
            if yawrate_rms < 0.015:
                score = 100
                evaluate_item = '横摆角速度均方根的舒适性指标中,横摆角速度均方根在舒适的范围内,得100分'
            elif 0.015 < yawrate_rms < 0.08:
                tmp_score = scenario.get_interpolation(yawrate_rms, (0.08, 0), (0.015, 100))
                score = min(score, tmp_score)
                evaluate_item = f'横摆角速度均方根的舒适性指标中,横摆角速度均方根稍大,得{score}分'
            else:
                score = 0
                evaluate_item = '横摆角速度均方根的舒适性指标中,横摆角速度均方根大于舒适行驶的范围,得0分'
                break
            start_index = end_index
            end_index = start_index + 50
            if end_index >= len(scenario.scenario_data):
                end_index = len(scenario.scenario_data)
    except:
        score = -1
        evaluate_item = '评分功能发生错误,选择的评分脚本无法对此场景进行评价'
    finally:
        score = round(score, 2)
        score_description = '1)  当车辆横摆角速度均方根小0.025时被认为舒适,得100分;\n' \
                            '2)  当车辆速横摆角速度均方根大于0.04时被认为极不舒适，得0分;\n' \
                            '3)  当车辆横摆角速度均方根在0.02和0.04之间时被认为不舒适，按照0分到100分进行插值。'
        return {
            'unit_scene_ID': script_id,
            'unit_scene_score': score,
            'evaluate_item': evaluate_item,
            'score_description': score_description
        }

