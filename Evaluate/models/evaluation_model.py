import math

import pandas as pd

from enumerations import ScenarioType


class ScenarioData(object):
    def __init__(self, scenarios_data, obj_scenarios_data, scenario_type):
        """
        :param scenarios_data: 数据为从vtd输出的自车csv数据文件读取的csv
        :param obj_scenarios_data: 数据为从vtd输出的目标车csv数据文件读取的csv
        :param scenario_type: 场景的类型 1自然驾驶 2交通法规 3事故场景 4泛化场景
        """

        index = scenarios_data.loc[scenarios_data['time'] == 0.2].index.values[0]
        scenarios_data = scenarios_data.loc[index:]
        self.scenario_data = scenarios_data.set_index(keys=['time'])
        self.scenario_type = scenario_type
        # 车道宽度暂定3.75
        self.lane_width = 3.75
        time = obj_scenarios_data['time'][0]
        if time <= 0.2:
            index = obj_scenarios_data.loc[obj_scenarios_data['time'] >= 0.2].index.values[0]
            obj_scenarios_data = obj_scenarios_data.loc[index:]
            self.obj_scenario_data = obj_scenarios_data.set_index(keys=['time'])
        else:
            self.obj_scenario_data = obj_scenarios_data.set_index(keys=['time'])

    def get_scenario_id(self):
        if not self.scenario_type == ScenarioType.generalization.value:
            return self.scenario_data.iloc[1]['unit_scene_ID']
        else:
            name_list = self.scenario_data.iloc[1]['unit_scene_ID'].split('_')
            return name_list[0] + '_' + name_list[1]

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
        else:
            obj_data = self.obj_scenario_data[(self.obj_scenario_data['object_ID'] == obj_id)]
            lateral_v = self.scenario_data.loc[time_stamp]['lateral_velocity'] + obj_data.loc[time_stamp][
                'object_rel_vel_y']
            longitudinal_v = self.scenario_data.loc[time_stamp]['longitudinal_velocity'] + obj_data.loc[time_stamp][
                'object_rel_vel_x']
        return math.sqrt(lateral_v ** 2 + longitudinal_v ** 2)

    def get_max_velocity(self, obj_id=0):
        """
        获取自车或目标车的最大速度
        :param obj_id: 为0时为自车
        :return:max_velocity 最大速度
        """
        self.scenario_data['velocity'] = (self.scenario_data['lateral_velocity'] ** 2 + self.scenario_data[
            'longitudinal_velocity'] ** 2) ** 0.5
        # 自车
        if obj_id == 0:
            max_velocity = self.scenario_data['velocity'].max()
        # 目标车
        else:
            obj_data = self.obj_scenario_data[(self.obj_scenario_data['object_ID'] == obj_id)]
            self.scenario_data['object_velocity'] = ((self.scenario_data['lateral_velocity'] + obj_data[
                'object_rel_vel_y']) ** 2 + (self.scenario_data['longitudinal_velocity'] + obj_data[
                'object_rel_vel_x']) ** 2) ** 0.5
            max_velocity = self.scenario_data['object_velocity'].max()
        return max_velocity

    def get_min_velocity(self, obj_id=0):
        """
        获取自车或目标车的最小速度
        :param obj_id: 为0时为自车
        :return:min_velocity 最小速度
        """
        self.scenario_data['velocity'] = (self.scenario_data['lateral_velocity'] ** 2 + self.scenario_data[
            'longitudinal_velocity'] ** 2) ** 0.5
        # 自车
        if obj_id == 0:
            min_velocity = self.scenario_data['velocity'].min()
        # 目标车
        else:
            obj_data = self.obj_scenario_data[(self.obj_scenario_data['object_ID'] == obj_id)]
            self.scenario_data['object_velocity'] = ((self.scenario_data['lateral_velocity'] + obj_data[
                'object_rel_vel_y']) ** 2 + (self.scenario_data['longitudinal_velocity'] + obj_data[
                'object_rel_vel_x']) ** 2) ** 0.5
            min_velocity = self.scenario_data['object_velocity'].min()
        return min_velocity

    def get_velocity_variation(self, start_time, end_time):
        """
        获取一段时间内的自车车速变化量
        :param start_time: 起始时间戳
        :param end_time: 结束时间戳
        :return: velocity_variation 速度变化量，返回的为速度差的绝对值
        """
        self.scenario_data['velocity'] = (self.scenario_data['lateral_velocity'] ** 2 + self.scenario_data[
            'longitudinal_velocity'] ** 2) ** 0.5

        velocity_variation = abs(
            self.scenario_data.loc[start_time]['velocity'] - self.scenario_data.loc[end_time]['velocity'])

        return velocity_variation

    def get_lon_acc_roc(self, time_stamp):
        """
        获取纵向加速度变化率
        :param time_stamp: 需要获取结果的时间戳
        :return:lon_acc_roc 纵向加速度变化率
        """
        time_list = self.scenario_data.index.values.tolist()
        now_lon_acc = self.scenario_data.loc[time_stamp]['longitudinal_acceleration']
        index = time_list.index(time_stamp)
        pre_time_stamp = time_list[index - 1]
        pre_lon_acc = self.scenario_data.loc[pre_time_stamp]['longitudinal_acceleration']
        lon_acc_roc = (now_lon_acc - pre_lon_acc) / pre_lon_acc
        return lon_acc_roc

    def get_lat_acc_roc(self, time_stamp):
        """
        获取横向加速度变化率
        :param time_stamp: 需要获取结果的时间戳
        :return:lat_acc_roc 横向加速度变化率
        """
        time_list = self.scenario_data.index.values.tolist()
        now_lon_acc = self.scenario_data.loc[time_stamp]['lateral_acceleration']
        index = time_list.index(time_stamp)
        pre_time_stamp = time_list[index - 1]
        pre_lat_acc = self.scenario_data.loc[pre_time_stamp]['lateral_acceleration']
        lat_acc_roc = (now_lon_acc - pre_lat_acc) / pre_lat_acc
        return lat_acc_roc

    def get_lon_acc_roc_max(self, start_time=None, end_time=None):
        """
        获取一段时间内的轨迹的最大纵向加速度变化率
        如果起始时间传参为空，默认使用轨迹起始时间
        如果结束时间传参为空，默认使用轨迹结束时间
        :param start_time: 计算加速度变化率的起始时间
        :param end_time: 计算加速度变化率的结束时间
        :return: 这段时间内最大纵向加速度变化率
        """
        index_list = self.scenario_data.index.tolist()
        start_time = index_list[0] if not start_time else start_time
        end_time = index_list[-1] if not end_time else end_time
        self.scenario_data = self.scenario_data.loc[start_time:end_time]
        lon_acc_roc_max = self.scenario_data['longitudinal_accelerate_roc'].max()
        return lon_acc_roc_max

    def get_lat_acc_roc_max(self, start_time=None, end_time=None):
        """
        获取一段时间内的轨迹的最大横向加速度变化率
        如果起始时间传参为空，默认使用轨迹起始时间
        如果结束时间传参为空，默认使用轨迹结束时间
        :param start_time: 计算加速度变化率的起始时间
        :param end_time: 计算加速度变化率的结束时间
        :return: 这段时间内最大横向加速度变化率
        """
        index_list = self.scenario_data.index.tolist()
        start_time = index_list[0] if not start_time else start_time
        end_time = index_list[-1] if not end_time else end_time
        self.scenario_data = self.scenario_data.loc[start_time:end_time]
        lat_acc_roc_max = self.scenario_data['lateral_accelerate_roc'].max()
        return lat_acc_roc_max

    def get_change_lane_time(self):
        """
        通过车道中心偏移距离大于1m时的时间开始判断变道
        :return: 变道轨迹的持续时间
        """
        lane_offset = 1
        # 筛选出航向角小于3度且距离车道中心小于一半的数据
        change_lane_trail = self.scenario_data.query(
            '(lane_center_offset<-@lane_offset) or (lane_center_offset>@lane_offset)')
        timestamp_list = change_lane_trail.index.values.tolist()
        try:
            start_time = timestamp_list[0]
            end_time = timestamp_list[-1]
            period = (end_time - start_time) / 1000
            return period
        except:
            return 0

    def get_obj_acc(self, time_stamp):
        """
        获取目标车在某时刻的加速度
        :return:
        """
        ego_lat_acc = self.scenario_data.loc[time_stamp]['lateral_acceleration']
        ego_lon_acc = self.scenario_data.loc[time_stamp]['longitudinal_acceleration']
        obj_rel_lat_acc = self.obj_scenario_data.loc[time_stamp]['object_rel_acc_y']
        obj_rel_lon_acc = self.obj_scenario_data.loc[time_stamp]['object_rel_acc_x']
        obj_lat_acc = ego_lat_acc + obj_rel_lat_acc
        obj_lon_acc = ego_lon_acc + obj_rel_lon_acc
        return math.sqrt(obj_lat_acc ** 2 + obj_lon_acc ** 2)

    def __error_message(self, method, ego_flag):
        """
        通过调用的方法名判断是否在获取评分所需的值时发生错误
        :param method:发生错误的方法名
        :param ego_flag:判断是否是自车的标志位
        :return:错误信息
        """
        if method == self.get_velocity:
            if ego_flag:
                return '错误:获取自车的速度失败,选择的评分脚本无法对此场景进行评价'
            else:
                return '错误:获取目标车的速度失败,选择的评分脚本无法对此场景进行评价'
        elif method == self.get_max_velocity:
            if ego_flag:
                return '错误:获取自车的最大速度失败,选择的评分脚本无法对此场景进行评价'
            else:
                return '错误:获取目标车的最大速度失败,选择的评分脚本无法对此场景进行评价'
        elif method == self.get_min_velocity:
            if ego_flag:
                return '错误:获取自车的最小速度失败,选择的评分脚本无法对此场景进行评价'
            else:
                return '错误:获取目标车的最小速度失败,选择的评分脚本无法对此场景进行评价'
        elif method == self.get_velocity_variation:
            return '错误:获取自车的车速变化量失败,选择的评分脚本无法对此场景进行评价'
        elif method == self.get_lon_acc_roc:
            return '错误:获取自车的纵向加速度变化率失败,选择的评分脚本无法对此场景进行评价'
        elif method == self.get_lat_acc_roc:
            return '错误:获取自车的横向加速度变化率失败,选择的评分脚本无法对此场景进行评价'
        elif method == self.get_lon_acc_roc_max:
            return '错误:获取自车的最大纵向加速度变化率失败,选择的评分脚本无法对此场景进行评价'
        elif method == self.get_lat_acc_roc_max:
            return '错误:获取自车的最大横向加速度变化率失败,选择的评分脚本无法对此场景进行评价'
        elif method == self.get_change_lane_time:
            return '错误:获取目标车的加速度失败,选择的评分脚本无法对此场景进行评价'
        elif method == self.get_obj_acc:
            return '错误:获取目标车的加速度失败,选择的评分脚本无法对此场景进行评价'
        else:
            return '错误:评分功能发生,选择的评分脚本无法对此场景进行评价'
