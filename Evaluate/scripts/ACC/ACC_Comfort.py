# @Author           : 汤宇飞
# @Time             : 2022/10/19
# @Function         : ACC_Comfort
# @Scenario         : 前车慢行/前方无车定速巡航
# @Usage            : 所有国赛ACC场景
# @UpdateTime       : /
# @UpdateUser       : /
import math


def get_report(scenario, script_id):
    try:
        start_index = 0
        end_index = 30
        velocity_var_score = 25
        yawrate_rms_score = 25
        velocity_var_flag = True
        yawrate_rms_flag = True
        acc_flag = True
        acc_roc_flag = True
        evaluate_item = ''
        scenario.scenario_data['velocity'] = (scenario.scenario_data['lateral_velocity'] ** 2 + scenario.scenario_data[
            'longitudinal_velocity'] ** 2) ** 0.5

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
            evaluate_item = '最大加速度变化率大于舒适行驶的范围'
            score = 0
            acc_roc_flag = False
        elif standard_max_loc_roc < max_lon_acc_roc < standard_max_loc_roc * 1.5:
            acc_roc_evaluate_item = '最大加速度变化率稍大'
            acc_roc_score = scenario.get_interpolation(max_lon_acc_roc, (standard_max_loc_roc, 25),
                                                       (standard_max_loc_roc * 1.5, 0))
        else:
            acc_roc_evaluate_item = '最大加速度变化率在舒适的范围内'
            acc_roc_score = 25

        # 最大加速度
        max_lon_acc = max(abs(scenario.scenario_data['longitudinal_accelerate_roc'].max()),
                          abs(scenario.scenario_data['longitudinal_accelerate_roc'].min()))
        if isinstance(max_lon_acc, str) and '错误' in max_lon_acc:
            error_msg = scenario.__error_message(scenario.get_lon_acc_roc).split('错误:')[1]
            raise RuntimeError
        standard_max_acc = scenario.get_interpolation(avg_velocity, (18, 5), (72, 3.5))
        if isinstance(standard_max_acc, str) and '错误' in standard_max_acc:
            error_msg = scenario.__error_message(scenario.get_interpolation).split('错误:')[1]
            raise RuntimeError
        elif standard_max_acc > 5:
            standard_max_acc = 5
        elif standard_max_acc < 3.5:
            standard_max_acc = 3.5
        if max_lon_acc > standard_max_acc * 1.5:
            evaluate_item = '舒适性指标中,车辆最大加速度大于舒适行驶的范围,得0分' if evaluate_item == '' else '舒适性指标中,车辆最大加速度和最大加速度变化率都大于舒适行驶的范围,得0分'
            score = 0
            acc_flag = False
        elif standard_max_acc < max_lon_acc < standard_max_acc * 1.5:
            acc_evaluate_item = '最大加速度稍大'
            acc_score = scenario.get_interpolation(max_lon_acc, (standard_max_acc, 25),
                                                   (standard_max_acc * 1.5, 0))
        else:
            acc_evaluate_item = '最大加速度在舒适的范围内'
            acc_score = 25
        if acc_flag and acc_roc_flag:
            for i in range(1, len(scenario.scenario_data) // 50 + 1):
                cut_df = scenario.scenario_data.iloc[start_index:end_index:]
                velocity_var = cut_df['velocity'].var()
                if velocity_var < 5:
                    velocity_var_score = 25
                    velocity_var_evaluate_item = '速度的方差在舒适的范围内'
                elif 5 < velocity_var < 10:
                    tmp_score = scenario.get_interpolation(velocity_var, (10, 0), (5, 25))
                    velocity_var_evaluate_item = '速度的方差稍大'
                    velocity_var_score = min(velocity_var_score, tmp_score)
                else:
                    score = 0
                    evaluate_item = '舒适性指标中,速度的方差大于舒适行驶的范围,得0分'
                    velocity_var_flag = False
                yawrate_rms = math.sqrt(
                    sum([x ** 2 for x in cut_df['yawrate'].values.tolist()]) / len(scenario.scenario_data))
                if yawrate_rms < 0.02:
                    yawrate_rms_score = 25
                    yawrate_rms_evaluate_item = '横摆角速度均方根在舒适的范围内'
                elif 0.02 < yawrate_rms < 0.04:
                    tmp_score = scenario.get_interpolation(yawrate_rms, (0.04, 0), (0.02, 25))
                    yawrate_rms_evaluate_item = '横摆角速度均方根稍大'
                    yawrate_rms_score = min(yawrate_rms_score, tmp_score)
                else:
                    yawrate_rms_flag = False
                    score = 0
                    evaluate_item = '舒适性指标中,横摆角速度均方根大于舒适行驶的范围,得0分'
                start_index = end_index
                end_index = start_index + 50
                if end_index >= len(scenario.scenario_data):
                    end_index = len(scenario.scenario_data)
                if not velocity_var_flag or not yawrate_rms_flag:
                    break
        if acc_roc_flag and acc_flag and velocity_var_flag and yawrate_rms_flag:
            score = acc_score + acc_roc_score + yawrate_rms_score + velocity_var_score
            evaluate_item = f'此次评价中:{acc_roc_evaluate_item};{acc_evaluate_item};{velocity_var_evaluate_item};' \
                            f'{yawrate_rms_evaluate_item};得{score}分'
    except RuntimeError:
        score = -1
        evaluate_item = error_msg
    except:
        score = -1
        evaluate_item = '评分功能发生错误,选择的评分脚本无法对此场景进行评价'
    finally:
        score = round(score, 2)
        score_description = '1)  车辆舒适性从4个纬度进行评分，满分为100分，每个纬度25分;\n' \
                            '2)  在每个维度中，满足舒适性25分，稍显不舒适在0分和25分之间插值，大于不舒适的阈值时得0分;\n' \
                            '3)  总得分为4个纬度相加获得，每个纬度互相独立;\n' \
                            '4)  如果有一项的零分则认为舒适性差，总分得0分。'
        return {
            'unit_scene_ID': script_id,
            'unit_scene_score': score,
            'evaluate_item': evaluate_item,
            'score_description': score_description
        }
