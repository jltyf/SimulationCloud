# @Author           : 汤宇飞
# @Time             : 2022/10/19
# @Function         : ACC_Comfort_1(最大加速度变化率)
# @Scenario         : 前车慢行/前方无车定速巡航
# @Usage            : 所有国赛ACC场景
# @UpdateTime       : /
# @UpdateUser       : /

def get_report(scenario, script_id):
    try:
        # 最大加速度变化率
        max_lon_acc_roc = scenario.get_lon_acc_roc_max()
        if isinstance(max_lon_acc_roc, str) and '错误' in max_lon_acc_roc:
            error_msg = max_lon_acc_roc.split('错误:')[1]
            raise RuntimeError
        avg_velocity = scenario.get_velocity(scenario.scenario_data.index.values.tolist()[-1])
        if isinstance(avg_velocity, str) and '错误' in avg_velocity:
            error_msg = scenario.__error_message(scenario.get_velocity).split('错误:')[1]
            raise RuntimeError
        standard_max_loc_roc = scenario.get_interpolation(avg_velocity, (18, 5), (72, 2.5))
        if isinstance(standard_max_loc_roc, str) and '错误' in standard_max_loc_roc:
            error_msg = scenario.__error_message(scenario.get_interpolation).split('错误:')[1]
            raise RuntimeError
        elif standard_max_loc_roc > 5:
            standard_max_loc_roc = 5
        elif standard_max_loc_roc < 2.5:
            standard_max_loc_roc = 2.5
        if max_lon_acc_roc > standard_max_loc_roc * 1.5:
            evaluate_item = '最大加速度变化率的舒适性指标中,车辆最大加速度变化率大于舒适行驶的范围,得0分'
            score = 0
        elif standard_max_loc_roc < max_lon_acc_roc < standard_max_loc_roc * 1.5:
            score = scenario.get_interpolation(max_lon_acc_roc, (standard_max_loc_roc, 100),
                                               (standard_max_loc_roc * 1.5, 0))
            evaluate_item = f'最大加速度变化率的舒适性指标中,车辆最大加速度变化率稍大,得{score}分'
        else:
            evaluate_item = '最大加速度变化率的舒适性指标中,车辆最大加速度变化率在舒适的范围内,得100分'
            score = 100
    except RuntimeError:
        score = -1
        evaluate_item = error_msg
    except:
        score = -1
        evaluate_item = '评分功能发生错误,选择的评分脚本无法对此场景进行评价'
    finally:
        score_description = '1)  当车速大等于72km/h时加速度变化率舒适值为2.5m/s³，当车速小等于18km/h时加速度变化率舒适值为5m/s³，当车速在72km/h和18km/h时线性插值确定舒适值;\n' \
                            '2)  当车辆最大加速度变化率小于舒适值时被认为舒适,得100分;\n' \
                            '3)  当车辆最大加速度变化率大于舒适值的1.5倍时被认为极不舒适，得0分;\n' \
                            '4)  当车辆最大加速度变化率在舒适值和舒适值的1.5倍之间时被认为不舒适，按照0分到100分进行插值。'
        return {
            'unit_scene_ID': script_id,
            'unit_scene_score': score,
            'evaluate_item': evaluate_item,
            'score_description': score_description
        }
