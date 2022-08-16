import ast
import copy
import itertools

from enumerations import DataType, RoadType


class ScenarioData(object):
    def __init__(self, scenario_series):
        self.scenario_generalization_list = list()
        self.scenario_dict = dict()
        # 需要泛化的静态元素(枚举类型),如果需要在此添加
        self.scenario_dict['generalization_list'] = ['scenario_weather', 'scenario_time', 'scenario_radius_curvature']
        self.scenario_dict['scene_id'] = scenario_series['场景编号']
        self.scenario_dict['scenario_name'] = scenario_series['场景名称']
        self.scenario_dict['ego_start_x'] = scenario_series['自车初始x坐标']
        self.scenario_dict['ego_start_y'] = scenario_series['自车初始y坐标']
        self.scenario_dict['scenario_resume'] = scenario_series['场景简述']
        self.scenario_dict['scenario_weather'] = str(scenario_series['天气情况']).split(',')
        self.scenario_dict['scenario_time'] = str(scenario_series['场景发生时间']).split(',')
        self.scenario_dict['scenario_vehicle_model'] = scenario_series['车辆模型']
        self.scenario_dict['scenario_road_type'] = scenario_series['道路类型']
        self.scenario_dict['ego_start_velocity'] = scenario_series['自车初始速度V0(km/h)']
        self.scenario_dict['ego_heading_angle'] = str(scenario_series['自车航向角'])
        self.scenario_dict['ego_velocity_status'] = str(scenario_series['自车行驶速度状态'])
        self.scenario_dict['ego_trajectory'] = str(scenario_series['自车轨迹形态'])
        self.scenario_dict['ego_duration_time'] = str(scenario_series['自车轨迹持续时间(s)'])
        self.scenario_dict['ego_velocity_time'] = ast.literal_eval(scenario_series['自车速度分段持续时间'])
        self.scenario_dict['ego_trajectory_time'] = ast.literal_eval(scenario_series['自车轨迹形态分段持续时间'])
        # 只有弯道时才起效果
        if self.scenario_dict['scenario_road_type'] == RoadType.city_curve_left.value or \
                self.scenario_dict['scenario_road_type'] == RoadType.city_curve_right.value:
            self.scenario_dict['scenario_radius_curvature'] = str(scenario_series['车道线曲率半径']).split(',')
        self.scenario_dict['generalization_type'] = ast.literal_eval(scenario_series['泛化标志位'])
        if str(scenario_series['目标初始x坐标']):
            self.scenario_dict['obs_start_x'] = str(scenario_series['目标初始x坐标']).split(';')
            self.scenario_dict['obs_start_y'] = str(scenario_series['目标初始y坐标']).split(';')
            self.scenario_dict['obs_start_velocity'] = str(scenario_series['目标初始速度V1(km/h)']).split(';')
            self.scenario_dict['obs_lateral_acceleration'] = str(scenario_series['目标物最大横向加速度(m/s²)']).split(';')
            self.scenario_dict['obs_longitudinal_acceleration'] = str(scenario_series['目标物最大纵向加速度(m/s²)']).split(';')
            self.scenario_dict['obs_velocity_status'] = str(scenario_series['目标行驶速度状态']).split(';')
            self.scenario_dict['obs_trajectory'] = str(scenario_series['目标轨迹形态']).split(';')
            self.scenario_dict['obs_duration_time'] = str(scenario_series['目标轨迹持续时间(s)']).split(';')
            self.scenario_dict['obs_trail_time'] = str(scenario_series['目标轨迹形态分段持续时间(s)']).split(';')
            self.scenario_dict['obs_heading_angle_rel'] = str(scenario_series['目标物相对自车航向角']).split(';')
            self.scenario_dict['obs_velocity_time'] = str(scenario_series['目标速度分段持续时间(s)']).split(';')
            self.scenario_dict['obs_type'] = str(scenario_series['目标物类型']).split(';')
        else:
            # 在没有目标物的情况下,此列为空值
            self.scenario_dict['obs_start_x'] = list()

    def get_scenario_model(self):
        characteristic_list = list()
        keys_list = list()
        lac_index = None
        long_index = None
        if self.scenario_dict['generalization_type']:
            for key, values in self.scenario_dict['generalization_type'].items():
                obj_param = list()
                if values > 10:
                    for obj_index in range(len(str(values))):
                        obj_param.append(int(str(values)[obj_index]))
                else:
                    obj_param = [values]
                for obj_index in range(len(obj_param)):
                    values_list = list()
                    key_name = f'{key}' + f'-{obj_index}'
                    values = obj_param[obj_index]
                    if values == DataType.static.value:
                        continue
                    if key not in self.scenario_dict['generalization_list'] and values != DataType.calculative.value:
                        # if values == DataType.generalizable.value or values == DataType.generalizable_limit.value:
                        # # 备用请勿删除
                        # _ = ast.literal_eval(str(self.scenario_dict[key][0]))
                        if values == DataType.generalizable_limit.value:
                            temp_limit_data = self.scenario_dict[key][obj_index].split('|')
                            self.scenario_dict[key][obj_index] = temp_limit_data[0]
                            self.scenario_dict[key + f'{obj_index}_limit'] = temp_limit_data[1]
                        try:
                            generalization_list = ast.literal_eval(self.scenario_dict[key])
                        except:
                            generalization_list = ast.literal_eval(self.scenario_dict[key][obj_index])
                        if not isinstance(generalization_list, list):
                            continue
                        for i in generalization_list:
                            if isinstance(i, list):
                                if 'lateral' in key:
                                    lac_index = generalization_list.index(i)
                                    generalization_list = i
                                elif 'longitudinal' in key:
                                    long_index = generalization_list.index(i)
                                    generalization_list = i
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
                        keys_list.append(key_name)
                        characteristic_list.append(values_list)
                    else:
                        if values == DataType.generalizable.value:
                            keys_list.append(key_name)
                            characteristic_list.append(self.scenario_dict[key])

        if not characteristic_list:
            return [self.scenario_dict]
        # 只有多个参数需要泛化的情况下需要做笛卡尔积
        if len(keys_list) > 1:
            characteristic_list = list(itertools.product(*characteristic_list))
        else:
            characteristic_list = characteristic_list[0]
        for characteristic in characteristic_list:
            temp_data = copy.deepcopy(self.scenario_dict)
            for key in keys_list:
                key_name = key.split('-')[0]
                key_index = int(key.split('-')[1])
                if (lac_index or long_index) and 'lateral' in key:
                    acc_value = ast.literal_eval(temp_data[key_name][key_index])
                    acc_value[lac_index] = characteristic[keys_list.index(key)]
                    generalization_value = [str(acc_value)]
                elif (lac_index or long_index) and 'longitudinal' in key:
                    acc_value = ast.literal_eval(temp_data[key_name][key_index])
                    acc_value[long_index] = characteristic[keys_list.index(key)]
                    generalization_value = str(acc_value)
                else:
                    if len(keys_list) == 1:
                        generalization_value = str(characteristic)
                    else:
                        generalization_value = str(characteristic[keys_list.index(key)])
                    # if 'ego' not in key:
                    #     generalization_value = [generalization_value]
                if 'acceleration' in key:
                    temp_data[key_name][key_index] = eval(generalization_value)
                elif 'ego' in key:
                    temp_data[key_name] = float(generalization_value)
                else:
                    temp_data[key_name][key_index] = float(generalization_value)
            self.scenario_generalization_list.append(temp_data)

        return self.scenario_generalization_list
