from enumerations import ScenarioType


class ScenarioData(object):
    def __init__(self, scenarios_data, scenario_type):
        """
        :param scenarios_data: 数据为从vtd输出的csv数据文件读取的csv
        """
        self.scenario_data = scenarios_data.set_index(keys=['time'])
        self.scenario_type = scenario_type

    def get_scenario_id(self):
        if not self.scenario_type == ScenarioType.generalization:
            return self.scenario_data.iloc[1]['unit_scene_ID']
        else:
            return self.scenario_data.iloc[1]['unit_scene_ID'].split('_')[0]
