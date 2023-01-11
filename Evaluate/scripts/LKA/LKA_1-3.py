# @Author  : 汤宇飞
# @Time    : 2023/01/04
# @Function: LKA_1-3
# @Scenario: 居中行驶
# @Usage   : 居中行驶场景
# @Update  : 2023/01/04

def get_report(scenario, script_id):
    try:
        start_velocity = scenario.get_average_velocity(scenario.scenario_data.iloc[:5].index.values.tolist())
        if isinstance(start_velocity, str) and '错误' in start_velocity:
            error_msg = start_velocity.split('错误:')[1]
            raise RuntimeError
        first_lane_id = scenario.scenario_data.iloc[0]['lane_id']
        center_offer_max = max(scenario.scenario_data['lane_center_offset'].max(),
                               abs(scenario.scenario_data['lane_center_offset'].min()))
        lane_id_list = list(set(scenario.scenario_data['lane_id'].tolist()))
        if len(lane_id_list) == 1 and lane_id_list[0] == first_lane_id and center_offer_max < 0.8:
            start_index = 0
            end_index = 30
            for i in range(1, len(scenario.scenario_data) // 30 + 1):
                cut_df = scenario.scenario_data.iloc[start_index:end_index:]
                if abs(cut_df['steering_angle'].mean()) < 20 and cut_df['steering_angle'].var() < 200:
                    lka_stable_velocity = scenario.get_velocity(cut_df.index.values.tolist()[-1])
                    if isinstance(lka_stable_velocity, str) and '错误' in lka_stable_velocity:
                        error_msg = lka_stable_velocity.split('错误:')[1]
                        raise RuntimeError
                    v_diff_lka = abs(lka_stable_velocity - start_velocity)
                    if v_diff_lka <= 2:
                        score = 100
                        evaluate_item = '车辆未使出本车道且维持设定车速且车速变动量不超过2km/h'
                    elif 2 < v_diff_lka <= 5:
                        score = round(scenario.get_interpolation(v_diff_lka, (2, 50), (5, 0)), 3)
                        if isinstance(score, str) and '错误' in score:
                            error_msg = scenario.__error_message(scenario.get_interpolation, False).split('错误:')[1]
                            raise RuntimeError
                        evaluate_item = '车辆未使出本车道且维持设定车速且车速变动量在2-5km/h范围内'
                    else:
                        score = 0
                        evaluate_item = '车辆未使出本车道但未能维持设定车速'
                    break
                start_index = end_index
                end_index = start_index + 30
                if end_index >= len(scenario.scenario_data):
                    end_index = len(scenario.scenario_data)
        else:
            score = 0
            evaluate_item = '车辆驶出本车道'

        score_description = '1) 车辆未使出本车道且维持设定车速且车速变动量不超过2km/h，得分100；\n' \
                            f'2) 车辆未使出本车道且维持设定车速且车速变动量在2-5km/h范围内，得{score}分；\n' \
                            '3) 车辆驶离本车道，得分0 。'
    except RuntimeError:
        score = -1
        evaluate_item = error_msg
    except:
        score = -1
        evaluate_item = '评分功能发生错误,选择的评分脚本无法对此场景进行评价'

    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }
