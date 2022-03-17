'''
    这个文件对新数据,可以生成直线和路口类型文件，对应的道路模型是China_Crossing_002.opt 和 China_UrbanRoad_014.opt
    China_UrbanRoad_014.opt 道路是北向的
'''
import math
import os
import json
import pandas as pd
from Generalization.serialization.scenario_serialization import ScenarioData
from Generalization.trail import Trail
from Generalization.utils import dump_json
from enumerations import TrailType
from utils import get_cal_model, generateFinalTrail, getXoscPosition, trailModify, getLabel, Point
from openx import Scenario, change_CDATA
import warnings

warnings.filterwarnings("ignore")


def parsingConfigurationFile(absPath, ADAS_module):
    car_trail = os.path.join(absPath + '/trails/', 'CarTrails_Merge.csv')
    ped_trail = os.path.join(absPath + '/trails/', 'PedTrails_Merge.csv')
    json_trail = os.path.join(absPath + '/trails/', 'Trails_Merge.json')
    with open(json_trail) as f:
        trails_json_dict = json.load(f)
    trails_json_dict = dump_json(trails_json_dict)
    fileCnt = 0
    car_trail_data = pd.read_csv(car_trail)
    ped_trail_data = pd.read_csv(ped_trail)

    # 按功能列表分别读取不同的功能配置表
    parm_data = pd.read_excel(os.path.join(absPath + '/trails/', "配置参数表样例0210.xlsx"),
                              sheet_name=ADAS_module, keep_default_na=False, engine='openpyxl')
    ADAS_list = [ADAS for ADAS in ADAS_module]
    scenario_df = [parm_data[scenario_list] for scenario_list in ADAS_list][0]
    for index, scenario_series in scenario_df.iterrows():
        print(scenario_series['场景编号'], 'Start')
        scenario = ScenarioData(scenario_series)
        scenario_list = scenario.get_scenario_model()
        scenario_index = 0
        for single_scenario in scenario_list:
            single_scenario = get_cal_model(single_scenario)
            ego_trails_list = list()
            # 根据自车场景速度情况选择轨迹
            ego_trail_section = 0
            rotate_tuple = ('ego_e', 'ego_n'), ('left_e', 'left_n'), ('right_e', 'right_n')
            for ego_speed_status in single_scenario['ego_velocity_status']:
                trail_type = TrailType.ego_trail
                if ego_trail_section == 0:
                    start_speed = float(single_scenario['ego_start_velocity'])
                    heading_angle = float(single_scenario['ego_heading_angle'])
                    start_point = Point(0, 0)
                else:
                    start_speed = float(ego_trails_list[-1].iloc[-1]['vel_filtered'])
                    heading_angle = float(ego_trails_list[-1].iloc[-1]['headinga'])
                    start_point = Point(ego_trails_list[-1].iloc[-1]['ego_e'], ego_trails_list[-1].iloc[-1]['ego_n'])

                ego_trail_slices = Trail(trail_type, car_trail_data, ped_trail_data, trails_json_dict, ego_speed_status,
                                         single_scenario, ego_trail_section, start_speed, heading_angle, rotate_tuple,
                                         start_point)
                if ego_trail_slices:
                    ego_trails_list.append(ego_trail_slices.position)
                else:
                    print(f'ego第{ego_trail_section + 1}段轨迹没有生成', ego_trail_section)
                ego_trail_section += 1

            if ego_trails_list:
                # 拼接自车轨迹
                init_e = float(single_scenario['ego_start_x'])
                init_n = float(single_scenario['ego_start_y'])
                init_h = float(single_scenario['ego_heading_angle'])
                ego_trail = generateFinalTrail('ego', ego_trails_list, 'ego_e', 'ego_n', 'headinga', rotate_tuple,
                                               init_e=init_e, init_n=init_n, init_h=init_h)
                # ego_trail = ego_trail.drop_duplicates(subset=['ego_e', 'ego_n', 'headinga'], keep='first') # 静止轨迹会被删掉
                # ego_trail = ego_trail.reset_index(drop=True)
                # 因轨迹航向角的微小偏移所做的微调，选择的列'ego_e'通过道路模型确定
                ego_delta_col = 'ego_e'
                delta_h = abs(ego_trail.at[len(ego_trail) - 1, 'headinga'] - ego_trail.at[0, 'headinga'])
                if delta_h > 0.5:
                    ego_trail = trailModify(ego_trail, 'Time', ego_delta_col, 'headinga')
            else:
                print(scenario_series['场景编号'], "ego没有符合条件的轨迹, 失败")

            object_position_list = list()  # 二维数组,第一维度为不同的目标物，第二维度为相同目标物的分段轨迹形态
            if single_scenario['obs_start_x']:
                for object_index in range(len(single_scenario['obs_start_x'])):
                    object_status = single_scenario['obs_velocity_status'][object_index]
                    object_trail_list = list()

                    # 根据目标车场景速度情况选择轨迹
                    object_trail_section = 0
                    for object_split_status in object_status:
                        trail_type = TrailType.vehicle_trail
                        if object_index == 0 and '行人' in single_scenario['scenario_resume']:
                            trail_type = TrailType.ped_trail
                        if object_trail_section == 0:
                            start_speed = float(single_scenario['obs_start_velocity'][object_index])
                            heading_angle = float(single_scenario['obs_heading_angle_rel'][object_index])
                            start_point = Point(float(single_scenario['obs_start_x'][object_index]),
                                                float(single_scenario['obs_start_y'][object_index]))
                        else:
                            start_speed = float(object_trail_list[-1].iloc[-1]['vel_filtered'])
                            heading_angle = float(object_trail_list[-1].iloc[-1]['headinga'])
                            start_point = Point(object_trail_list[-1].iloc[-1]['ego_e'],
                                                object_trail_list[-1].iloc[-1]['ego_n'])

                        object_trail_slices = Trail(trail_type, car_trail_data, ped_trail_data, trails_json_dict,
                                                    object_split_status,
                                                    single_scenario, object_trail_section, start_speed, heading_angle,
                                                    rotate_tuple, start_point, object_index)
                        if object_trail_slices:
                            object_trail_list.append(object_trail_slices.position)
                        else:
                            print(f'object第{object_trail_section + 1}段轨迹没有生成', object_trail_section)
                        object_trail_section += 1

                    if object_trail_list:
                        # 拼接目标车轨迹
                        # init_e = float(single_scenario['obs_start_x'][object_index]) # 考虑车头朝向,初始车头朝向与道路方向一致
                        # init_n = float(single_scenario['obs_start_y'][object_index]) # 考虑车头朝向,初始车头朝向与道路方向一致
                        init_e = float(single_scenario['obs_start_y'][object_index])  # 考虑车头朝向,初始车头朝向与道路方向垂直
                        init_n = float(single_scenario['obs_start_x'][object_index])  # 考虑车头朝向,初始车头朝向与道路方向垂直
                        init_h = float(single_scenario['obs_heading_angle_rel'][object_index]) + float(
                            single_scenario['ego_heading_angle'])
                        object_trail = generateFinalTrail('object', object_trail_list, 'ego_e', 'ego_n', 'headinga',
                                                          rotate_tuple, init_e=init_e, init_n=init_n, init_h=init_h)
                        # 因轨迹航向角的微小偏移所做的微调，选择的列'ego_e'和自车保持一致
                        if init_h % 180 == 0:
                            obj_delta_col = ego_delta_col
                        elif init_h % 90 == 0:
                            obj_delta_col = 'ego_n'
                        else:
                            obj_delta_col = None

                        if obj_delta_col:
                            delta_h = abs(
                                object_trail.at[len(object_trail) - 1, 'headinga'] - object_trail.at[0, 'headinga'])
                            if delta_h > 0.5:
                                object_trail = trailModify(object_trail, 'Time', obj_delta_col, 'headinga')
                    else:
                        print(scenario_series['场景编号'], "obs没有符合条件的轨迹")

                    object_position_list.append(object_trail)

            # 转化仿真场景路径点, 生成仿真场景文件
            offset_x = 7  # 因匹配泛化道路模型要做的e偏移量
            offset_y = 0  # 因匹配泛化道路模型要做的n偏移量
            offset_h = 90  # 初始车头朝向和道路方向不一致，因此要调整h偏移量

            ego_points, egotime = getXoscPosition(ego_trail, 'Time', 'ego_e', 'ego_n', 'headinga', offset_x, offset_y,
                                                  offset_h)
            object_points = []
            if object_position_list:
                for obsL in range(len(object_position_list)):
                    object_points.append(
                        getXoscPosition(object_position_list[obsL], 'Time', 'ego_e', 'ego_n', 'headinga', offset_x,
                                        offset_y, offset_h))

            egoSpeed = 5  # 随意设的，不发挥作用
            sceperiod = math.ceil(egotime[-1] - egotime[0])
            s = Scenario(ego_points, object_points, 0, egotime, egoSpeed, 0, 0, 0, sceperiod)
            s.print_permutations()
            output_path = os.path.join(absPath + '/trails/', 'simulation_new',
                                       scenario_series['场景编号'] + '_' + str(scenario_index))
            files = s.generate(
                output_path)  # '/home/lxj/Documents/pyworkspace/data/trails/simulation_new/AEB_1-1_17/AEB_1-1_17.xosc'
            scenario_index += 1
            print(files)
            if 'PCW' in scenario_series['场景编号']:
                change_CDATA(files[0][0])  # 行人场景特例，对xosc文件内的特殊字符做转换

            # 生成每个场景的描述文件 json
            getLabel(output_path, scenario_series['场景编号'], scenario_series['场景名称'])

    print(fileCnt)


if __name__ == "__main__":
    parsingConfigurationFile("/home/lxj/Documents/pyworkspace/data", ['ALC-base'])
