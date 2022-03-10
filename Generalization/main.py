'''
    这个文件对新数据,可以生成直线和路口类型文件，对应的道路模型是China_Crossing_002.opt 和 China_UrbanRoad_014.opt
'''
import math
import os
import traceback
from datetime import datetime
import json
import pandas as pd
import copy
import numpy as np
import xml.etree.ElementTree as ET
from scenariogeneration import xodr
from scenariogeneration import xosc
from scenariogeneration import ScenarioGenerator
from scenariogeneration.xodr import RoadSide, Object, ObjectType, Dynamic, Orientation

from Generalization.serialization.scenario_serialization import ScenarioData
from Generalization.trail import Trail
from Generalization.utils import dump_json, get_connect_trail, get_adjust_trails
from enumerations import TrailType
from utils import concatTrails, corTransform_init, generateFinalTrail, getEgoPosition
from functools import reduce

unchanged_line_label_list = []
change_line_label_list = []
MaximumNumberNfSameTrajectories = 10  # 基础拼接轨迹的数量，一般是最终生成场景数的10倍
MaxFileNumber = 1  # 生成的最终场景数
NumberOfTracks = 1000
LaneWidth = 3
# json中得排序
StartTime = 1
StopTime = 2
StartHeadingIndex = 3
StopHeadingIndex = 4
StartSpeedIndex = 5
StopSpeedIndex = 6
LongituteTypeIndex = 7  # longituteType json文件中的位置
TrajectoryTypeIndex = 9  # lateralType json文件中的位置

CSVInXIndex = 4  # 轨迹文件中ego_e 列的位置
CSVInYIndex = 5  # 轨迹文件中ego_n 列的位置

BIsStitchingModificationSpeed = True


class ObsPosition():
    def __init__(self, time=0, ObjectID=0, ObjectType=0, x=0, y=0, h=0, vel=0):
        self.time = time
        self.ObjectID = ObjectID
        self.ObjectType = ObjectType
        self.y = float(y)
        self.x = float(x)
        self.h = h
        self.vel = vel


class Point():
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


# 创建道路旁静止的场景
def create_static_object(road, object_dict):
    for single_object in object_dict:
        for k, v in ObjectType.__members__.items():
            if k == single_object.attrib['type']:
                single_object.attrib['type'] = v
                break

        road_object = Object(
            s=single_object.attrib['s'],
            t=single_object.attrib['t'],
            Type=single_object.attrib['type'],
            dynamic=Dynamic.no,
            id=single_object.attrib['id'],
            name=single_object.attrib['name'],
            zOffset=single_object.attrib['zOffset'],
            validLength=single_object.attrib['validLength'],
            orientation=Orientation.none,
            length=single_object.attrib['length'],
            width=single_object.attrib['width'],
            height=single_object.attrib['height'],
            pitch=single_object.attrib['pitch'],
            roll=single_object.attrib['roll']
        )

        # 判断此object是否是重复的元素
        repeat = single_object.find('repeat')
        if repeat is not None:
            road.add_object_roadside(road_object_prototype=road_object, repeatDistance=0, side=RoadSide.left,
                                     tOffset=1.75)
            road.add_object_roadside(road_object_prototype=road_object, repeatDistance=0, side=RoadSide.right,
                                     tOffset=-1.755)
        else:
            road.add_object(road_object)
    return road


class Scenario(ScenarioGenerator):
    def __init__(self, gps, obs, ObjectID, gpsTime, egoSpeed, Speed, intersectime, augtype, sceperiod):
        ScenarioGenerator.__init__(self)
        self.gps = gps
        self.obs = obs
        self.gpsTime = gpsTime
        self.ObjectID = ObjectID
        self.egoSpeed = egoSpeed
        self.Speed = Speed
        self.intersectime = intersectime
        self.augtype = augtype
        self.sceperiod = sceperiod

    def road(self, **kwargs):
        positionEgo = self.gps
        planview = xodr.PlanView()

        lasth = float(positionEgo[0].h)
        for i in range(len(self.gps) - 1):
            x = 0.000001 if abs(positionEgo[i].x) < 0.000001 else positionEgo[i].x
            y = 0.000001 if abs(positionEgo[i].y) < 0.000001 else positionEgo[i].y
            nextx = 0.000001 if abs(positionEgo[i + 1].x) < 0.000001 else positionEgo[i + 1].x
            nexty = 0.000001 if abs(positionEgo[i + 1].y) < 0.000001 else positionEgo[i + 1].y

            if (i > 0) & (float(positionEgo[i].h - lasth) < -6):
                h = float(positionEgo[i].h) + 2 * math.pi
            elif (i > 0) & (float(positionEgo[i].h - lasth) > 6):
                h = float(positionEgo[i].h) - 2 * math.pi
            else:
                h = float(positionEgo[i].h)

            planview.add_fixed_geometry(xodr.Line(math.sqrt(math.pow(nextx - x, 2) + math.pow(nexty - y, 2))), x, y, h)
            lasth = h
        planview.add_fixed_geometry(xodr.Line(100), nextx, nexty, h)
        # create two different roadmarkings
        rm_solid = xodr.RoadMark(xodr.RoadMarkType.solid, 0.2)
        rm_dashed = xodr.RoadMark(xodr.RoadMarkType.broken, 0.2)

        # create simple lanes
        lanes = xodr.Lanes()
        lanesection1 = xodr.LaneSection(0, xodr.standard_lane(offset=1.75, rm=rm_dashed))
        lanesection1.add_left_lane(xodr.standard_lane(offset=3.5, rm=rm_dashed))
        lanesection1.add_left_lane(xodr.standard_lane(offset=3.5, rm=rm_dashed))
        lanesection1.add_left_lane(xodr.standard_lane(offset=3.5, rm=rm_solid))
        lanesection1.add_right_lane(xodr.standard_lane(offset=3.5, rm=rm_dashed))
        lanesection1.add_right_lane(xodr.standard_lane(offset=3.5, rm=rm_dashed))
        lanesection1.add_right_lane(xodr.standard_lane(offset=3.5, rm=rm_solid))
        lanes.add_lanesection(lanesection1)
        lanes.add_laneoffset(xodr.LaneOffset(a=1.75))

        road = xodr.Road(0, planview, lanes)
        odr = xodr.OpenDrive('myroad' + str(self.road_id))
        # 静态元素
        objects_list = []
        tree = ET.parse(os.getcwd() + '/models/static_object_models.xodr')
        root = tree.getroot()
        objects_dict = root.iter(tag='object')
        road = create_static_object(road, objects_dict)

        # road = create_static_object(road, object_id=0, object_type=ObjectType.railing, repeat_flag=1)
        odr.add_road(road)
        odr.adjust_roads_and_lanes()
        return odr

    # 获取距离
    def get_distance(self, pState, pEnd):
        '''
        get distance between two points
        ----------
        args:
            px (list): point X, (x, y)
            py (list): point Y, (x, y)
        ----------
        return:
            number: distance
        '''
        return ((pState.x - pEnd.x) ** 2 + (pState.y - pEnd.y) ** 2) ** 0.5

    def getH(self, point1, point2):
        h = math.atan2((point2.y - point1.y), (point2.x - point1.x))
        return h

    def scenario(self, **kwargs):
        road = xosc.RoadNetwork(self.road_file, scenegraph="/simulation0.osgb")

        catalog = xosc.Catalog()
        catalog.add_catalog('VehicleCatalog', 'Distros/Current/Config/Players/Vehicles')
        catalog.add_catalog('PedestrianCatalog', 'Distros/Current/Config/Players/Pedestrians')
        catalog.add_catalog('ControllerCatalog', 'Distros/Current/Config/Players/driverCfg.xml')

        pbb = xosc.BoundingBox(0.5, 0.5, 1.8, 2.0, 0, 0.9)
        bb = xosc.BoundingBox(2.1, 4.5, 1.8, 1.5, 0, 0.9)
        fa = xosc.Axle(0.5, 0.6, 1.8, 3.1, 0.3)
        ba = xosc.Axle(0, 0.6, 1.8, 0, 0.3)
        red_veh = xosc.Vehicle('Audi_A3_2009_black', xosc.VehicleCategory.car, bb, fa, ba, 69.444, 200, 10)
        white_veh = xosc.Vehicle('Audi_A3_2009_red', xosc.VehicleCategory.car, bb, fa, ba, 69.444, 200, 10)
        male_ped = xosc.Pedestrian('Christian', 'male_adult', 70, xosc.PedestrianCategory.pedestrian, pbb)

        prop = xosc.Properties()
        cnt = xosc.Controller('DefaultDriver', prop)
        cnt2 = xosc.Controller('No Driver', prop)

        egoname = 'Ego'
        entities = xosc.Entities()
        entities.add_scenario_object(egoname, red_veh, cnt)
        objname = 'Player'

        if self.augtype != 7:

            # object car model
            for i in range(len(self.obs)):
                row = self.obs[i]
                entities.add_scenario_object(objname + str(i), white_veh, cnt2)

        elif self.augtype == 7:

            # pedestrian model
            for i in range(len(self.obs)):
                row = self.obs[i]
                entities.add_scenario_object(objname + str(i), male_ped)

        positionEgo = self.gps
        positionObj = self.obs
        init = xosc.Init()
        step_time = xosc.TransitionDynamics(xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 0)
        step_time1 = xosc.TransitionDynamics(xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 1)
        egospeed = xosc.AbsoluteSpeedAction(self.egoSpeed, step_time)
        objspeed = xosc.AbsoluteSpeedAction(self.Speed, step_time1)

        # ego car
        # ego_init_h = self.getH(positionEgo[0],positionEgo[1]) if self.get_distance(positionEgo[0],positionEgo[1]) > 0.5 else positionEgo[0].h
        ego_init_h = positionEgo[0].h
        init.add_init_action(egoname, xosc.TeleportAction(
            xosc.WorldPosition(x=0.000001, y=0.000001, z=0, h=ego_init_h, p=0, r=0)))
        init.add_init_action(egoname, egospeed)

        # obj car
        for i in range(len(positionObj)):
            row = positionObj[i]
            name = objname + str(i)
            x = -10000
            y = 10000
            # x = 0.000001 if (abs(float(row[0].x)) < 0.000001) else float(row[0].x)
            # y = 0.000001 if (abs(float(row[0].y)) < 0.000001) else float(row[0].y)
            if len(row) < 5:
                continue
            # obj_init_h = self.getH(row[0],row[1]) if self.get_distance(row[0],row[1]) > 0.2 else row[0].h
            obj_init_h = row[0].h
            init.add_init_action(name, xosc.TeleportAction(xosc.WorldPosition(x=x, y=y, z=0, h=obj_init_h, p=0, r=0)))
            init.add_init_action(name, objspeed)

        trajectory = xosc.Trajectory('oscTrajectory0', False)
        step_dataEgo = []
        positionEgo1 = []
        lasth = float(positionEgo[0].h)
        for j in range(len(positionEgo) - 1):
            x = float(positionEgo[j].x)
            y = float(positionEgo[j].y)

            # if (j > 0)&(float(positionEgo[j].h) < 0)&(lasth > 0):
            #     h = float(positionEgo[j].h) + 2 * math.pi
            # elif (j > 0)&(float(positionEgo[j].h) > 0)&(lasth < 0):
            #     h = float(positionEgo[j].h) - 2 * math.pi
            # else:
            #     h = float(positionEgo[j].h)

            n = j
            if j >= (len(positionEgo) - 1):
                n = j - 1
            # h = self.getH(positionEgo[n], positionEgo[n + 1]) if self.get_distance(positionEgo[n], positionEgo[n + 1]) > 0.2 else positionEgo[n].h
            h = positionEgo[n].h
            if h == 0:
                h = 0.000001

            step_dataEgo.append(j / 10)
            positionEgo1.append(xosc.WorldPosition(x=x, y=y, z=0, h=h, p=0, r=0))
            lasth = h

        polyline = xosc.Polyline(step_dataEgo, positionEgo1)
        trajectory.add_shape(polyline)

        speedaction = xosc.FollowTrajectoryAction(trajectory, xosc.FollowMode.position, xosc.ReferenceContext.absolute,
                                                  1, 0)
        trigger = xosc.ValueTrigger('drive_start_trigger', 0, xosc.ConditionEdge.rising,
                                    xosc.SimulationTimeCondition(0, xosc.Rule.greaterThan))

        event = xosc.Event('Event1', xosc.Priority.overwrite)
        event.add_trigger(trigger)
        event.add_action('newspeed', speedaction)
        man = xosc.Maneuver('my maneuver')
        man.add_event(event)

        mangr = xosc.ManeuverGroup('mangroup', selecttriggeringentities=True)
        mangr.add_actor('Ego')
        mangr.add_maneuver(man)

        trigger0 = xosc.Trigger('start')
        act = xosc.Act('Act1', trigger0)
        act.add_maneuver_group(mangr)

        story1 = xosc.Story('mystory_ego')
        story1.add_act(act)

        sb = xosc.StoryBoard(init, stoptrigger=xosc.ValueTrigger('stop_trigger', 0, xosc.ConditionEdge.none,
                                                                 xosc.SimulationTimeCondition(self.sceperiod,
                                                                                              xosc.Rule.greaterThan),
                                                                 'stop'))
        sb.add_story(story1)

        # object car
        for i in range(len(positionObj)):
            row = positionObj[i]
            # print(row[0].ObjectID)
            name = objname + str(i)
            positionM = []
            step_dataM = []
            if len(row) < 2:
                continue
            rowNew = row
            lasth = float(rowNew[0].h)
            for j in range(len(rowNew) - 1):
                x = float(rowNew[j].x)
                y = float(rowNew[j].y)

                # if (i > 0)&(float(rowNew[j].h) < 0)&(lasth > 0):
                #     h = float(rowNew[j].h) + 2 * math.pi
                # elif (i > 0)&(float(rowNew[j].h) > 0)&(lasth < 0):
                #     h = float(rowNew[j].h) - 2 * math.pi
                # else:
                #     h = float(rowNew[j].h)

                n = j
                if j >= (len(rowNew) - 1):
                    n = j - 1
                # h = self.getH(rowNew[n],rowNew[n + 1]) if self.get_distance(rowNew[n],rowNew[n + 1]) > 0.2 else rowNew[n].h
                h = rowNew[n].h
                if h == 0:
                    h = 0.000001

                positionM.append(xosc.WorldPosition(x=x, y=y, z=0, h=h, p=0, r=0))
                step_dataM.append(float(rowNew[j].time))  # + self.intersectime
                lasth = h
            if len(positionM) < 3:
                continue

            # 使目标轨迹结束后离开视野
            positionM.append(xosc.WorldPosition(x=-10000, y=10000, z=0, h=h, p=0, r=0))
            step_dataM.append(float(rowNew[j + 1].time))

            trajectoryM = xosc.Trajectory('oscTrajectory1', False)
            polylineM = xosc.Polyline(step_dataM, positionM)
            trajectoryM.add_shape(polylineM)

            speedaction2 = xosc.FollowTrajectoryAction(trajectoryM, xosc.FollowMode.position,
                                                       xosc.ReferenceContext.absolute, 1, 0)

            event2 = xosc.Event('Event1', xosc.Priority.overwrite)
            # trigger2 = xosc.EntityTrigger("obj-start-trigger", step_dataM[0], xosc.ConditionEdge.rising, xosc.SpeedCondition(0, xosc.Rule.greaterThan),'Ego')
            trigger2 = xosc.EntityTrigger("obj-start-trigger", 0, xosc.ConditionEdge.rising,
                                          xosc.SpeedCondition(0, xosc.Rule.greaterThan), 'Ego')
            event2.add_trigger(trigger2)

            if self.augtype == 7:
                pedaction = xosc.FollowTrajectoryAction(trajectoryM, xosc.FollowMode.position,
                                                        xosc.ReferenceContext.absolute, 1, 0)
                event2.add_action('newspeed', pedaction)
                walp_trigger = xosc.EntityTrigger('ped_walp_trigger', 0, xosc.ConditionEdge.rising, \
                                                  xosc.TimeToCollisionCondition(self.intersectime, xosc.Rule.lessThan,
                                                                                entity=name), 'Ego')
                event2.add_trigger(walp_trigger)

            else:
                event2.add_action('newspeed', speedaction2)

            man = xosc.Maneuver('my maneuver')
            man.add_event(event2)

            event3 = xosc.Event('Event_ped', xosc.Priority.overwrite)
            event3.add_trigger(trigger)

            if self.augtype == 7:
                action3 = xosc.CustomCommandAction(0, 0, 0, 0, 1, 0, 0)
                action3.add_element(self.createUDAction())
                event3.add_action('newspeed', action3)
                man.add_event(event3)

                finish_trigger = xosc.EntityTrigger('finish_trigger', \
                                                    0, xosc.ConditionEdge.rising,
                                                    xosc.ReachPositionCondition(position=positionM[-1], tolerance=1),
                                                    name)
                event4 = xosc.Event('Event_ped', xosc.Priority.overwrite)
                event4.add_trigger(finish_trigger)
                be_still_action = xosc.AbsoluteSpeedAction(0, xosc.TransitionDynamics(xosc.DynamicsShapes.step,
                                                                                      xosc.DynamicsDimension.time, 1))
                event4.add_action('ped_be_still_action', be_still_action)
                man.add_event(event4)

            mangr2 = xosc.ManeuverGroup('mangroup', selecttriggeringentities=True)
            mangr2.add_actor(name)
            mangr2.add_maneuver(man)

            act2 = xosc.Act('Act1', trigger0)
            act2.add_maneuver_group(mangr2)

            story2 = xosc.Story('mystory_' + name)
            story2.add_act(act2)

            sb.add_story(story2)

        # prettyprint(sb.get_element())

        paramet = xosc.ParameterDeclarations()

        sce = xosc.Scenario('my scenario', 'Maggie', paramet, entities, sb, road, catalog)
        return sce

    def createUDAction(self, **kwargs):
        tree = ET.parse(
            '/home/lxj/Documents/pyworkspace/code/scenariogeneration-main/openX/vtd/simulation0_20210625_1344.xosc')
        root = tree.getroot()
        ele = root[5][2][1][0][1][1][0][0][0]
        newnode = ET.Element("CustomCommandAction")
        newnode.attrib = {'type': 'scp'}
        newnode.text = '<![CDATA[' + ele.text + ']]>'
        return newnode


# 获取距离
def get_distance(pState, pEnd):
    '''
    get distance between two points
    ----------
    args:
        px (list): point X, (x, y)
        py (list): point Y, (x, y)
    ----------
    return:
        number: distance
    '''
    return ((pState.x - pEnd.x) ** 2 + (pState.y - pEnd.y) ** 2) ** 0.5


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
    parm_data = pd.read_excel(os.path.join(absPath + '/trails/', "配置参数表样例0210.xlsx"),
                              sheet_name=ADAS_module, keep_default_na=False, engine='openpyxl')
    ADAS_list = [ADAS for ADAS in ADAS_module]
    scenario_df = [parm_data[scenario_list] for scenario_list in ADAS_list][0]
    for index, scenario_series in scenario_df.iterrows():
        print(scenario_series['场景编号'], 'Start')
        scenario = ScenarioData(scenario_series)
        scenario_list = scenario.get_scenario_model()
        for single_scenario in scenario_list:
            ego_trails_list = list()
            ego_road_point_list = list()
            obs_road_point_list = list()
            # 根据自车场景速度情况选择轨迹
            ego_trail_section = 0
            rotate_tuple = ('ego_e', 'ego_n'), ('left_e', 'left_n'), ('right_e', 'right_n')
            for ego_speed_status in single_scenario['ego_velocity_status']:
                trail_type = TrailType.ego_trail
                if ego_trail_section == 0:
                    start_speed = float(single_scenario['ego_start_velocity'])
                    heading_angle = float(single_scenario['ego_heading_angle'])
                else:
                    start_speed = float(ego_trails_list[-1].iloc[-1]['vel_filtered'])
                    heading_angle = float(ego_trails_list[-1].iloc[-1]['headinga'])

                ego_trail_slices = Trail(trail_type, car_trail_data, ped_trail_data, trails_json_dict, ego_speed_status,
                                         single_scenario, ego_trail_section, start_speed, heading_angle, rotate_tuple)
                '''需要增加未找到轨迹的报错判断'''
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
                                               init_e, init_n, init_h)
            else:
                print(scenario_series['场景编号'], "ego没有符合条件的轨迹, 失败")

            object_position_list = list()  # 二维数组,第一维度为不同的目标物，第二维度为相同目标物的分段轨迹形态
            if isinstance(single_scenario['obs_start_velocity'], list):

                for object_index in range(len(single_scenario['obs_start_velocity'])):
                    object_status = single_scenario['obs_velocity_status'][object_index]
                    object_trail_list = list()

                    # 根据目标车场景速度情况选择轨迹
                    object_trail_section = 0
                    for object_split_status in object_status:
                        trail_type = TrailType.vehicle_trail
                        if object_trail_section == 0:
                            start_speed = float(single_scenario['obs_start_velocity'][object_index])
                            heading_angle = float(single_scenario['obs_heading_angle_rel'][object_index])
                        else:
                            start_speed = float(object_trail_list[-1].iloc[-1]['vel_filtered'])
                            heading_angle = float(object_trail_list[-1].iloc[-1]['headinga'])

                        object_trail_slices = Trail(trail_type, car_trail_data, ped_trail_data, trails_json_dict,
                                                    object_split_status,
                                                    single_scenario, object_trail_section, start_speed, heading_angle,
                                                    rotate_tuple)
                        if object_trail_slices:
                            object_trail_list.append(object_trail_slices.position)
                        else:
                            print(f'object第{object_trail_section + 1}段轨迹没有生成', object_trail_section)
                        object_trail_section += 1

                    if object_trail_list:
                        # 拼接目标车轨迹
                        init_e = float(single_scenario['obs_start_x'][object_index])
                        init_n = float(single_scenario['obs_start_y'][object_index])
                        init_h = float(single_scenario['obs_heading_angle_rel'][object_index]) + float(
                            single_scenario['ego_heading_angle'])
                        object_trail = generateFinalTrail('object', object_trail_list, 'ego_e', 'ego_n', 'headinga',
                                                          rotate_tuple, 0, 0, 0)
                    else:
                        print(scenario_series['场景编号'], "obs没有符合条件的轨迹")

                    object_position_list.append(object_trail)

            # 转化仿真场景路径点
            ego_points, time = getEgoPosition(ego_trail, 'Time', 'ego_e', 'ego_n', 'headinga')
            object_points = []
            for obsL in range(len(object_position_list)):
                object_points.append(getEgoPosition(object_position_list[obsL], 'Time', 'ego_e', 'ego_n', 'headinga'))

            egoSpeed = 5  # 随意设的，不发挥作用
            sceperiod = math.ceil(time[-1] - time[0])
            s = Scenario(ego_points, object_points, 0, time, egoSpeed, 0, 0, 0, sceperiod)
            s.print_permutations()
            output_path = os.path.join(absPath + '/trails/', 'simulation_new')
            files = s.generate(
                output_path)  # '/home/lxj/Documents/pyworkspace/code/ScenarioTool_new/analysis/simulation'
            print(files)

    print(fileCnt)


def geneLabel(output_path):
    '''
    生成label.json文件
    '''
    labeljson = {}
    labeljson['functional_module'] = ["ACC"]
    labeljson['scene_type'] = "自适应巡航"
    labeljson['rode_type'] = "城市普通道路"
    labeljson['rode_section'] = "路段"
    with open(os.path.join(output_path, output_path.split('/')[-1] + '.json'), 'w', encoding='utf-8') as f:
        json.dump(labeljson, f, indent=4, ensure_ascii=False)


def moveList(obsList, mx, my):
    '''
    Parameters
    ----------
    obsList: 轨迹列表，必须包含（x,y）

    Returns: 返回处理后的轨迹列表
    -------

    '''
    position = []
    for i in range(len(obsList)):
        obsPosition = obsList[i]
        obsPosition.x = obsPosition.x + mx
        obsPosition.y = obsPosition.y + my
        position.append(obsPosition)
    return position.copy()


def changeCDATA(filepath):
    f = open(filepath, "r", encoding="UTF-8")
    txt = f.readline()
    all_line = []
    # txt是否为空可以作为判断文件是否到了末尾
    while txt:
        txt = txt.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&quot;", '"').replace(
            "&apos;", "'")
        all_line.append(txt)
        # 读取文件的下一行
        txt = f.readline()
    f.close()
    f1 = open(filepath, 'w', encoding="UTF-8")
    for line in all_line:
        f1.write(line)
    f1.close()


def createJsonFile(path, functional_module, scene_type, road_type, road_section, scene_description, test_procedure,
                   expect_test_result, gps, obs, pedT):
    functiona = []
    functiona.append(functional_module)
    jsontext = {'functional_module': functiona,
                'scene_type': scene_type,
                'road_type': road_type,
                'road_section': road_section,
                'scene_description': scene_description}
    if functional_module in 'PCW':
        gpsSpeed = math.floor(get_distance(Point(gps[0].x, gps[0].y),
                                           Point(gps[1].x, gps[1].y)) * 36)
        conditionsJson = {"ego_v": str(gpsSpeed) + " km/h"}
        pedSpeed = math.floor(get_distance(Point(pedT[0].x, pedT[0].y),
                                           Point(pedT[1].x, pedT[1].y)) * 36)
        x = pedT[0].x
        y = pedT[0].y
        keyV = 'obj' + str(1) + '_v'
        keyX = 'obj' + str(1) + '_x'
        keyY = 'obj' + str(1) + '_y'
        conditionsJson[keyV] = str(pedSpeed) + " km/h"
        conditionsJson[keyX] = x
        conditionsJson[keyY] = y
        test_procedure = test_procedure.replace("(obj1_v)", str(pedSpeed))
        test_procedure = test_procedure.replace("(ego_v)", str(gpsSpeed))
        jsontext['init_conditions'] = conditionsJson
        jsontext['test_procedure'] = test_procedure
        if gpsSpeed < 40:
            expect_test_result = expect_test_result.replace("TTC时间", '2.3s')
        elif gpsSpeed < 50:
            expect_test_result = expect_test_result.replace("TTC时间", '2.5s')
        elif gpsSpeed < 60:
            expect_test_result = expect_test_result.replace("TTC时间", '2.7s')
        elif gpsSpeed < 70:
            expect_test_result = expect_test_result.replace("TTC时间", '3.0s')
        elif gpsSpeed < 80:
            expect_test_result = expect_test_result.replace("TTC时间", '3.1s')
        else:
            expect_test_result = expect_test_result.replace("TTC时间", '3.2s')
        jsontext['expect_test_result'] = expect_test_result
    else:
        gpsSpeed = math.floor(get_distance(Point(gps[0].x, gps[0].y),
                                           Point(gps[1].x, gps[1].y)) * 36)
        conditionsJson = {"ego_v": str(gpsSpeed) + " km/h"}
        for i in range(len(obs)):
            obsSpeed = math.floor(get_distance(Point(obs[i][0].x, obs[i][0].y),
                                               Point(obs[i][1].x, obs[i][1].y)) * 36)
            x = obs[i][0].x
            y = obs[i][0].y
            keyV = 'obj' + str(i + 1) + '_v'
            keyX = 'obj' + str(i + 1) + '_x'
            keyY = 'obj' + str(i + 1) + '_y'
            conditionsJson[keyV] = str(obsSpeed) + " km/h"
            conditionsJson[keyX] = x
            conditionsJson[keyY] = y
            strObsV = '(obj' + str(i + 1) + '_v)'
            test_procedure = test_procedure.replace(strObsV, str(obsSpeed))
        jsontext['init_conditions'] = conditionsJson

        test_procedure = test_procedure.replace("(ego_v)", str(gpsSpeed))
        jsontext['test_procedure'] = test_procedure
        if functional_module in 'FCW':
            if gpsSpeed < 40:
                expect_test_result = expect_test_result.replace("TTC时间", '2.3s')
            elif gpsSpeed < 50:
                expect_test_result = expect_test_result.replace("TTC时间", '2.5s')
            elif gpsSpeed < 60:
                expect_test_result = expect_test_result.replace("TTC时间", '2.7s')
            elif gpsSpeed < 70:
                expect_test_result = expect_test_result.replace("TTC时间", '3.0s')
            elif gpsSpeed < 80:
                expect_test_result = expect_test_result.replace("TTC时间", '3.1s')
            else:
                expect_test_result = expect_test_result.replace("TTC时间", '3.2s')
        elif functional_module in 'AEB':
            if gpsSpeed > 50:
                expect_test_result = expect_test_result.replace("TTC时间", '1.4s')
            elif gpsSpeed > 40:
                expect_test_result = expect_test_result.replace("TTC时间", '1.35s')
            elif gpsSpeed > 30:
                expect_test_result = expect_test_result.replace("TTC时间", '1.3s')
            else:
                expect_test_result = expect_test_result.replace("TTC时间", '1.2s')
        jsontext['expect_test_result'] = expect_test_result
    jsondata = json.dumps(jsontext, indent=4, separators=(',', ': '), ensure_ascii=False)
    f = open(path, 'w', encoding='utf-8')
    f.write(jsondata)
    f.close()


if __name__ == "__main__":
    parsingConfigurationFile("D:/泛化", ['AEB'])
