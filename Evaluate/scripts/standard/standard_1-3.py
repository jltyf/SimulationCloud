# @Author           : 汤宇飞
# @Time             : 2022/11/30
# @Function         : standard_1-3
# @Scenario         : 交通信号灯识别及响应
# @Usage            : 交通灯由红变绿
# @UpdateTime       : 2022/11/30
# @UpdateUser       : 汤宇飞

def fun(index_time):
    if index_time < 14:
        color = 'red'
    elif 14 <= index_time < 16:
        color = 'yellow'
    else:
        color = 'green'
    return color


def get_report(scenario, script_id):
    try:
        # speed_limit_list = scenario.scenario_data['speed_limit'].values.tolist()
        # if 1 in speed_limit_list:
        #     speed_limit_flag = True
        # else:
        #     speed_limit_flag = False
        traffic_light_flag = True
        # 交通灯位置
        signal_x = 600
        signal_y = -385
        # scenario.scenario_data['traffic_light_flag'] = True
        # scenario.scenario_data['traffic_light_color'] = [scenario.scenario_data.index > 14]
        if traffic_light_flag:
            red_light_data = scenario.scenario_data[scenario.scenario_data['traffic_light_color'] == 'red']
            yellow_light_data = scenario.scenario_data[scenario.scenario_data['traffic_light_color'] == 'yellow']
            green_light_data = scenario.scenario_data[scenario.scenario_data['traffic_light_color'] == 'green']
            scenario.scenario_data['light_distance'] = (((scenario.scenario_data['x_coordination'] - signal_x) ** 2 + (
                    scenario.scenario_data['y_coordination'] - signal_y)) ** 0.5).fillna(0)

            limit_start_velocity = scenario.get_velocity(1)
            if isinstance(limit_start_velocity, str) and '错误' in limit_start_velocity:
                error_msg = scenario.__error_message(scenario.get_velocity, False).split('错误:')[1]
                raise RuntimeError
            limit_max_velocity = scenario.get_max_velocity(start_time=1)
            if isinstance(limit_max_velocity, str) and '错误' in limit_max_velocity:
                error_msg = scenario.__error_message(scenario.get_max_velocity, False).split('错误:')[1]
                raise RuntimeError
            # if limit_start_velocity <= speed_limit:
            #     if limit_max_velocity > speed_limit:
            #         score = 60
            #         evaluate_item = '测试车辆到达限速标志时，车速不高于限速标志所示速度,但后续未能将速度维持在限速之内,得60分'
            #     else:
            #         score = 100
            #         evaluate_item = '测试车辆到达限速标志时，车速不高于限速标志所示速度,且能将速度维持在限速范围内,得100分'
            # else:
            #     score = 0
            #     evaluate_item = '测试车辆到达限速标志时，车速高于限速标志所示速度,得0分'
        else:
            score = 0
            evaluate_item = '未能识别交通信号灯,得0分'
    except RuntimeError:
        score = -1
        evaluate_item = error_msg
    except:
        score = -1
        evaluate_item = '评分功能发生错误,选择的评分脚本无法对此场景进行评价'
    finally:
        score_description = '1) 能够正常识别限速标志；\n2) 能够在测试车辆到达限速标志时，车速不高于限速标志所示速度；\n3)在限速范围内车速不高于限速。'
        return {
            'unit_scene_ID': script_id,
            'unit_scene_score': score,
            'evaluate_item': evaluate_item,
            'score_description': score_description,
        }
