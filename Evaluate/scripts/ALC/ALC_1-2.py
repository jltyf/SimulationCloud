# @Author  : 张璐
# @Time    : 2022/03/09
# @Function : ALC1-2

def get_report(scenario, script_id):
    last_stage = scenario.scenario_data.iloc[-5:-1]
    lane_center_offset = (last_stage['lane_center_offset'].abs()).max()
    change_line_flag = scenario.scenario_data['frame_ID'].max() - scenario.scenario_data['frame_ID'].min()
    if change_line_flag == 0 and lane_center_offset < 1:
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
