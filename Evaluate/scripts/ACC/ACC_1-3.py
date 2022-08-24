# @Author  : 张璐
# @Time    : 2022/03/01
# @Function: ACC_1-3
# @Scenario: 跟随前车停车与起步
# @Usage   : 第二届算法比赛任务十场景三
# @Update  : 2022/08/24

from enumerations import CollisionStatus


def get_report(scenario, script_id):
    timestamp_list = scenario.scenario_data.index.tolist()
    stop_timestamp_list = []
    for timestamp in timestamp_list:
        if scenario.get_velocity(timestamp) < 0.5:
            stop_timestamp_list.append(timestamp)
    stop_timestamp = int(min(stop_timestamp_list))
    start_timestamp = int(max(stop_timestamp_list))
    first_stage = scenario.scenario_data.iloc[0:stop_timestamp]
    third_stage = scenario.scenario_data.iloc[start_timestamp:]
    max_acc = first_stage['longitudinal_acceleration'].max()
    max_dec = third_stage['longitudinal_acceleration'].min()

    collision_status_list = scenario.scenario_data['collision_status'].values.tolist()
    end_v = scenario.get_velocity(scenario.scenario_data.index.tolist()[-1])

    # 碰撞用枚举类表示
    if CollisionStatus.collision.value in collision_status_list or len(collision_status_list) == 0 or end_v < 0.5:
        score = 0
        evaluate_item = '未跟车停车，发生碰撞，或跟车起步失败，得分0'
    elif len(collision_status_list) > 0 and max_dec >= -4 and max_acc <= 3:
        score = 100
        evaluate_item = '能够跟随前车停止且跟停减速度最大值≤4m/s²，能够成功跟车起步且加速过程中加速度最大值≤3m/s²，得分100'
    elif len(collision_status_list) > 0 and (max_dec < -4 or max_acc > 3):
        score = 60
        evaluate_item = '能够跟随前车停止并成功跟车起步，但参数不满足"减速过程中停减速度最大值≤4m/s²,加速过程中加速度最大值≤3m/s²"要求，得分60'

    score_description = '1) 能够跟随前车停止且跟停减速度最大值≤4m/s²，能够成功跟车起步且加速过程中加速度最大值≤3m/s²，得分100；\n' \
                        '2) 能够跟随前车停止并成功跟车起步，但参数不满足上述①中要求，得分60；\n' \
                        '3) 未跟车停车，发生碰撞，或跟车起步失败，得分0。'
    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }
