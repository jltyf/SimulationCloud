# @Author           : 李玲星
# @Time             : 2022/09/13
# @Function         : GSACCLKA_1
# @Scenario         : 前车慢行+直道居中行驶、弯道居中行驶
# @Usage            : 自适应巡航+车道保持组合测试一、二、三、四
# @UpdateTime       : 2022/09/22
# @UpdateUser       : 汤宇飞

import numpy as np
from enumerations import CollisionStatus


def get_report(scenario, script_id):
    try:
        start_velocity = scenario.get_average_velocity(scenario.scenario_data.iloc[:5].index.values.tolist())
        if isinstance(start_velocity, str) and '错误' in start_velocity:
            error_msg = scenario.__error_message(scenario.get_average_velocity, False).split('错误:')[1]
            raise RuntimeError
        ACC_flag = True  # temporary
        LKA_flag = True  # temporary
        if LKA_flag:
            first_lane_id = scenario.scenario_data.iloc[0]['lane_id']
            center_offer_max = max(scenario.scenario_data['lane_center_offset'].max(),
                                   abs(scenario.scenario_data['lane_center_offset'].min()))
            lane_id_list = list(set(scenario.scenario_data['lane_id'].tolist()))
            if len(lane_id_list) == 1 and lane_id_list[0] == first_lane_id and center_offer_max < 0.8:
                start_index = 0
                edn_index = 30
                for i in range(1, len(scenario.scenario_data) // 30 + 1):
                    cut_df = scenario.scenario_data.iloc[start_index:edn_index:]
                    if abs(cut_df['steering_angle'].mean()) < 20 and cut_df['steering_angle'].var() < 200:
                        lka_stable_velocity = scenario.get_velocity(cut_df.index.values.tolist()[-1])
                        if isinstance(start_velocity, str) and '错误' in start_velocity:
                            error_msg = scenario.__error_message(scenario.get_velocity, False).split('错误:')[1]
                            raise RuntimeError
                        v_diff_lka = abs(lka_stable_velocity - start_velocity)
                        if v_diff_lka <= 2:
                            score_lka = 50
                            evaluate_item_lka = 'LKA功能：车辆未使出本车道且维持设定车速且车速变动量不超过2km/h'
                        elif 2 < v_diff_lka <= 5:
                            score_lka = round(scenario.get_interpolation(v_diff_lka, (2, 50), (5, 0)), 0)
                            if isinstance(score_lka, str) and '错误' in score_lka:
                                error_msg = scenario.__error_message(scenario.get_interpolation, False).split('错误:')[1]
                                raise RuntimeError
                            evaluate_item_lka = 'LKA功能：车辆未使出本车道且维持设定车速且车速变动量在2-5km/h范围内'
                        else:
                            score_lka = 0
                            evaluate_item_lka = 'LKA功能：车辆未使出本车道但未能维持设定车速'
                        break
                    start_index = edn_index
                    edn_index = start_index + 30
            else:
                score_lka = 0
                evaluate_item_lka = 'LKA功能：车辆驶出本车道'
        else:
            score_lka = 50
            evaluate_item_lka = '场景中未触发LKA功能.'
        if ACC_flag:
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
                    head_way = distance / acc_stable_velocity
                    if 1 < head_way < 3:
                        if v_diff_acc <= 2:
                            score_acc = 50
                            evaluate_item_acc = 'ACC功能：车辆以目标车速稳定跟车且车头时距处于安全范围内(1~3s);'
                        elif 5 < v_diff_acc < 10:
                            score_acc = scenario.get_interpolation(head_way, (5, 50), (10, 0))
                            if isinstance(score_acc, str) and '错误' in score_acc:
                                error_msg = scenario.__error_message(scenario.get_interpolation, False).split('错误:')[1]
                                raise RuntimeError
                            evaluate_item_acc = 'ACC功能：能够完成跟车动作,但跟车时候车速和前车车速在5~10km/h之间;'
                        else:
                            score_acc = 0
                            evaluate_item_acc = 'ACC功能：能够完成跟车动作,但和前车车速差距过大;'
                    else:
                        score_acc = 0
                        evaluate_item_acc = 'ACC功能：车头时距不在1～3s的范围内，跟车距离不符合要求;'
                else:
                    score_acc = 0
                    evaluate_item_acc = 'ACC功能：车辆未能稳定跟车;'
            else:
                score_acc = 0
                evaluate_item_acc = 'ACC功能：车辆发生碰撞;'
        if not ACC_flag and not LKA_flag:
            score = -1
            evaluate_item = '评分功能发生错误,该场景中均未触发ACC和LKA功能'
        elif score_acc == 0 or score_lka == 0:
            score = 0
            evaluate_item = evaluate_item_acc + evaluate_item_lka + ',得0分.'
        else:
            score = score_lka + score_acc
            evaluate_item = evaluate_item_acc + evaluate_item_lka + f',得{score}分.'
    except RuntimeError:
        score = -1
        evaluate_item = error_msg
    except:
        score = -1
        evaluate_item = '评分功能发生错误,选择的评分脚本无法对此场景进行评价'
    finally:
        score_description = '1)  车辆未驶出本车道，维持设定车速且车速变动量不超过2km/h，稳定跟车时，跟车车间时距范围在1-3s，主车与目标车车速差不超过5km/h，得分100;\n' \
                            '2)  车辆未驶出本车道，维持设定车速且车速变动量不超过2km/h，稳定跟车时，跟车车间时距范围在1-3s，主车与目标车车速差在5-10km/h范围内，得分按照插值进行计算；\n' \
                            '3)  车辆未驶出本车道，维持设定车速且车速变动量在2-5km/h范围内，稳定跟车时，跟车车间时距范围在1-3s，主车与目标车车速差不超过5km/h，得分按照插值进行计算；\n' \
                            '4)  车辆未驶出本车道，维持设定车速且车速变动量在2-5km/h范围内，稳定跟车时，跟车车间时距范围在1-3s，主车与目标车车速差在5-10km/h范围内，得分按照插值进行计算；\n' \
                            '5)  其他情况，得分0。'
        return {
            'unit_scene_ID': script_id,
            'unit_scene_score': score,
            'evaluate_item': evaluate_item,
            'score_description': score_description
        }
