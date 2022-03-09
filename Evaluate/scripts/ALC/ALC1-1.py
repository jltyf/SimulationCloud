# @Author  : 张晋崇
# @Time    : 2022/02/28
#@Function : ALC1-1

def get_report(scenario, script_id):
    lat_acc_max=(scenario.scenario_data['lateral_acceleration'].abs()).max()
    lon_acc_max=(scenario.scenario_data['longitudinal_acceleration'].abs()).max()
    lat_acc_roc_max=scenario.get_lat_acc_roc()
    time_change_lane=scenario.scenario_date['pass']#缺少的变量

    # 定义车辆变道成功

    # 得分说明
    if time_change_lane <= 6 and (scenario.lat_acc_roc_max() <= 2 and lon_acc_max <=3 and lat_acc_roc_max <= 5):
        score = 100
        evaluate_item = '得分 100，该算法中 ALC 功能正常，且变道过程中具备良好的舒适性'
    elif time_change_lane <= 6 and not (scenario.lat_acc_roc_max <= 2 and lon_acc_max <=3 and lat_acc_roc_max <= 5):
        score = 60
        evaluate_item = '得分 60，该算法中 ALC 功能正常，但变道过程中舒适较差'
    elif time_change_lane > 6:
        score = 0
        evaluate_item = '得分 0，该算法 ALC 功能异常,无干扰车变道失败'

    score_description ='1)得分 100，该算法中 ALC 功能正常，且变道过程中具备良好的舒适性;\n'\
                        '2)得分 60，该算法中 ALC 功能正常，但变道过程中舒适较差;\n'\
                        '3)得分 0，该算法 ALC 功能异常,无干扰车变道失败'

    return {
        'unit_scene_ID' : script_id,
        'unit_scene_score' : score,
        'evaluate_item' : evaluate_item,
        'score_description' : score_description
    }
