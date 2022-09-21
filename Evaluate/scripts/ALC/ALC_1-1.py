# @Author  : 张晋崇
# @Time    : 2022/02/28
# @Function : ALC_1-1
# @Scenario: 无干扰车变道
# @Usage   : 评分细则4.1.1、评分细则4.1.2
# @Update  : 2022/08/24

def get_report(scenario, script_id):
    evaluate_flag = True
    try:
        lat_acc_max = (scenario.scenario_data['lateral_acceleration'].abs()).max()
        lon_acc_max = (scenario.scenario_data['longitudinal_acceleration'].abs()).max()
        lat_acc_roc_max = (scenario.scenario_data['lateral_accelarate_roc'].abs()).max()
        change_lane_time = scenario.get_change_lane_time()
        if isinstance(change_lane_time, str) and '错误' in change_lane_time:
            score = -1
            evaluate_flag = False
            evaluate_item = scenario.__error_message(scenario.get_change_lane_time, False).split('错误:')[1]
        else:
            change_line_flag = scenario.scenario_data['lane_id'].max() - scenario.scenario_data['lane_id'].min()
    except:
        score = -1
        evaluate_flag = False
        evaluate_item = '评分功能发生错误,选择的评分脚本无法对此场景进行评价'
    # 得分说明
    if evaluate_flag:
        if change_lane_time <= 6 and change_line_flag:
            if lon_acc_max <= 2 and lat_acc_max <= 3 and lat_acc_roc_max <= 5:
                score = 100
                evaluate_item = '得分 100，该算法中 ALC 功能正常，且变道过程中具备良好的舒适性'
            elif lon_acc_max > 2 or lat_acc_max > 3 or lat_acc_roc_max > 5:
                score = 60
                evaluate_item = '得分 60，该算法中 ALC 功能正常，但变道过程中舒适较差'
        else:
            score = 0
            evaluate_item = '得分 0，该算法 ALC 功能异常,无干扰车变道失败'

    score_description = '1)得分 100，该算法中 ALC 功能正常，且变道过程中具备良好的舒适性;\n' \
                        '2)得分 60，该算法中 ALC 功能正常，但变道过程中舒适较差;\n' \
                        '3)得分 0，该算法 ALC 功能异常,无干扰车变道失败。'

    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }
