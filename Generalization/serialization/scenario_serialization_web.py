import ast
import itertools

from enumerations import DataType, RoadType


class ScenarioData(object):
    def __init__(self, scenario_data):
        self.scenario_generalization_list = list()
        self.scenario_dict = dict()
        # 需要泛化的静态元素(枚举类型),如果需要在此添加
        self.scenario_dict['generalization_list'] = ['scenario_weather', 'scenario_time', 'scenario_radius_curvature']
        self.scenario_dict['scene_id'] = scenario_data['sceneId']
        self.scenario_dict['scenario_name'] = scenario_data['scenarioName']
        self.scenario_dict['ego_start_x'] = scenario_data['egoStartX']
        self.scenario_dict['ego_start_y'] = scenario_data['egoStartY']
        self.scenario_dict['scenario_resume'] = scenario_data['scenarioResume']
        self.scenario_dict['scenario_weather'] = str(scenario_data['scenarioWeather']).split(',')
        self.scenario_dict['scenario_time'] = str(scenario_data['scenarioTime']).split(',')
        self.scenario_dict['scenario_vehicle_model'] = scenario_data['scenarioVehicleModel']
        self.scenario_dict['scenario_road_type'] = int(scenario_data['scenarioRoadType'])
        self.scenario_dict['ego_start_velocity'] = scenario_data['egoStartVelocity']
        self.scenario_dict['ego_heading_angle'] = str(scenario_data['egoHeadingAngle'])
        self.scenario_dict['ego_velocity_status'] = str(scenario_data['egoVelocityStatus'])
        self.scenario_dict['ego_trajectory'] = str(scenario_data['egoTrajectory'])
        self.scenario_dict['ego_duration_time'] = str(scenario_data['egoDurationTime'])
        self.scenario_dict['ego_velocity_time'] = ast.literal_eval(scenario_data['egoVelocityTime'])
        self.scenario_dict['ego_trajectory_time'] = ast.literal_eval(scenario_data['egoTrajectoryTime'])
        # 只有弯道时才起效果
        if self.scenario_dict['scenario_road_type'] == RoadType.city_curve_left.value or \
                self.scenario_dict['scenario_road_type'] == RoadType.city_curve_right.value:
            self.scenario_dict['scenario_radius_curvature'] = str(scenario_data['scenarioRadiusCurvature']).split(',')
        self.scenario_dict['generalization_type'] = ast.literal_eval(scenario_data['generalizationType'])
        if str(scenario_data['obsStartX']):
            self.scenario_dict['obs_start_x'] = str(scenario_data['obsStartX']).split(';')
            self.scenario_dict['obs_start_y'] = str(scenario_data['obsStartY']).split(';')
            self.scenario_dict['obs_start_velocity'] = str(scenario_data['obsStartVelocity']).split(';')
            self.scenario_dict['obs_lateral_acceleration'] = str(scenario_data['obsLateralAcceleration']).split(';')
            self.scenario_dict['obs_longitudinal_acceleration'] = str(scenario_data['obsLongitudinalAcceleration']).split(';')
            self.scenario_dict['obs_velocity_status'] = str(scenario_data['obsVelocityStatus']).split(';')
            self.scenario_dict['obs_trajectory'] = str(scenario_data['obsTrajectory']).split(';')
            self.scenario_dict['obs_duration_time'] = str(scenario_data['obsDurationTime']).split(';')
            self.scenario_dict['obs_trail_time'] = str(scenario_data['obsTrailTime']).split(';')
            self.scenario_dict['obs_heading_angle_rel'] = str(scenario_data['obsHeadingAngleRel']).split(';')
            self.scenario_dict['obs_velocity_time'] = str(scenario_data['obsVelocityTime']).split(';')
        else:
            # 在没有目标物的情况下,此列为空值
            self.scenario_dict['obs_start_x'] = list()

    def get_scenario_model(self):
        characteristic_list = list()
        keys_list = list()
        other_obj_dict = dict()
        lac_index = None
        long_index = None
        if self.scenario_dict['generalization_type']:
            for key, values in self.scenario_dict['generalization_type'].items():
                values_list = list()
                if key not in self.scenario_dict['generalization_list']:
                    if values == DataType.generalizable.value or values == DataType.generalizable_limit.value:
                        # # 备用请勿删除
                        # _ = ast.literal_eval(str(self.scenario_dict[key][0]))
                        if values == DataType.generalizable_limit.value:
                            temp_limit_data = self.scenario_dict[key][0].split('|')
                            self.scenario_dict[key][0] = temp_limit_data[0]
                            self.scenario_dict[key + '_limit'] = temp_limit_data[1]
                        try:
                            if 'obs' in key:
                                if isinstance(eval(str(self.scenario_dict[key][0])), list):
                                    other_obj_dict[key] = self.scenario_dict[key][1:]
                                generalization_list = ast.literal_eval((self.scenario_dict[key][0]))
                            else:
                                generalization_list = ast.literal_eval(str(self.scenario_dict[key]))
                        except:
                            if isinstance(eval(str(self.scenario_dict[key][0])), list):
                                other_obj_dict[key] = self.scenario_dict[key][1:]
                                generalization_list = eval(self.scenario_dict[key][0])
                            else:
                                generalization_list = self.scenario_dict[key]
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
                        keys_list.append(key)
                        characteristic_list.append(values_list)
                else:
                    if values == DataType.generalizable.value:
                        keys_list.append(key)
                        characteristic_list.append(self.scenario_dict[key])

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
                if (lac_index or long_index) and 'lateral' in key:
                    acc_value = ast.literal_eval(temp_data[key][0])
                    acc_value[lac_index] = characteristic[keys_list.index(key)]
                    generalization_value = [str(acc_value)]
                elif (lac_index or long_index) and 'longitudinal' in key:
                    acc_value = ast.literal_eval(temp_data[key][0])
                    acc_value[long_index] = characteristic[keys_list.index(key)]
                    generalization_value = str(acc_value)
                elif other_obj_dict and key in other_obj_dict.keys():
                    if isinstance(characteristic, tuple):
                        generalization_value = [str(characteristic[keys_list.index(key)]), *other_obj_dict[key]]
                    else:
                        generalization_value = [str(characteristic), *other_obj_dict[key]]
                else:
                    if len(keys_list) == 1:
                        generalization_value = str(characteristic)
                    else:
                        generalization_value = str(characteristic[keys_list.index(key)])
                    if 'ego' not in key:
                        generalization_value = [generalization_value]
                if 'acceleration' in key:
                    temp_data[key][0] = generalization_value
                else:
                    temp_data[key] = generalization_value
            self.scenario_generalization_list.append(temp_data)

        return self.scenario_generalization_list

    def get_limit_data(self, limit_value, key):
        limit_data = limit_value.split('|')
        self.scenario_dict[key + 'limit'] = limit_data[1]
        return limit_data[0]
