# @Author  : 张璐
# @Time    : 2022/08/19
# @Function: FSRA_1-5-2
# @Scenario: 跟车时前车减速行驶
# @Usage   : 评分细则4.1.6
# @Update  : 2022/08/24

def get_dec_interpolation(ego_v):
    p1 = [18, -5]
    p2 = [72, -3.5]
    k = (p1[1] - p2[1]) / (p1[0] - p2[0])
    b = (p1[0] * p2[1] - p1[1] * p2[0]) / (p1[0] - p2[0])
    dec_interpolation = k * ego_v + b
    return dec_interpolation


def get_dec_roc_interpolation(ego_v):
    p1 = [18, 5]
    p2 = [72, 2.5]
    k = (p1[1] - p2[1]) / (p1[0] - p2[0])
    b = (p1[0] * p2[1] - p1[1] * p2[0]) / (p1[0] - p2[0])
    dec_roc_interpolation = k * ego_v + b
    return dec_roc_interpolation


def conditions(scenario, index):
    # 实际值
    ego_v = scenario.get_velocity(index)
    acceleration = scenario.scenario_data.loc[index]['longitudinal_acceleration']
    max_lon_acc_roc = scenario.get_lon_acc_roc(index)
    if 18 < ego_v < 72:
        # 标准值
        max_dec = get_dec_interpolation(ego_v)
        max_dec_roc = get_dec_roc_interpolation(index)

        if (max_dec <= acceleration) and (max_lon_acc_roc <= max_dec_roc):
            return True
        else:
            return False
    elif ego_v < 18:
        if (-5 <= acceleration < 0) and max_lon_acc_roc <= 5:
            return True
        else:
            return False
    else:
        if (-3.5 <= acceleration < 0) and max_lon_acc_roc <= 2.5:
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

    obj_data = scenario.obj_scenario_data.loc[3:]  # 读取3秒后目标车数据
    obj_rel_vel_lon = obj_data['object_rel_vel_x'].iloc[0]  # 目标车相对纵向速度
    scenario.scenario_data = scenario.scenario_data.loc[5:]  # 读取5秒（稳定跟车）后自车数据
    distance = scenario.scenario_data['object_closest_dist'] / scenario.get_velocity(scenario.scenario_data.index[0])  # 车头时距

    standard_1 = '自车行驶速度≤18km/h时，最大加速度值≤4m/s²、最大减速度值≤5m/s2、最大减速度变化率≤5m/s³；自车行驶速度≧72km/h时，' \
                 '最大加速度值≤2m/s²、最大减速度值≤3.5m/s2、最大减速度变化率≤2.5m/s³；自车行驶速度在18km/h至72km/h区间时，' \
                 '最大加速度值为 2-4m/s2之间插值、最大减速度值为3.5-5m/s2之间插值、最大减速度变化率为2.5-5m/s³之间插值'

    if obj_rel_vel_lon <= 2 and (1 <= distance <= 2.2):
        if condition_flag:
            score = 100
            evaluate_item = f'自车跟随前车减速行驶，且前车车速稳定后，跟车车间时距范围在1-2.2s，且满足条件“{standard_1}”，得分100'
        elif not condition_flag:
            score = 60
            evaluate_item = f'自车跟随前车减速行驶，且前车车速稳定后，跟车车间时距范围在1-2.2s，但不满足条件“{standard_1}”，得分60'
    else:
        score = 0
        evaluate_item = f'自车未跟随前车减速或跟随前车减速但车间时距不满足要求，得分0'

    score_description = '1) 车辆在全速域内，应满足：自车行驶速度≤18km/h时，最大加速度值≤4m/s²、最大减速度值≤5m/s2、最大减速度变化率≤5m/s³；' \
                        '自车行驶速度≧72km/h时，最大加速度值≤2m/s²、最大减速度值≤3.5m/s2、最大减速度变化率≤2.5m/s³；' \
                        '自车行驶速度在18km/h至72km/h区间时，最大加速度值为 2-4m/s2之间插值、最大减速度值为3.5-5m/s2之间插值、最大减速度变化率为2.5-5m/s³之间插值；\n' \
                        '2) 自车跟随前车减速行驶，且前车车速稳定后，跟车车间时距范围在1-2.2s，且满足条件“{standard_1}”，得分100；\n' \
                        '3) 自车跟随前车减速行驶，且前车车速稳定后，跟车车间时距范围在1-2.2s，但不满足条件“{standard_1}”，得分60；\n' \
                        '4) 自车未跟随前车减速或跟随前车减速但车间时距不满足要求，得分0。'

    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }
