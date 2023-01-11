# @Author  : 汤宇飞
# @Time    : 2023/01/04
# @Function: GSACC_3
# @Scenario: 全速自适应巡航基础场景
# @Usage   : 全速自适应巡航基础功能
# @Update  : 2023/01/04

from enumerations import CollisionStatus


def get_report(scenario, script_id):
    try:
        collision_status_list = scenario.scenario_data['collision_status'].values.tolist()
        if CollisionStatus.collision.value not in collision_status_list:
            ACC_data = scenario.scenario_data.iloc[-50:]
            stable_road_id = ACC_data['road_id'].mean()
            stable_lane_id = ACC_data['lane_id'].mean()
            acc_stable_velocity = scenario.get_average_velocity(ACC_data.index.values.tolist())
            if isinstance(acc_stable_velocity, str) and '错误' in acc_stable_velocity:
                error_msg = scenario.__error_message(scenario.get_average_velocity, False).split('错误:')[1]
                raise RuntimeError
            stable_df = ACC_data.copy()
            stable_df['velocity'] = (ACC_data['lateral_velocity'] ** 2 + ACC_data[
                'longitudinal_velocity'] ** 2) ** 0.5
            if stable_df['velocity'].var() <= 10 and stable_road_id == ACC_data.iloc[-1][
                'road_id'] and stable_lane_id == ACC_data.iloc[-1]['lane_id']:
                tmp_df = scenario.obj_scenario_data[
                    scenario.obj_scenario_data['frame_ID'].isin(stable_df['frame_ID'].values.tolist()) & (
                            scenario.obj_scenario_data['road_id'] == stable_road_id) & (
                            scenario.obj_scenario_data['lane_id'] == stable_lane_id) & (
                            scenario.obj_scenario_data['object_direction'] <= 5 | (
                            scenario.obj_scenario_data['object_direction'] >= 355))]
                obj_data = tmp_df.copy()
                obj_data['distance'] = (obj_data['object_rel_pos_y'] ** 2 + obj_data[
                    'object_rel_pos_x'] ** 2) ** 0.5
                distance = float('inf')
                set_velocity = float('inf')
                for obj_id, obj_df in obj_data.groupby('object_ID'):
                    obj_distance = obj_df['distance'].mean()
                    if obj_distance < distance:
                        set_velocity = scenario.get_average_velocity(obj_df.index.values.tolist(), obj_id)
                        distance = obj_distance
                v_diff_acc = abs(acc_stable_velocity - set_velocity)
                head_way = distance / (acc_stable_velocity / 3.6)  # km/h和m/s换算
                if 1 < head_way < 8:
                    if v_diff_acc <= 5:
                        score = 100
                        evaluate_item = '车辆以目标车速稳定跟车且车头时距处于安全范围内(1~5s)，得分100'
                    elif 5 < v_diff_acc < 15:
                        score = round(scenario.get_interpolation(v_diff_acc, (5, 50), (15, 0)), 3)
                        if isinstance(score, str) and '错误' in score:
                            error_msg = score.split('错误:')[1]
                            raise RuntimeError
                        evaluate_item = f'能够完成跟车动作,但跟车时候车速和前车车速在5~10km/h之间，得分{score}。'
                    else:
                        score = 0
                        evaluate_item = '能够完成跟车动作,但和前车车速差距过大，得分0。'
                else:
                    score = 0
                    evaluate_item = '车头时距不在1～8s的范围内，跟车距离不符合要求，得分0。'
            else:
                score = 0
                evaluate_item = '车辆未能稳定跟车，得分0。'
        else:
            score = 0
            evaluate_item = '车辆发生碰撞，得分0。'

    except RuntimeError:
        score = -1
        evaluate_item = error_msg
    except:
        score = -1
        evaluate_item = '评分功能发生错误,选择的评分脚本无法对此场景进行评价'
    score_description = '1) 稳定跟车时，跟车车间时距范围在1-8s，主车与目标车车速差不超过5km/h，得分100;\n' \
                        '2) 稳定跟车时，跟车车间时距范围在1-8s，主车与目标车车速差在5-10km/h范围内，得分按照插值处理；\n' \
                        '3) 其他情况，得分0。'
    return {
        'unit_scene_ID': script_id,
        'unit_scene_score': score,
        'evaluate_item': evaluate_item,
        'score_description': score_description
    }
