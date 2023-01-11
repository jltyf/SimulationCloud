# @Author           : 汤宇飞
# @Time             : 2022/11/30
# @Function         : standard_1-2
# @Scenario         : 人行横道识别及响应
# @Usage            : 存在人行横道的场景
# @UpdateTime       : 2022/11/30
# @UpdateUser       : 汤宇飞


def get_report(scenario, script_id):
    try:
        # crossing_list = scenario.scenario_data['crossing'].values.tolist()
        # if 1 in crossing_list:
        #     crossing_flag = True
        # else:
        #     crossing_flag = False
        crossing_flag = True
        speed_limit = 30
        # 人行横道位置
        signal_x = 630
        signal_y = -390
        if crossing_flag:
            scenario.scenario_data['signal_distance'] = (((scenario.scenario_data['x_coordination'] - signal_x) ** 2 + (
                    scenario.scenario_data['y_coordination'] - signal_y)) ** 0.5).fillna(0)
            limit_start_time = min(scenario.scenario_data['signal_distance'][
                                       (scenario.scenario_data['signal_distance'] < 10)].index.tolist())
            limit_start_velocity = scenario.get_velocity(limit_start_time)
            if isinstance(limit_start_velocity, str) and '错误' in limit_start_velocity:
                error_msg = scenario.__error_message(scenario.get_velocity, False).split('错误:')[1]
                raise RuntimeError
            if limit_start_velocity <= speed_limit:
                score = 100
                evaluate_item = '测试车辆通过人行横道时，车速不高于30km/h,得100分'
            else:
                score = 0
                evaluate_item = '测试车辆到达限速标志时，车速高于30km/h,得0分'
        else:
            score = 0
            evaluate_item = '未能识别场景中的限速标牌,得0分'
    except RuntimeError:
        score = -1
        evaluate_item = error_msg
    except:
        score = -1
        evaluate_item = '评分功能发生错误,选择的评分脚本无法对此场景进行评价'
    finally:
        score_description = '1) 能够正常识别人行横道；\n2) 能够在测试车辆通过人行横道时，车速不高于30km/h。'
        return {
            'unit_scene_ID': script_id,
            'unit_scene_score': score,
            'evaluate_item': evaluate_item,
            'score_description': score_description,
        }
