import sys

import pandas as pd
import os
from Evaluate.models.evaluation_model import ScenarioData
from enumerations import ScenarioType


def scenario_score(scenario_data_path, scenario_type):
    """
    :param scenario_data_path:vtd输出数据的csv文件
    :param scenario_type: 场景的类型(自然驾驶，交通法规，事故场景，泛化场景)
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
    csv_data = pd.read_csv(scenario_data_path)  # 防止弹出警告
    csv_df = pd.DataFrame(csv_data)

    # 创建ScenarioData类需要传入标准格式数据的dataframe
    scenario = ScenarioData(csv_df, scenario_type)
    scenario_id = scenario.get_scenario_id()
    scripts_path = os.path.join(os.getcwd(), 'scripts')
    for script_id in os.listdir(os.path.join(os.getcwd(), 'scripts')):
        if script_id.split('.p')[0] == scenario_id:
            function_name = 'get_report'
            sys.path.append(scripts_path)
            evaluate = __import__(scenario_id)
            imp_function = getattr(evaluate, function_name)
            return imp_function(scenario.scenario_data, scenario_id)


if __name__ == '__main__':
    result = scenario_score('D:/temp_22020216.csv', ScenarioType.generalization)
    print(result)
