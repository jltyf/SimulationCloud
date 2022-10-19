# @Author           : 李玲星
# @Time             : 2022/09/07
# @Function         : GSAEBLKA_1
# @Scenario         : 前车静止、前车减速+直道居中行驶、弯道居中行驶
# @Usage            : 国赛自动紧急制动+车道保持组合测试一、二、三、四、五;太和桥自动紧急制动+车道保持组合测试一、二、三、四
# @UpdateTime       : 2022/10/19
# @UpdateUser       : 汤宇飞

from enumerations import CollisionStatus


def get_report(scenario, script_id):
    try:
        start_velocity = scenario.get_average_velocity(scenario.scenario_data.iloc[:5].index.values.tolist())
        if isinstance(start_velocity, str) and '错误' in start_velocity:
            error_msg = start_velocity.split('错误:')[1]
            raise RuntimeError
        AEB_data = scenario.scenario_data[scenario.scenario_data['longitudinal_acceleration'] <= -(start_velocity/360)]
        if len(AEB_data) > 20:
            AEB_flag = True  # temporary
        else:
            AEB_flag = False
        LKA_flag = True  # temporary
        if LKA_flag:
            first_lane_id = scenario.scenario_data.iloc[0]['lane_id']
            center_offer_max = max(scenario.scenario_data['lane_center_offset'].max(), abs(scenario.scenario_data['lane_center_offset'].min()))
            lane_id_list = list(set(scenario.scenario_data['lane_id'].tolist()))
            if len(lane_id_list) == 1 and lane_id_list[0] == first_lane_id and center_offer_max < 0.8:
                start_index = 0
                end_index = 30
                for i in range(1, len(scenario.scenario_data) // 30 + 1):
                    cut_df = scenario.scenario_data.iloc[start_index:end_index:]
                    if abs(cut_df['steering_angle'].mean()) < 20 and cut_df['steering_angle'].var() < 200:
                        stable_velocity = scenario.get_velocity(cut_df.index.values.tolist()[-1])
                        if isinstance(start_velocity, str) and '错误' in start_velocity:
                            error_msg = start_velocity.split('错误:')[1]
                            raise RuntimeError
                        v_diff = abs(stable_velocity - start_velocity)
                        if v_diff <= 2:
                            score_lka = 50
                            evaluate_item_lka = 'LKA功能：车辆未使出本车道且维持设定车速且车速变动量不超过2km/h'
                        elif 2 < v_diff <= 5:
                            score_lka = round(scenario.get_interpolation(v_diff, (2, 50), (5, 0)), 0)
                            evaluate_item_lka = 'LKA功能：车辆未使出本车道且维持设定车速且车速变动量在2-5km/h范围内'
                        else:
                            score_lka = 0
                            evaluate_item_lka = 'LKA功能：车辆未使出本车道但未能维持设定车速'
                        break
                    start_index = end_index
                    end_index = start_index + 30
                    if end_index >= len(scenario.scenario_data):
                        end_index = len(scenario.scenario_data)
            else:
                score_lka = 0
                evaluate_item_lka = 'LKA功能：车辆驶出本车道'
        else:
            score_lka = 50
            evaluate_item_lka = '场景中未触发LKA功能.'
        if AEB_flag:
            collision_status_list = scenario.scenario_data['collision_status'].values.tolist()
            if CollisionStatus.collision.value not in collision_status_list:
                frame = scenario.scenario_data.iloc[-1]['frame_ID']
                same_direction_obj = scenario.obj_scenario_data[(scenario.obj_scenario_data['frame_ID'] == frame) & ((
                        scenario.obj_scenario_data['object_direction'] <= 5) | (scenario.obj_scenario_data[
                                                                                    'object_direction'] >= 355))]
                obj_distance = same_direction_obj.copy()
                obj_distance['distance'] = (same_direction_obj['object_rel_pos_y']**2 + same_direction_obj[
                    'object_rel_pos_x']**2)**0.5
                distance_final = obj_distance['distance'].min()
                if distance_final >= 5:
                    score_aeb = 50
                    evaluate_item_aeb = 'AEB功能：车辆未发生碰撞且前方车辆静止时，自车制动后与前车车距不小于5米;'
                else:
                    score_aeb = 25
                    evaluate_item_aeb = 'AEB功能：车辆未发生碰撞且前方车辆静止时，自车制动后与前车车距小于5米;'
            else:
                score_aeb = 0
                evaluate_item_aeb = 'AEB功能：车辆发生碰撞;'
        else:
            score_aeb = 50
            evaluate_item_aeb = 'AEB功能：场景中未触发;'
        if not AEB_flag and not LKA_flag:
            score = -1
            evaluate_item = '评分功能发生错误,该场景中均未触发AEB和LKA功能'
        elif score_aeb == 0 or score_lka == 0:
            score = 0
            evaluate_item = evaluate_item_aeb + evaluate_item_lka + ',得0分.'
        else:
            score = score_lka + score_aeb
            evaluate_item = evaluate_item_aeb + evaluate_item_lka + f',得{score}分.'
    except RuntimeError:
        score = -1
        evaluate_item = error_msg
    except:
        score = -1
        evaluate_item = '评分功能发生错误,选择的评分脚本无法对此场景进行评价'


    finally:
        score_description = '1） 车辆未驶出本车道，维持设定车速且车速变动量小等于2km/h；前方车辆静止时，自车制动后与前车车距不小于5米，得100分。\n' \
                            '2) 车辆未驶出本车道，维持设定车速且车速变动量小等于2km/h；前方车辆静止时，自车制动后与前车车距小于5米，得75分；\n' \
                            '3) 车辆未驶出本车道，维持设定车速且车速变动量在2-5km/h内;前方车辆静止时，自车与前方车辆未发生碰撞，得分按照插值进行计算;\n' \
                            '4) 其他情况，得0分；'
        return {
            'unit_scene_ID': script_id,
            'unit_scene_score': score,
            'evaluate_item': evaluate_item,
            'score_description': score_description,
        }
