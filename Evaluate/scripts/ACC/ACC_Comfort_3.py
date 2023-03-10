# @Author           : 汤宇飞
# @Time             : 2022/10/19
# @Function         : ACC_Comfort_3(速度方差)
# @Scenario         : 前车慢行/前方无车定速巡航
# @Usage            : 所有国赛ACC场景
# @UpdateTime       : /
# @UpdateUser       : /

def get_report(scenario, script_id):
    try:
        start_index = 0
        end_index = 30
        score = 100
        scenario.scenario_data['velocity'] = (scenario.scenario_data['lateral_velocity'] ** 2 + scenario.scenario_data[
            'longitudinal_velocity'] ** 2) ** 0.5
        for i in range(1, len(scenario.scenario_data) // 50 + 1):
            cut_df = scenario.scenario_data.iloc[start_index:end_index:]
            velocity_var = cut_df['velocity'].var()
            if velocity_var < 8:
                score = 100
                evaluate_item = '速度方差的舒适性指标中,速度的方差在舒适的范围内,得100分'
            elif 8 < velocity_var < 15:
                tmp_score = scenario.get_interpolation(velocity_var, (15, 0), (8, 100))
                score = min(tmp_score, score)
                evaluate_item = f'速度方差的舒适性指标中,速度的方差稍大,得{score}分'
            else:
                score = 0
                evaluate_item = '速度方差的舒适性指标中,速度的方差大于舒适行驶的范围,得0分'
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
        score_description = '1)  当车辆速度方差小于5时被认为舒适,得100分;\n' \
                            '2)  当车辆速度方差大于10时被认为极不舒适，得0分;\n' \
                            '3)  当车辆速度方差在5和10之间时被认为不舒适，按照0分到100分进行插值。'
        return {
            'unit_scene_ID': script_id,
            'unit_scene_score': score,
            'evaluate_item': evaluate_item,
            'score_description': score_description
        }
