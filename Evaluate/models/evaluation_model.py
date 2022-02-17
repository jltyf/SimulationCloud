import math

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

    def get_velocity(self, time_stamp, obj_id=0):
        """
        根据横向速度和纵向速度获取某个时间点的自车或目标物的速度
        :param time_stamp: 需求速度的时间戳
        :param obj_id: 默认为0时获取自车的速度
        :return: velocity time_stamp时刻的速度
        """
        # 自车的速度
        if obj_id == 0:
            lateral_v = self.scenario_data[time_stamp]['lateral_velocity']
            longitudinal_v = self.scenario_data[time_stamp]['longitudinal_velocity']
        else:
            lateral_v = self.scenario_data[time_stamp]['lateral_velocity'] + \
                        self.scenario_data[self.scenario_data['object_ID'] == obj_id][time_stamp]['lateral_velocity']
            longitudinal_v = self.scenario_data[time_stamp]['longitudinal_velocity'] + \
                             self.scenario_data[self.scenario_data['object_ID'] == obj_id][time_stamp][
                                 'longitudinal_velocity']
        return math.sqrt(lateral_v ** 2 + longitudinal_v ** 2)
