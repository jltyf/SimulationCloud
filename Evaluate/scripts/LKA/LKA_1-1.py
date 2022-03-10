# @Author  : 张璐
# @Time    : 2022/02/21
# @Function: LKA1-1

def get_report(scenario, script_id):
    dis_deviation = (scenario.scenario_data['lane_center_offset'].abs()).max()
    acceleration_max = scenario.scenario_data['lateral_acceleration'].max()

    # 目前输入数据中没有车道线宽度，暂时设为定值
    road_width = 3.75
    distance = dis_deviation - road_width * 0.5

    if dis_deviation <= 0.2 and acceleration_max <= 2.3:
        score = 100
        evaluate_item = '直道居中行驶时自车中心线与车道中心线偏移距离不大于0.2m，且最大横向加速度不大于2.3m/s²,得100分'
    elif 0.2 < dis_deviation <= 0.4 and acceleration_max <= 2.3:
        score = 70
        evaluate_item = '直道居中行驶时自车中心线与车道中心线偏移距离大于0.2m且不大于0.4m，最大横向加速度不大于2.3m/s²,得70分'
    elif dis_deviation > 0.4 and acceleration_max <= 2.3 and distance < 0:
        score = 50
        evaluate_item = '直道居中行驶时自车中心线与车道中心线偏移距离大于0.4m，最大横向加速度不大于2.3m/s²,且自车未驶离本车道，得分50'
    elif distance > 0 or acceleration_max > 2.3:
        score = 0
        evaluate_item = '直道居中行驶时车辆驶出本车道，或最大横向加速度不大于2.3m/s²,且自车未驶离本车道，得分0'

    score_description = '1) 自车中心线与车道中心线偏移距离不大于0.2m，且自车最大横向加速度≤2.3m/s²，得分100；\n' \
                        '2) 自车中心线与车道中心线偏移距离大于0.2m且不大于0.4m，且自车最大横向加速度≤2.3m/s²，得分70；\n' \
                        '3) 直道居中行驶时自车中心线与车道中心线偏移距离大于0.4m，自车最大横向加速度≤2.3m/s²，且自车未驶离本车道，得分50；\n' \
                        '4) 车辆驶出本车道，或自车最大横向加速度>2.3m/s²得分0。'

    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }
