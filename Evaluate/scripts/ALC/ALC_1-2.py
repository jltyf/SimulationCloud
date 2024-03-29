# @Author  : 张璐
# @Time    : 2022/03/09
# @Function : ALC_1-2
# @Scenario: 有干扰车变道
# @Usage   : 评分细则4.2.1、评分细则4.2.2
# @Update  : 2022/08/24

def get_report(scenario, script_id):
    last_stage = scenario.scenario_data.iloc[-5:-1]
    lane_center_offset = (last_stage['lane_center_offset'].abs()).max()
    change_line_flag = scenario.scenario_data['lane_id'].max() - scenario.scenario_data['lane_id'].min()
    if change_line_flag == 0 and lane_center_offset <= 0.2:
        score = 100
        evaluate_item = '得分 100，在相邻车道有干扰车辆时选择继续在自车道行驶。'
    else:
        score = 0
        evaluate_item = '得分 0，相邻车道有干扰车辆时继续变道，安全性差。'

    score_description = '1)得分 100，在相邻车道有干扰车辆时选择继续在自车道行驶;\n' \
                        '2)得分 0，相邻车道有干扰车辆时继续变道，安全性差。'

    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }
