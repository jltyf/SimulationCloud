# @Author  : 张璐
# @Time    : 2022/02/21
# @Function: LKA1-2

def get_report(scenario, script_id):
    dis_deviation = (scenario.scenario_data['lane_center_offset'].abs()).max()
    acceleration_max = (scenario.scenario_data['lateral_acceleration'].abs()).max()
    init_velocity = scenario.get_velocity(scenario.scenario_data.index.tolist()[0])
    v_max = scenario.get_max_velocity()
    v_min = scenario.get_min_velocity()

    # 目前输入数据中没有车道线宽度，暂时设为定值
    road_width = 3.75
    distance = dis_deviation - road_width * 0.5 + 1

    if acceleration_max <= 2.3 and distance < 0 and (
            init_velocity - init_velocity * 0.2 <= v_min <= init_velocity + init_velocity * 0.2) and (
            init_velocity - init_velocity * 0.2 <= v_max <= init_velocity + init_velocity * 0.2):
        score = 100
        evaluate_item = '弯道居中行驶时自车最大横向加速度不大于2.3m/s²，且自车未驶离本车道，得100分'
    elif acceleration_max > 2.3 and distance < 0 and (
            init_velocity - init_velocity * 0.2 <= v_min <= init_velocity + init_velocity * 0.2) and (
            init_velocity - init_velocity * 0.2 <= v_max <= init_velocity + init_velocity * 0.2):
        score = 60
        evaluate_item = '弯道居中行驶时自车最大横向加速度大于2.3m/s²，且自车未驶离本车道，得60分'
    elif distance > 0 or v_min < init_velocity - init_velocity * 0.2 or v_max > init_velocity + init_velocity * 0.2:
        score = 0
        evaluate_item = '弯道居中行驶时自车驶离本车道，得分0'

    score_description = '1) 自车最大横向加速度≤2.3m/s²，且自车未驶离本车道，得分100；\n' \
                        '2) 自车最大横向加速度>2.3m/s²，且自车未驶离本车道，得分60；\n' \
                        '3) 自车驶离本车道，得分0 。'

    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }
