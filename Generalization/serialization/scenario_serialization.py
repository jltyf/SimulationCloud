import ast
import itertools

from enumerations import DataType


class ScenarioData(object):
    def __init__(self, scenario_series):
        self.scenario_generalization_list = list()
        self.scenario_dict = dict()
        self.scenario_dict['scene_id'] = scenario_series['场景编号']
        self.scenario_dict['scenario_name'] = scenario_series['场景名称']
        self.scenario_dict['ego_start_x'] = scenario_series['自车初始x坐标']
        self.scenario_dict['ego_start_y'] = scenario_series['自车初始y坐标']
        self.scenario_dict['scenario_resume'] = scenario_series['场景简述']
        self.scenario_dict['ego_start_velocity'] = [scenario_series['自车初始速度V0(km/h)']]
        try:
            eval(self.scenario_dict['ego_start_velocity'][0])
        except:
            self.scenario_dict['ego_start_velocity'] = self.scenario_dict['ego_start_velocity'][0]
        self.scenario_dict['ego_heading_angle'] = str(scenario_series['自车航向角'])
        self.scenario_dict['ego_velocity_status'] = str(scenario_series['自车行驶速度状态'])
        self.scenario_dict['ego_trajectory'] = str(scenario_series['自车轨迹形态'])
        self.scenario_dict['ego_duration_time'] = str(scenario_series['自车轨迹持续时间(s)'])
        self.scenario_dict['ego_velocity_time'] = eval(scenario_series['自车速度分段持续时间'])
        self.scenario_dict['ego_trajectory_time'] = eval(scenario_series['自车轨迹形态分段持续时间'])
        self.scenario_dict['generalization_type'] = ast.literal_eval(scenario_series['泛化标志位'])
        # self.scenario_dict['scene_type'] = str(scenario_series['scene_type'])
        # self.scenario_dict['scene_description'] = str(scenario_series['scene_description'])
        # self.scenario_dict['expect_test_result'] = str(scenario_series['expect_test_result'])
        if str(scenario_series['目标初始x坐标']):
            self.scenario_dict['obs_start_x'] = str(scenario_series['目标初始x坐标']).split(';')
            self.scenario_dict['obs_start_y'] = str(scenario_series['目标初始y坐标']).split(';')
            self.scenario_dict['obs_start_velocity'] = str(scenario_series['目标初始速度V1(km/h)']).split(';')
            self.scenario_dict['obs_velocity_status'] = str(scenario_series['目标行驶速度状态']).split(';')
            self.scenario_dict['obs_trajectory'] = str(scenario_series['目标轨迹形态']).split(';')
            self.scenario_dict['obs_duration_time'] = str(scenario_series['目标轨迹持续时间(s)']).split(';')
            self.scenario_dict['obs_trail_time'] = str(scenario_series['目标轨迹形态分段持续时间(s)']).split(';')
            self.scenario_dict['obs_heading_angle_rel'] = str(scenario_series['目标物相对自车航向角']).split(';')
            self.scenario_dict['obs_velocity_time'] = str(scenario_series['目标速度分段持续时间(s)']).split(';')
            if self.scenario_dict['scenario_name'] in 'PCW':
                self.scenario_dict['ped_initial_position_x'] = str(scenario_series['目标初始x坐标']).split(';')
                self.scenario_dict['ped_initial_position_y'] = str(scenario_series['目标初始y坐标']).split(';')
                self.scenario_dict['ped_speed_status'] = str(scenario_series['目标行驶速度状态']).split(';')
                self.scenario_dict['ped_trajectory'] = str(scenario_series['目标轨迹形态']).split(';')
                self.scenario_dict['ped_speed_duration_time'] = str(scenario_series['目标速度分段持续时间(s)']).split(';')
                self.scenario_dict['pedT_trail_section_duration_time'] = str(scenario_series['目标轨迹形态分段持续时间(s)']).split(
                    ';')
                self.scenario_dict['ped_heading_angle_rel'] = str(scenario_series['目标物相对自车航向角']).split(',')
        else:
            # 在没有目标物的情况下,此列为空值
            self.scenario_dict['obs_start_x'] = list()

    def get_scenario_model(self):
        characteristic_list = list()
        keys_list = list()
        other_obj_dict = dict()
        for key, values in self.scenario_dict['generalization_type'].items():
            values_list = list()
            if values == DataType.generalizable.value:
                # # 备用请勿删除
                # _ = ast.literal_eval(str(self.scenario_dict[key][0]))
                if isinstance(ast.literal_eval(str(self.scenario_dict[key][0])), list):
                    other_obj_dict[key] = self.scenario_dict[key][1:]
                    generalization_list = eval(self.scenario_dict[key][0])
                else:
                    generalization_list = self.scenario_dict[key]
                min_value = generalization_list[0]
                max_value = generalization_list[1]
                step = generalization_list[2]
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

        if not characteristic_list:
            return [self.scenario_dict]
        # 只有多个参数需要泛化的情况下需要做笛卡尔积
        if len(keys_list) > 1:
            characteristic_list = list(itertools.product(*characteristic_list))
        else:
            characteristic_list = characteristic_list[0]
        for characteristic in characteristic_list:
            temp_data = self.scenario_dict.copy()
            for key in keys_list:
                if other_obj_dict[key]:
                    if isinstance(characteristic, tuple):
                        temp_data[key] = [str(characteristic[keys_list.index(key)]), *other_obj_dict[key]]
                    else:
                        temp_data[key] = [str(characteristic), *other_obj_dict[key]]
                else:
                    if 'ego' in key:
                        if len(keys_list) == 1:
                            temp_data[key] = str(characteristic)
                        else:
                            temp_data[key] = str(characteristic[keys_list.index(key)])
                    else:
                        if len(keys_list) == 1:
                            temp_data[key] = [str(characteristic)]
                        else:
                            temp_data[key] = [str(characteristic[keys_list.index(key)])]
            self.scenario_generalization_list.append(temp_data)

        return self.scenario_generalization_list
