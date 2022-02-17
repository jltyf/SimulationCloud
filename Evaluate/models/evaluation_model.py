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
            lateral_v = self.scenario_data.loc[time_stamp]['lateral_velocity']
            longitudinal_v = self.scenario_data.loc[time_stamp]['longitudinal_velocity']
        # 目标车的速度
        else:
            lateral_v = self.scenario_data.loc[time_stamp]['lateral_velocity'] + \
                        self.scenario_data[self.scenario_data['object_ID'] == obj_id][time_stamp]['object_rel_vel_x']
            longitudinal_v = self.scenario_data.loc[time_stamp]['longitudinal_velocity'] + \
                             self.scenario_data[self.scenario_data['object_ID'] == obj_id][time_stamp][
                                 'object_rel_vel_y']
        return math.sqrt(lateral_v ** 2 + longitudinal_v ** 2)

    def get_max_velocity(self, obj_id=0):
        """
        获取自车或目标车的最大速度
        :param obj_id: 为0时为自车
        :return:max_velocity 最大速度
        """
        # 自车
        self.scenario_data['velocity'] = math.sqrt(
            self.scenario_data['lateral_velocity'] ** 2 + self.scenario_data['longitudinal_velocity'] ** 2)
        if obj_id == 0:
            max_velocity = self.scenario_data['velocity'].max()
        # 目标车
        else:
            self.scenario_data['object_velocity'] = math.sqrt(
                (self.scenario_data['lateral_velocity'] + self.scenario_data['object_rel_vel_x']) ** 2 + (
                        self.scenario_data['longitudinal_velocity'] + self.scenario_data['object_rel_vel_y']) ** 2)
            max_velocity = self.scenario_data[self.scenario_data['object_ID'] == obj_id]['object_velocity'].max()
        return max_velocity

    def get_min_velocity(self, obj_id=0):
        """
        获取自车或目标车的最小速度
        :param obj_id: 为0时为自车
        :return:min_velocity 最小速度
        """
        # 自车
        self.scenario_data['velocity'] = math.sqrt(
            self.scenario_data['lateral_velocity'] ** 2 + self.scenario_data['longitudinal_velocity'] ** 2)
        if obj_id == 0:
            min_velocity = self.scenario_data['velocity'].min()
        # 目标车
        else:
            self.scenario_data['object_velocity'] = math.sqrt(
                (self.scenario_data['lateral_velocity'] + self.scenario_data['object_rel_vel_x']) ** 2 + (
                        self.scenario_data['longitudinal_velocity'] + self.scenario_data['object_rel_vel_y']) ** 2)
            min_velocity = self.scenario_data[self.scenario_data['object_ID'] == obj_id]['object_velocity'].min()
        return min_velocity

    def get_velocity_variation(self, start_time, end_time):
        """
        获取一段时间内的自车车速变化量
        :param start_time: 起始时间戳
        :param end_time: 结束时间戳
        :return: velocity_variation 速度变化量，返回的为速度差的绝对值
        """
        self.scenario_data['velocity'] = math.sqrt(
            self.scenario_data['lateral_velocity'] ** 2 + self.scenario_data['longitudinal_velocity'] ** 2)

        velocity_variation = abs(
            self.scenario_data.loc[start_time]['velocity'] - self.scenario_data.loc[end_time]['velocity'])

        return velocity_variation
