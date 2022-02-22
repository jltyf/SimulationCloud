import itertools

from enumerations import DataType


class ADASScenario(object):
    def __init__(self, scenario_series):
        self.scenario_generalization_list = list()
        self.scenario_dict = dict()
        self.scenario_dict['scene_id'] = scenario_series['场景编号']
        self.scenario_dict['scenario_name'] = scenario_series['场景名称']
        self.scenario_dict['ego_start_x'] = scenario_series['自车初始x坐标']
        self.scenario_dict['ego_start_y'] = scenario_series['自车初始y坐标']
        self.scenario_dict['ego_start_velocity'] = eval(scenario_series['自车初始速度V0(km/h)'])
        self.scenario_dict['ego_heading_angle'] = str(scenario_series['自车航向角'])
        self.scenario_dict['ego_velocity_status'] = str(scenario_series['自车行驶速度状态'])
        self.scenario_dict['ego_trajectory'] = str(scenario_series['自车轨迹形态'])
        self.scenario_dict['ego_duration_time'] = str(scenario_series['自车轨迹持续时间(s)']).split(',')
        self.scenario_dict['ego_velocity_time'] = eval(scenario_series['自车速度分段持续时间'])
        self.scenario_dict['ego_trajectory_time'] = eval(scenario_series['自车轨迹形态分段持续时间'])
        # self.scenario_dict['scene_type'] = str(scenario_series['scene_type'])
        # self.scenario_dict['road_type'] = str(scenario_series['road_type'])
        # self.scenario_dict['road_section'] = str(scenario_series['road_section'])
        # self.scenario_dict['scene_description'] = str(scenario_series['scene_description'])
        # self.scenario_dict['test_procedure'] = str(scenario_series['test_procedure'])
        # self.scenario_dict['expect_test_result'] = str(scenario_series['expect_test_result'])
        self.scenario_dict['obs_start_x'] = str(scenario_series['目标初始x坐标']).split(',')
        self.scenario_dict['obs_start_y'] = eval(scenario_series['目标初始y坐标'])
        self.scenario_dict['obs_start_velocity'] = eval(scenario_series['目标初始速度V1(km/h)'])
        self.scenario_dict['obs_velocity_status'] = str(scenario_series['目标行驶速度状态']).split(',')
        self.scenario_dict['obs_trajectory'] = str(scenario_series['目标轨迹形态']).split(',')
        self.scenario_dict['obs_duration_time'] = str(scenario_series['目标轨迹持续时间(s)']).split(',')
        self.scenario_dict['obs_trail_time'] = str(scenario_series['目标轨迹形态分段持续时间(s)']).split(',')
        self.scenario_dict['obs_heading_angle_rel'] = str(scenario_series['目标物相对自车航向角']).split(',')
        self.scenario_dict['obs_velocity_time'] = str(scenario_series['目标速度分段持续时间(s)']).split(',')
        # self.scenario_dict['direction'] = str(scenario_series['目标正反向标志']).split(',')[-1]
        self.scenario_dict['generalization_type'] = eval(scenario_series['泛化标志位'])
        if self.scenario_dict['scenario_name'] in 'PCW':
            self.scenario_dict['ped_initial_position_x'] = str(scenario_series['目标初始x坐标']).split(',')
            self.scenario_dict['ped_initial_position_y'] = str(scenario_series['目标初始y坐标']).split(',')
            self.scenario_dict['ped_speed_status'] = str(scenario_series['目标行驶速度状态']).split(',')
            self.scenario_dict['ped_trajectory'] = str(scenario_series['目标轨迹形态']).split(',')
            self.scenario_dict['ped_speed_duration_time'] = str(scenario_series['目标速度分段持续时间(s)']).split(',')
            self.scenario_dict['pedT_trail_section_duration_time'] = str(scenario_series['目标轨迹形态分段持续时间(s)']).split(',')
            self.scenario_dict['ped_heading_angle_rel'] = str(scenario_series['目标物相对自车航向角']).split(',')

    def get_scenario_model(self):
        characteristic_list = list()
        keys_list = list()
        for key, values in self.scenario_dict['generalization_type'].items():
            values_list = list()
            if values == DataType.generalizable.value:
                min_value = self.scenario_dict[key][0]
                max_value = self.scenario_dict[key][1]
                step = self.scenario_dict[key][2]
                float_flag = False
                if min_value < 1 or step < 1:
                    min_value = int(min_value * 100)
                    max_value = int(max_value * 100)
                    step = int(step * 100)
                    float_flag = True
                for value in range(min_value, max_value + step, step):
                    if float_flag:
                        value = value / 100
                    values_list.append(value)
                keys_list.append(key)
                characteristic_list.append(values_list)
        characteristic_list = list(itertools.product(*characteristic_list))
        for characteristic in characteristic_list:
            for key in keys_list:
                self.scenario_dict[key] = characteristic[keys_list.index(key)]
            self.scenario_generalization_list.append(self.scenario_dict)
        for key, values in self.scenario_dict['generalization_type'].items():
            if values == DataType.calculative.value:
                formula = eval(self.scenario_dict[key])
                '''需要修改，获取算式'''
                self.scenario_dict[key] = formula

        return self.scenario_generalization_list
