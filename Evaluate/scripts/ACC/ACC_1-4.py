# @Author  : 张璐
# @Time    : 2022/03/02
# @Function: ACC_1-4
# @Scenario: 前车减速行驶
# @Usage   : 第二届算法比赛任务十场景四
# @Update  : 2022/08/24

from enumerations import CollisionStatus


def get_dec_interpolation(ego_v):
    p1 = [18, -5]
    p2 = [72, -3.5]
    k = (p1[1] - p2[1]) / (p1[0] - p2[0])
    b = (p1[0] * p2[1] - p1[1] * p2[0]) / (p1[0] - p2[0])
    dec_interpolation = k * ego_v + b
    return dec_interpolation


def conditions(scenario, index):
    # 实际值
    ego_v = scenario.get_velocity(index)
    acceleration = scenario.scenario_data.loc[index]['longitudinal_acceleration']
    if 18 < ego_v < 72:
        # 标准值
        max_dec = get_dec_interpolation(ego_v)

        if (max_dec <= acceleration):
            return True
        else:
            return False
    elif ego_v < 18:
        if (-5 <= acceleration <= 4):
            return True
        else:
            return False
    else:
        if (-3.5 <= acceleration <= 2):
            return True
        else:
            return False


def get_report(scenario, script_id):
    condition_flag = True
    index_list = scenario.scenario_data.index.values.tolist()
    for index in index_list:
        condition_flag = conditions(scenario, index)
        if not condition_flag:
            break

    collision_status_list = scenario.scenario_data['collision_status'].values.tolist()

    standard_1 = '自车行驶速度≤18km/h时，最大加速度值≤4m/s²、最大减速度值≤5m/s2、最大减速度变化率≤5m/s³；自车行驶速度≧72km/h时，' \
                 '最大加速度值≤2m/s²、最大减速度值≤3.5m/s2、最大减速度变化率≤2.5m/s³；自车行驶速度在18km/h至72km/h区间时，' \
                 '最大加速度值为 2-4m/s2之间插值、最大减速度值为3.5-5m/s2之间插值、最大减速度变化率为2.5-5m/s³之间插值'

    if CollisionStatus.collision.value in collision_status_list:
        score = 0
        evaluate_item = f'前车减速行驶时，发生碰撞，得分0'
    elif condition_flag:
        score = 100
        evaluate_item = f'前车减速行驶时，未发生碰撞，且减速度满足条件“{standard_1}”，得分100'
    elif not condition_flag:
        score = 60
        evaluate_item = f'前车减速行驶时，未发生碰撞，但减速度不满足条件“{standard_1}”，得分60'

    score_description = '1) 车辆在全速域内，应满足：自车行驶速度≤18km/h时，最大加速度值≤4m/s²、最大减速度值≤5m/s2、最大减速度变化率≤5m/s³；' \
                        '自车行驶速度≧72km/h时，最大加速度值≤2m/s²、最大减速度值≤3.5m/s2、最大减速度变化率≤2.5m/s³；' \
                        '自车行驶速度在18km/h至72km/h区间时，最大加速度值为 2-4m/s2之间插值、最大减速度值为3.5-5m/s2之间插值、最大减速度变化率为2.5-5m/s³之间插值；\n' \
                        '2) 前车减速行驶时，发生碰撞，得分0；\n' \
                        '3) 前车减速行驶时，未发生碰撞，且减速度满足条件“{standard_1}”，得分100；\n' \
                        '4) 前车减速行驶时，未发生碰撞，但减速度不满足条件“{standard_1}”，得分60。'
    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }
