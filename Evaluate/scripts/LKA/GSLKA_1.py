# @Author  : 张璐
# @Time    : 2022/08/16
# @Function: GSLKA_1
# @Scenario: 直道居中行驶、弯道居中行驶
# @Usage   : 全国职业院校技能大赛车道保持辅助测试一、二
# @Update  : 2022/08/24

def get_v_interpolation(v_diff):
    p1 = [2, 100]
    p2 = [5, 0]
    k = (p1[1] - p2[1]) / (p1[0] - p2[0])
    b = (p1[0] * p2[1] - p1[1] * p2[0]) / (p1[0] - p2[0])
    v_interpolation = k * v_diff + b
    return v_interpolation


def get_report(scenario, script_id):
    v_max = scenario.get_max_velocity()
    v_min = scenario.get_min_velocity()

    set_velocity = 80

    v_max_diff = abs(v_max - set_velocity)
    v_min_diff = abs(v_min - set_velocity)
    v_diff = max(v_max_diff, v_min_diff)

    dis_deviation = (scenario.scenario_data['lane_center_offset'].abs()).max()

    road_width = 3.75
    distance = dis_deviation - road_width * 0.5 + 1

    if distance <= 0 and v_diff <= 2:
        score = 100
        evaluate_item = f'车辆未驶出本车道，且车速维持在2km/h范围内，得分100'
    elif distance <= 0 and 2 < v_diff <= 5:
        score = get_v_interpolation(v_diff)
        evaluate_item = f'车辆未驶出本车道，且车速维持在2-5km/h范围内，得分按照插值进行计算'
    elif distance > 0 or v_diff > 5:
        score = 0
        evaluate_item = f'车辆未驶出本车道，且车速维持在5km/h范围外，或车辆驶出本车道，得分0'

    score_description = '1) 车辆未驶出本车道，且车速维持在2km/h范围内，得分100；\n' \
                        '2) 车辆未驶出本车道，且车速维持在2-5km/h范围内，得分按照插值进行计算；\n' \
                        '3) 车辆未驶出本车道，且车速维持在5km/h范围外，或车辆驶出本车道，得分0。'

    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }
