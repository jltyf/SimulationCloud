'''
    这个文件对新数据,可以生成直线和路口类型文件，对应的道路模型是China_Crossing_002.opt 和 China_UrbanRoad_014.opt
    China_UrbanRoad_014.opt 道路是北向的
'''
import traceback

from flask import Flask, request
from gevent import pywsgi
import math
import os
import sys
import shutil

sys.path.append('/SimulationCloud/')

import json
import warnings
import pandas as pd
from minio import Minio
from multiprocessing import Pool
from Generalization.serialization.scenario_serialization_web import ScenarioData
from Generalization.trail import Trail
from Generalization.utils import dump_json, formatThree, change_CDATA, get_plt, upload_xosc
from enumerations import TrailType, RoadType, ObjectType
from utils import get_cal_model, generateFinalTrail, getXoscPosition, trailModify, getLabel, Point
from configparser import ConfigParser
from openx import Scenario
from log.log_set import Loggers

warnings.filterwarnings("ignore")
pd.set_option('max_colwidth', 100)
# pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
cfg = ConfigParser()
cfg.read("../setting.ini")
setting_data = dict(cfg.items("pro"))
model_data = dict(cfg.items("model path"))
absPath = setting_data['data path']
client = Minio(
    endpoint=setting_data['endpoint'],
    access_key=setting_data['access key'],
    secret_key=setting_data['secret key'],
    secure=False
)
app = Flask(import_name=__name__)


def generalization(scenario_data, single_scenario, car_trail_data, ped_trail_data, trails_json_dict, scenario_index):
    if not os.path.exists(setting_data['scenario path']):
        os.mkdir(setting_data['scenario path'])
    ego_trails_list = list()
    # 根据自车场景速度情况选择轨迹
    ego_trail_section = 0
    rotate_tuple = ('ego_e', 'ego_n'), ('left_e', 'left_n'), ('right_e', 'right_n')
    for ego_speed_status in single_scenario['ego_velocity_status']:
        trail_type = TrailType.ego_trail
        ego_delta_col = 'ego_e'  # 因轨迹航向角的微小偏移所做的微调，选择的列'ego_e'通过道路模型确定
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
                                 start_point, ego_delta_col)
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

    else:
        print(scenario_data['sceneId'], "ego没有符合条件的轨迹, 失败")

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

                # 因轨迹航向角的微小偏移所做的微调，选择的列'ego_e'和自车保持一致
                if init_h % 180 == 0:
                    obj_delta_col = ego_delta_col
                elif init_h % 90 == 0:
                    obj_delta_col = 'ego_n'
                else:
                    obj_delta_col = None

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
                                            rotate_tuple, start_point, obj_delta_col, object_index)
                if len(object_trail_slices.position) > 0:
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

            else:
                print(scenario_data['sceneId'], "obs没有符合条件的轨迹")

            object_position_list.append(object_trail)
    # 转化仿真场景路径点, 生成仿真场景文件
    offset_h = 90  # 因匹配泛化道路模型要做的h偏移量 China_UrbanRoad_014直路:90 China_Crossing_002十字路口:90
    offset_z = 0
    root_path = setting_data['generalization models path']

    # 根据不同的道路模型设置偏移量
    if single_scenario['scenario_road_type'] == RoadType.city_straight.value:
        offset_x = 7  # 因匹配泛化道路模型要做的e偏移量 China_UrbanRoad_014直路:7 China_Crossing_002十字路口:5.5
        offset_y = 0  # 因匹配泛化道路模型要做的n偏移量 China_UrbanRoad_014直路:0 China_Crossing_002十字路口:-65
        xodr_path = root_path + '/' + model_data['city straight xodr']
        osgb_path = root_path + '/' + model_data['city straight osgb']
    elif single_scenario['scenario_road_type'] == RoadType.city_crossroads.value:
        offset_x = 5.5
        offset_y = -63.5
        xodr_path = root_path + '/' + model_data['city crossroads xodr']
        osgb_path = root_path + '/' + model_data['city crossroads osgb']
    elif single_scenario['scenario_road_type'] == RoadType.city_curve_left.value or \
            single_scenario['scenario_road_type'] == RoadType.city_curve_right.value:
        radius = abs(int(single_scenario['scenario_radius_curvature'][0]))
        motion = single_scenario['ego_trajectory']
        if '6' in motion:
            index = motion.index('6')
            if radius == 150:
                offset_x = 214.2
                offset_y = 81.6
                xodr_path = root_path + '/' + model_data['city curve left 150 xodr']
                osgb_path = root_path + '/' + model_data['city curve left 150 osgb']
            elif radius == 300:
                offset_x = 213.2
                offset_y = -68.57
                xodr_path = root_path + '/' + model_data['city curve left 300 xodr']
                osgb_path = root_path + '/' + model_data['city curve left 300 osgb']
            elif radius == 500:
                offset_x = 213.7
                offset_y = -268.5
                xodr_path = root_path + '/' + model_data['city curve left 500 xodr']
                osgb_path = root_path + '/' + model_data['city curve left 500 osgb']
        elif '7' in motion:
            index = motion.index('7')
            offset_x = -200.6
            if radius == 150:
                offset_y = 79.58
                xodr_path = root_path + '/' + model_data['city curve right 150 xodr']
                osgb_path = root_path + '/' + model_data['city curve right 150 osgb']
            elif radius == 300:
                offset_y = -70.38
                xodr_path = root_path + '/' + model_data['city curve right 300 xodr']
                osgb_path = root_path + '/' + model_data['city curve right 300 osgb']
            elif radius == 500:
                xodr_path = root_path + '/' + model_data['city curve right 500 xodr']
                osgb_path = root_path + '/' + model_data['city curve right 500 osgb']
                offset_y = -326.54
        # 分段弯道
        if len(motion) > 1:
            for trail in ego_trails_list[0:index]:
                offset_x -= (trail.iloc[-1]['ego_e'] - trail.iloc[0]['ego_e'])
                offset_y -= (trail.iloc[-1]['ego_n'] - trail.iloc[0]['ego_n'])
    ego_points, egotime = getXoscPosition(ego_trail, 'Time', 'ego_e', 'ego_n', 'headinga', offset_x, offset_y,
                                          offset_h, offset_z)  # 初始轨迹朝向与道路方向一致
    # ego_points, egotime = getXoscPosition(ego_trail, 'Time', 'ego_n', 'ego_e', 'headinga', offset_x, offset_y, offset_h) # 初始轨迹朝向与道路方向垂直
    object_points = []
    trail_motion_time_count = 0
    if object_position_list:
        for obsL in range(len(object_position_list)):
            motion = single_scenario['obs_trajectory'][object_index]
            obj_distance_y = float(single_scenario['obs_start_x'][object_index])
            obj_distance_x = float(single_scenario['obs_start_y'][object_index])
            if '6' in motion or '7' in motion:
                offset_y -= obj_distance_y
                offset_x -= obj_distance_x
            if '0' == motion and (
                    single_scenario['scenario_road_type'] == RoadType.city_curve_left.value or single_scenario[
                'scenario_road_type'] == RoadType.city_curve_right.value):
                offset_y = obj_distance_y - (radius - 150) * 1.5
                if single_scenario['scenario_road_type'] == RoadType.city_curve_right.value and radius == 500:
                    offset_y -= 50
            #     offset_x = obj_distance_x
            obs_points, obs_time = getXoscPosition(object_position_list[obsL], 'Time', 'ego_e', 'ego_n',
                                                   'headinga', offset_x, offset_y, offset_h, offset_z)
            if '6' in motion or '7' in motion:
                # 根据车速和目标车初始位置计算出目标车移动这段距离需要的时间
                trail_motion_time_count = int(round(
                    (abs(obj_distance_y) * 3.6 / float(single_scenario['obs_start_velocity'][object_index])),
                    1) * 10)
                del obs_points[0:trail_motion_time_count]
                del obs_time[0:trail_motion_time_count]
                obs_time[:] = [round(x - trail_motion_time_count / 10, 2) for x in obs_time]
            object_points.append((obs_points, obs_time))
            # object_points.append(getXoscPosition(object_position_list[obsL], 'Time', 'ego_n', 'ego_e', 'headinga', offset_x, offset_y, offset_h)) # 初始轨迹朝向与道路方向垂直
    if not trail_motion_time_count == 0:
        ego_points = ego_points[:len(ego_points) - trail_motion_time_count]
        egotime = egotime[:len(egotime) - trail_motion_time_count]
    sceperiod = math.ceil(egotime[-1] - egotime[0])
    s = Scenario(ego_points, object_points, egotime, sceperiod, single_scenario, absPath, xodr_path, osgb_path)
    s.print_permutations()
    output_path = os.path.join(setting_data['scenario path'],
                               scenario_data['sceneId'] + '_' + str(scenario_index))
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    files = s.generate(output_path)
    print(files)
    if 'PCW' in scenario_data['sceneId'] or '行人' in scenario_data['scenarioResume']:
        change_CDATA(files[0][0])  # 行人场景特例，对xosc文件内的特殊字符做转换

    # get_plt(ego_trail, object_position_list)  # 查看生成得自车轨迹 测试用
    # 生成每个场景的描述文件 json
    getLabel(output_path, scenario_data['sceneId'], scenario_data['scenarioName'])
    # 上传到minio
    minio_path = '批量泛化场景/' + single_scenario['uu_id'] + '/' + scenario_data['sceneId'].split('_')[0] + '/' + \
                 scenario_data['sceneId'] + '/' + os.path.basename(files[0][0])
    try:
        upload_xosc(client, setting_data['bucket name'], minio_path, files[0][0])
        result_dict = {
            'osgbAddress': osgb_path,
            'xodrAddress': xodr_path,
            'xoscAddress': minio_path,
        }
        return result_dict
    except:
        return 'minioE'


@app.route("/test_1.0", methods=["POST"])
def parsingConfigurationFile():
    scenario_data = json.loads(request.get_data(as_text=True))  # 获取 JSON 数据
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
    print(scenario_data['sceneId'], 'Start')
    try:
        scenario = ScenarioData(scenario_data)
        scenario_list = scenario.get_scenario_model()
        scenario_index = 0
        result_list = list()
        process_list = list()
    except Exception as e:
        error_msg = traceback.format_exc()
        log = Loggers()
        log.logger.info(f'错误类型:泛化入参错误,错误信息:{error_msg},错误模板:{scenario_data["sceneId"]}')
        response = {'success': False,
                    'code': 101,
                    'message': '传入的泛化参数错误，泛化失败!',
                    'params': None}
        return response
    try:
        with Pool(processes=int(setting_data['process number'])) as executor:
            for single_scenario in scenario_list:
                single_scenario, range_flag = get_cal_model(single_scenario)
                # 如果需要泛化的值不在不等式的范围内，此条数据作废
                if not range_flag:
                    continue
                process = executor.apply_async(generalization,
                                               (scenario_data, single_scenario, car_trail_data, ped_trail_data,
                                                trails_json_dict, scenario_index))
                scenario_index += 1
                process_list.append(process)
            for result in process_list:
                if result.get():
                    if result.get() == 'minioE':
                        response = {'success': False,
                                    'code': 104,
                                    'message': '泛化结束后minio上传文件失败，请检查配置文件!',
                                    'params': None}
                        return response
                    else:
                        result_list.append(result.get())

        if len(result_list) < 1:
            response = {'success': False,
                        'code': 103,
                        'message': '未泛化出场景,请检查输入参数合理性!',
                        'params': None}
        else:
            response = {'success': True,
                        'code': 200,
                        'message': '请求成功!',
                        'params': result_list}
            shutil.rmtree(setting_data['scenario path'])
        return response
    except Exception as e:
        error_msg = traceback.format_exc()
        log = Loggers()
        log.logger.info(f'错误类型:场景生成失败,错误信息:{error_msg},错误模板:{scenario_data["sceneId"]}')
        response = {'success': False,
                    'code': 102,
                    'message': '场景生成失败!',
                    'params': None}
        return response


@app.route("/format", methods=["GET"])
def format_files():
    data = json.loads(request.data)
    first_time = data['first_time']
    file_time = data['file']
    root_path = '/mnt/disk001/data/1+x/'
    new_dir = os.path.join(root_path, first_time)
    sc_path = os.path.join(new_dir, 'Scenarios')
    if not os.path.exists(first_time):
        os.mkdir(new_dir)

        xodr_path = os.path.join(new_dir, 'XODR')
        osgb_path = os.path.join(new_dir, 'OSGB')
        os.mkdir(new_dir)
        os.mkdir(sc_path)
        os.mkdir(xodr_path)
        os.mkdir(osgb_path)
        od_path = '/mnt/disk001/od'
        xodr = os.path.join(od_path, 'taiheqiao_1227_4.xodr')
        osgb = os.path.join(od_path, 'thq_dayou_1229_1.opt.osgb')
        shutil.copy(xodr, xodr_path)
        shutil.copy(osgb, osgb_path)
    second_path = os.path.join(sc_path, file_time)
    xosc_path = os.path.join(root_path, file_time + '.xosc')
    json_path = os.path.join(root_path, 'description.json')
    real_video = os.path.join(root_path, 'realVideo.mp4')
    simulation_path = os.path.join(root_path, 'simulation.mp4')
    shutil.copy(xosc_path, second_path)
    shutil.copy(json_path, second_path)
    shutil.copy(real_video, second_path)
    shutil.copy(simulation_path, second_path)

    response = {'success': True,
                'code': 200,
                'message': '请求成功!'}
    os.remove(xosc_path)
    os.remove(json_path)
    os.remove(real_video)
    os.remove(simulation_path)
    return response


if __name__ == "__main__":
    server = pywsgi.WSGIServer(
        ('0.0.0.0', 5001), app
    )
    server.serve_forever()
