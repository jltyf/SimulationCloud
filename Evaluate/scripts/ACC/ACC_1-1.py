# @Author  : 张璐lalala
# @Time    : 2022/02/22
# @Function: ACC_1-1
# @Scenario: 前方无车定速巡航
# @Usage   : 第二届算法比赛任务十场景一
# @Update  : 2022/08/24

def get_report(scenario, script_id):
    # stable_trail = scenario.scenario_data.tail(50)
    init_velocity = scenario.get_velocity(scenario.scenario_data.index.tolist()[0])
    scenario.scenario_data = scenario.scenario_data.tail(50)
    v_max = scenario.get_max_velocity()
    v_min = scenario.get_min_velocity()
    velocity_diff = abs(v_max - v_min)

    set_velocities_list = [30, 60, 80, 100, 120]

    for set_velocity in set_velocities_list:
        if init_velocity == set_velocity:
            v_max_diff = abs(v_max - set_velocity)
            v_min_diff = abs(v_min - set_velocity)
            v_diff = max(v_max_diff, v_min_diff)

    if v_diff <= 1:
        score = 100
        evaluate_item = '速度稳定后实车车速与巡航速度的差异不大于1km/h，得分100'
    elif 1 < v_diff <= 3:
        score = 60
        evaluate_item = '速度稳定后实车车速与巡航速度的差异大于1km/h，不大于3km/h，得分60'
    elif velocity_diff > 5 or v_diff > 3:
        # 目前稳定速度的阈值未定，暂时设为定值
        score = 0
        evaluate_item = '速度不能保持稳定，或者速度稳定后实车车速与巡航速度的差异大于3km/h，得分0'

    score_description = '1) 速度稳定后实车车速与巡航速度的差异不大于1km/h，得分100；\n' \
                        '2) 速度稳定后实车车速与巡航速度的差异大于1km/h，不大于3km/h，得分60；\n' \
                        '3) 速度不能保持稳定，或者速度稳定后实车车速与巡航速度的差异大于3km/h，得分0。'
    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }
