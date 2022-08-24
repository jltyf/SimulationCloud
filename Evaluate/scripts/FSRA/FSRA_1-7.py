# @Author  : 张璐
# @Time    : 2022/08/22
# @Function: FSRA_1-7
# @Scenario: 弯道跟车行驶
# @Usage   : 评分细则4.1.8
# @Update  : 2022/08/24


from enumerations import CollisionStatus


def get_report(scenario, script_id):
    dis_deviation = (scenario.scenario_data['lane_center_offset'].abs()).max()
    road_width = 3.75
    distance = dis_deviation - road_width * 0.5 + 1

    acceleration_max = (scenario.scenario_data['lateral_acceleration'].abs()).max()
    init_velocity = scenario.get_velocity(scenario.scenario_data.index.tolist()[0])
    v_max = scenario.get_max_velocity()
    v_min = scenario.get_min_velocity()
    collision_status_list = scenario.scenario_data['collision_status'].values.tolist()

    if CollisionStatus.collision.value not in collision_status_list and distance <= 0 and (
            init_velocity - init_velocity * 0.5 <= v_min <= init_velocity + init_velocity * 0.5) and (
            init_velocity - init_velocity * 0.5 <= v_max <= init_velocity + init_velocity * 0.5):
        if acceleration_max <= 2.3:
            score = 100
            evaluate_item = '自车跟随前车在弯道内稳定行驶，没有偏移出车道和碰撞，且横向加速度不大于2.3m/s2时,即在弯道内自车FSRA跟车功能正常，且具备较好的舒适性，得100分'
        else:
            score = 60
            evaluate_item = '自车跟随前车在弯道内行驶，没有偏移出车道和碰撞，但横向加速度大于2.3m/s2时,即在弯道内自车FSRA跟车功能正常，但舒适性较差，得60分'
    else:
        score = 0
        evaluate_item = '其他情况，即在弯道内自车FSRA跟车功能异常，得0分'

    score_description = '1) 自车跟随前车在弯道内稳定行驶，没有偏移出车道和碰撞，且横向加速度不大于2.3m/s2时,即在弯道内自车FSRA跟车功能正常，且具备较好的舒适性，得100分；\n' \
                        '2) 自车跟随前车在弯道内行驶，没有偏移出车道和碰撞，但横向加速度大于2.3m/s2时,即在弯道内自车FSRA跟车功能正常，但舒适性较差，得60分；\n' \
                        '3) 其他情况，即在弯道内自车FSRA跟车功能异常，得0分。'


    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }