# coding=UTF-8
import sys

import pandas as pd
import os

from Evaluate.models.evaluation_model import ScenarioData
from enumerations import ScenarioType
from log.log_set import Loggers

scenarios_category_list = ['AEB', 'ALC', 'ACC', 'LKA']


def scenario_score(scenario_data_path, scenario_type, script_name=None):
    """
    :param scenario_data_path:vtd输出数据的csv文件
    :param scenario_type: 场景的类型(自然驾驶，交通法规，事故场景，泛化场景)
    :param script_name: 默认脚本，如果没有设置就用csv数据中的场景ID查找
    :return:
            返回一个dict，包含生成报告需要的信息
            示例:
            {
            ‘unit_scene_ID':'AEB1-1_1',
            'unit_scene_score':60,
            'evaluate_item':'减速度为5.5，不满足3.5-5m/s2的指标范围',
            'score_description':'1)未发生碰撞，且自车最大减速度3.5-5m/s2，最大减速度变化率为3-5m/s³，得分100；'
                                 2).....'
            }
    """
    csv_data = pd.read_csv(scenario_data_path)
    csv_df = pd.DataFrame(csv_data)

    # 创建ScenarioData类需要传入标准格式数据的dataframe
    scenario = ScenarioData(csv_df, scenario_type)
    scenario_id = (script_name if script_name else scenario.get_scenario_id())
    for scenario_category in scenarios_category_list:
        if scenario_category in scenario_id:
            scripts_path = os.path.join(os.path.join(os.getcwd(), 'scripts'), scenario_category)
            for script_id in os.listdir(scripts_path):
                if script_id.split('.p')[0] == scenario_id:
                    function_name = 'get_report'
                    sys.path.append(scripts_path)
                    evaluate = __import__(scenario_id)
                    imp_function = getattr(evaluate, function_name)
                    return imp_function(scenario, scenario_id)
                    # try:
                    #     return imp_function(scenario, scenario_id)
                    #     return imp_function(scenario, scenario_id)
                    # except Exception as e:
                    #     error_txt = e.args[0]
                    #     log = Loggers()
                    #     log.logger.info(f'错误信息:{error_txt},发生脚本:{scenario_id}')


if __name__ == '__main__':
    result = scenario_score('D:/test_data_ACC1-4_Ego.csv', ScenarioType.natural.value, 'AEB_1-1')
    print(result)
