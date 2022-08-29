# @Author  : 张璐
# @Time    : 2022/08/16
# @Function: GSACC_1
# @Scenario: 前方无车定速巡航
# @Usage   : 全国职业院校技能大赛自适应巡航测试一
# @Update  : 2022/08/24

def get_v_interpolation(v_diff):
    p1 = [2, 100]
    p2 = [5, 0]
    k = (p1[1] - p2[1]) / (p1[0] - p2[0])
    b = (p1[0] * p2[1] - p1[1] * p2[0]) / (p1[0] - p2[0])
    v_interpolation = k * v_diff + b
    return v_interpolation


def get_report(scenario, script_id):
    scenario.scenario_data = scenario.scenario_data.tail(50)
    v_max = scenario.get_max_velocity()
    v_min = scenario.get_min_velocity()

    set_velocity = 80

    v_max_diff = abs(v_max - set_velocity)
    v_min_diff = abs(v_min - set_velocity)
    v_diff = max(v_max_diff, v_min_diff)

    if v_diff <= 2:
        score = 100
        evaluate_item = '速度稳定后实车车速与巡航速度的差异不大于2km/h，得分100'
    elif 2 < v_diff <= 5:
        score = get_v_interpolation(v_diff)
        evaluate_item = '速度稳定后实车车速与巡航速度的差异大于2km/h，不大于5km/h，得分按照插值处理'
    elif v_diff > 5:
        score = 0
        evaluate_item = '速度不能保持稳定，或者速度稳定后实车车速与巡航速度的差异大于5km/h，得分0'

    score_description = '1) 速度稳定后实车车速与巡航速度的差异不大于2km/h，得分100；\n' \
                        '2) 速度稳定后实车车速与巡航速度的差异大于2km/h，不大于5km/h，得分按照插值处理；\n' \
                        '3) 速度不能保持稳定，或者速度稳定后实车车速与巡航速度的差异大于5km/h，得分0。'
    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }
