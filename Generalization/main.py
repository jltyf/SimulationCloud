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

from enumerations import TrailType
from Generalization.serialization.scenario_serialization import ADASScenario
from Generalization.trail import Trail
from Generalization.utils import dump_json, get_connect_trail

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


class Scenario(ScenarioGenerator):
    def __init__(self, gps, obs, ped, roadT, roadL):
        ScenarioGenerator.__init__(self)
        self.gps = gps
        self.obs = obs
        self.ped = ped
        self.naming = 'numerical'
        self.roadT = roadT
        self.roadL = roadL

    def road(self, **kwargs):
        bIs = (self.roadT.count('6') + self.roadT.count('7')) == 0
        if bIs:
            planview = xodr.PlanView()
            planview.add_fixed_geometry(xodr.Line(250), -50, 0, 0)
            # create simple lanes
            lanes = xodr.Lanes()
            lanesection1 = xodr.LaneSection(0, xodr.standard_lane(rm=xodr.STD_ROADMARK_BROKEN))
            lanesection1.add_left_lane(xodr.standard_lane(offset=LaneWidth, rm=xodr.STD_ROADMARK_BROKEN))
            lanesection1.add_left_lane(xodr.standard_lane(offset=LaneWidth, rm=xodr.STD_ROADMARK_BROKEN))
            lanesection1.add_left_lane(xodr.standard_lane(offset=LaneWidth, rm=xodr.STD_ROADMARK_SOLID))
            lanesection1.add_right_lane(xodr.standard_lane(offset=LaneWidth, rm=xodr.STD_ROADMARK_BROKEN))
            lanesection1.add_right_lane(xodr.standard_lane(offset=LaneWidth, rm=xodr.STD_ROADMARK_BROKEN))
            lanesection1.add_right_lane(xodr.standard_lane(offset=LaneWidth, rm=xodr.STD_ROADMARK_SOLID))
            lanes.add_lanesection(lanesection1)
            road = xodr.Road(0, planview, lanes)
            odr = xodr.OpenDrive('myroad')
            odr.add_road(road)
            odr.adjust_roads_and_lanes()
            return odr
        else:
            roads = []
            numintersections = 4  # 3 or 4
            angles = []
            roadLength = 0
            radius = 0
            index = 0
            for k in range(len(self.roadT)):
                if self.roadT[k] in '6' or self.roadT[k] in '7':
                    roadLength = math.fabs(self.roadL[k - 1].y)
                    radius = math.fabs(self.roadL[k].y - self.roadL[k - 1].y)
                    index = k
                    break
            index2 = len(self.roadT)
            for k in range(index + 1, len(self.roadT)):
                if self.roadT[k] in '6' or self.roadT[k] in '7':
                    index2 = k
                    break
            for i in range(numintersections):
                roads.append(xodr.create_straight_road(i, n_lanes=3, length=roadLength))
                angles.append(i * 2 * np.pi / numintersections)
            junc = xodr.create_junction_roads(roads, angles, radius / 1.636)
            junction = xodr.create_junction(junc, 1, roads)
            odr = xodr.OpenDrive('myroad')
            odr.add_junction(junction)
            for r in roads:
                # r.add_shape(0, 0, 3, 0, 0, 0)
                odr.add_road(r)
            for j in junc:
                odr.add_road(j)

            odr.adjust_roads_and_lanes()
            return odr

    def getH(self, point1, point2):
        h = math.atan2((point2.y - point1.y), (point2.x - point1.x))
        return h

    def scenario(self, **kwargs):
        osgbName = self.road_file.split('.')
        osgbName = osgbName[0] + ".osgb"
        road = xosc.RoadNetwork(self.road_file, scenegraph=osgbName)

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

        # object car model
        for i in range(len(self.obs)):
            row = self.obs[i]
            entities.add_scenario_object(objname + str(i + 1), white_veh, cnt2)

        if len(self.ped) > 0:
            # pedestrian model
            entities.add_scenario_object(objname + "0", male_ped)

        positionEgo = self.gps
        positionObj = self.obs
        init = xosc.Init()
        step_time = xosc.TransitionDynamics(xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 0)
        egospeed = xosc.AbsoluteSpeedAction(0, step_time)
        objspeed = xosc.AbsoluteSpeedAction(0, step_time)

        # ego car
        init.add_init_action(egoname, xosc.TeleportAction(
            xosc.WorldPosition(x=positionEgo[0].x, y=positionEgo[0].y, z=0, h=self.getH(positionEgo[0], positionEgo[1]),
                               p=0, r=0)))
        init.add_init_action(egoname, egospeed)
        init.add_global_action(xosc.EnvironmentAction(name="InitEnvironment", environment=xosc.Environment(
            xosc.TimeOfDay(True, 2019, 12, 19, 20, 0, 0),
            xosc.Weather(sun_intensity=2000, sun_azimuth=40, sun_elevation=20,
                         cloudstate=xosc.CloudState.overcast,
                         precipitation=xosc.PrecipitationType.rain,
                         precipitation_intensity=1,
                         visual_fog_range=600),
            xosc.RoadCondition(friction_scale_factor=0.7))))
        # obj car
        for i in range(len(positionObj)):
            row = positionObj[i]
            name = objname + str(i + 1)
            x = -10000
            y = 10000
            # x = 0.000001 if (abs(float(row[0].x)) < 0.000001) else float(row[0].x)
            # y = 0.000001 if (abs(float(row[0].y)) < 0.000001) else float(row[0].y)
            init.add_init_action(name, xosc.TeleportAction(
                xosc.WorldPosition(x=x, y=y, z=0, h=self.getH(row[0], row[1]), p=0, r=0)))
            init.add_init_action(name, objspeed)

        # obj ped
        if len(self.ped) > 0:
            pedName = objname + "0"
            x = self.ped[0].x
            y = self.ped[0].y
            init.add_init_action(pedName,
                                 xosc.TeleportAction(xosc.WorldPosition(x=x, y=y, z=0, h=self.ped[0].h, p=0, r=0)))
            init.add_init_action(pedName, objspeed)

        # ego car story    
        trajectory = xosc.Trajectory('oscTrajectory0', False)
        step_dataEgo = []
        positionEgo1 = []
        for j in range(len(positionEgo) - 1):
            x = float(positionEgo[j].x)
            y = float(positionEgo[j].y)

            n = j
            if j >= (len(positionEgo) - 1):
                n = j - 1
            h = self.getH(positionEgo[n], positionEgo[n + 1])
            if h == 0:
                h = 0.000001

            step_dataEgo.append(j / 10)
            positionEgo1.append(xosc.WorldPosition(x=x, y=y, z=0, h=h, p=0, r=0))

        polyline = xosc.Polyline(step_dataEgo, positionEgo1)
        trajectory.add_shape(polyline)

        speedaction = xosc.FollowTrajectoryAction(trajectory, xosc.FollowMode.position, xosc.ReferenceContext.absolute,
                                                  1, 0)
        speedaction11 = xosc.AbsoluteSpeedAction(0, xosc.TransitionDynamics(xosc.DynamicsShapes.step,
                                                                            xosc.DynamicsDimension.time, 1))
        trigger = xosc.ValueTrigger('drive_start_trigger', 0, xosc.ConditionEdge.rising,
                                    xosc.SimulationTimeCondition(0, xosc.Rule.greaterThan))
        # trigger2 = xosc.EntityTrigger('stop', 0, xosc.ConditionEdge.rising, xosc.CollisionCondition(objname + '0'), egoname)

        event = xosc.Event('Event1', xosc.Priority.overwrite)
        event.add_trigger(trigger)
        event.add_action('newspeed', speedaction)
        # event11 = xosc.Event('Event11', xosc.Priority.overwrite)
        # event11.add_trigger(trigger2)
        # event11.add_action('newspeed11', speedaction11)
        man = xosc.Maneuver('my maneuver')
        man.add_event(event)
        # man.add_event(event11)

        mangr = xosc.ManeuverGroup('mangroup', selecttriggeringentities=True)
        mangr.add_actor('Ego')
        mangr.add_maneuver(man)

        trigger0 = xosc.Trigger('start')
        act = xosc.Act('Act1', trigger0)
        act.add_maneuver_group(mangr)

        story1 = xosc.Story('mystory_ego')
        story1.add_act(act)

        tiemLength = math.fabs(float(positionEgo[0].time) - float(positionEgo[len(positionEgo) - 1].time)) + 0.1
        sb = xosc.StoryBoard(init, stoptrigger=xosc.ValueTrigger('stop_trigger ', 0, xosc.ConditionEdge.none,
                                                                 xosc.SimulationTimeCondition(tiemLength,
                                                                                              xosc.Rule.greaterThan),
                                                                 'stop'))
        sb.add_story(story1)

        # object car story
        for i in range(len(positionObj)):
            row = positionObj[i]
            name = objname + str(i + 1)
            positionM = []
            step_dataM = []
            if len(row) < 2:
                continue
            rowNew = row
            lasth = float(rowNew[0].h)
            for j in range(len(rowNew) - 1):
                x = float(rowNew[j].x)
                y = float(rowNew[j].y)

                n = j
                if j >= (len(rowNew) - 1):
                    n = j - 1
                h = self.getH(rowNew[n], rowNew[n + 1])
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
            speedaction11 = xosc.AbsoluteSpeedAction(0, xosc.TransitionDynamics(xosc.DynamicsShapes.step,
                                                                                xosc.DynamicsDimension.time, 1))
            # trigger2 = xosc.EntityTrigger('stop', 0, xosc.ConditionEdge.rising, xosc.CollisionCondition(egoname),
            #                               objname + '1')
            # if len(positionObj) > 1:
            #     if i == 0:
            #         trigger3 = xosc.EntityTrigger('stop', 0, xosc.ConditionEdge.rising, xosc.CollisionCondition(objname + '2'),
            #                                       name)
            #         event22 = xosc.Event('Event11', xosc.Priority.overwrite)
            #         event22.add_trigger(trigger3)
            #         event22.add_action('newspeed11', speedaction11)
            #     else:
            #         trigger3 = xosc.EntityTrigger('stop', 0, xosc.ConditionEdge.rising,
            #                                       xosc.CollisionCondition(objname + '1'),
            #                                       name)
            #         event22 = xosc.Event('Event11', xosc.Priority.overwrite)
            #         event22.add_trigger(trigger3)
            #         event22.add_action('newspeed11', speedaction11)
            event2 = xosc.Event('Event1', xosc.Priority.overwrite)
            event2.add_trigger(trigger)
            event2.add_action('newspeed', speedaction2)
            # event11 = xosc.Event('Event11', xosc.Priority.overwrite)
            # event11.add_trigger(trigger2)
            # event11.add_action('newspeed11', speedaction11)

            man = xosc.Maneuver('my maneuver')
            man.add_event(event2)
            # man.add_event(event11)
            # if len(positionObj) > 1:
            #     man.add_event(event22)
            mangr2 = xosc.ManeuverGroup('mangroup', selecttriggeringentities=True)
            mangr2.add_actor(name)
            mangr2.add_maneuver(man)

            act2 = xosc.Act('Act1', trigger0)
            act2.add_maneuver_group(mangr2)

            story2 = xosc.Story('mystory_' + name)
            story2.add_act(act2)

            sb.add_story(story2)

        # object ped story
        if len(self.ped) > 0:
            positionPed = []
            step_dataPed = []
            for j in range(len(self.ped) - 1):
                x = float(self.ped[j].x)
                y = float(self.ped[j].y)
                n = j
                if j >= (len(self.ped) - 1):
                    n = j - 1
                h = self.getH(self.ped[n], self.ped[n + 1])
                if h == 0:
                    h = 0.000001

                positionPed.append(xosc.WorldPosition(x=x, y=y, z=0, h=h, p=0, r=0))
                step_dataPed.append(float(self.ped[j].time))  # + self.intersectime
            # # 使目标轨迹结束后离开视野
            # positionPed.append(xosc.WorldPosition(x=-10000, y=10000, z=0, h=h, p=0, r=0))
            # step_dataPed.append(float(self.ped[j + 1].time))

            trajectoryPed = xosc.Trajectory('oscTrajectoryPed', False)
            polylinePed = xosc.Polyline(step_dataPed, positionPed)
            trajectoryPed.add_shape(polylinePed)

            eventped = xosc.Event('Event1', xosc.Priority.overwrite)
            eventped.add_trigger(trigger)

            pedactionPed = xosc.FollowTrajectoryAction(trajectoryPed, xosc.FollowMode.position,
                                                       xosc.ReferenceContext.absolute, 1, 0)
            eventped.add_action('newspeed', pedactionPed)
            walp_trigger = xosc.EntityTrigger('ped_walp_trigger', 0, xosc.ConditionEdge.rising, \
                                              xosc.TimeToCollisionCondition(4.0, xosc.Rule.lessThan, entity=pedName),
                                              'Ego')
            eventped.add_trigger(walp_trigger)

            man = xosc.Maneuver('my maneuver')
            man.add_event(eventped)

            action3 = xosc.CustomCommandAction(0, 0, 0, 0, 1, 0, 0)
            action3.add_element(self.createUDAction())
            event3 = xosc.Event('Event_ped', xosc.Priority.overwrite)
            event3.add_trigger(trigger)
            event3.add_action('newspeed1', action3)
            man.add_event(event3)

            # 使人倒下后留在原地
            finish_trigger = xosc.EntityTrigger('finish_trigger', \
                                                0, xosc.ConditionEdge.rising,
                                                xosc.ReachPositionCondition(position=positionPed[-1], tolerance=1),
                                                pedName)
            event4 = xosc.Event('Event_ped', xosc.Priority.overwrite)
            event4.add_trigger(finish_trigger)
            be_still_action = xosc.AbsoluteSpeedAction(0, xosc.TransitionDynamics(xosc.DynamicsShapes.step,
                                                                                  xosc.DynamicsDimension.time, 1))
            event4.add_action('ped_be_still_action', be_still_action)
            man.add_event(event4)

            mangrPed = xosc.ManeuverGroup('mangroupped', selecttriggeringentities=True)
            mangrPed.add_actor(pedName)
            mangrPed.add_maneuver(man)

            act3 = xosc.Act('Act1', trigger0)
            act3.add_maneuver_group(mangrPed)

            story3 = xosc.Story('mystory_' + "ped")
            story3.add_act(act3)

            sb.add_story(story3)
        # prettyprint(sb.get_element())

        paramet = xosc.ParameterDeclarations()

        sce = xosc.Scenario('my scenario', 'Maggie', paramet, entities, sb, road, catalog)
        return sce

    def createUDAction(self, **kwargs):
        tree = ET.parse(
            'D:/test/read_batch_lxj0_20210625_1344.xosc')
        root = tree.getroot()
        ele = root[5][2][1][0][1][1][0][0][0]
        newnode = ET.Element("CustomCommandAction")
        newnode.attrib = {'type': 'scp'}
        newnode.text = '<![CDATA[' + ele.text + ']]>'
        return newnode


# 读取JSON文件，根据parameter分类，默认longituteType分类
def getJson(jsonList, parameter=7):
    '''

    Parameters
    ----------
    JSON格式
    "carID": "dongfeng",
    "start": 1616577524353.0,
    "stop": 1616577525353.0,
    "startHeadinga": 175.1166073108493,
    "stopHeadinga": 176.21322211682332,
    "startSpeed": 1.736722031318881,
    "stopSpeed": 0.000153704950162519,
    "longituteType": "Stop",
    "longituteOffset": 0.29471901585877686,
    "lateralType": "No change lane",
    "lateralOffset": 0.0,
    "crossPoint": 0,
    "carTrailPath": "/media/lxj/cicv_008/carTrails.csv",
    "pedTrailPath": "/media/lxj/cicv_008/pedTrails.csv"

    parameter: 条件在JSON中的位置

    Returns: 根据传参判断，生成list，默认参数是7，对应longituteType，
            json文件中对应longituteType有几种值就会生成几条list，
            返回格式是：[[][][]]
    -------
    '''
    # jsonPath = JsonPath
    # trailsJson = pd.read_json(jsonPath)
    # jsonList = trailsJson.values.tolist()
    global unchanged_line_label_list, change_line_label_list  # 在函数内部声明全局变量，只有特殊情况下使用
    if (parameter == 7) and len(unchanged_line_label_list) > 0:
        return unchanged_line_label_list
    elif parameter == 9 and len(change_line_label_list) > 0:
        return change_line_label_list
    dt = []
    for i in range(len(jsonList)):
        # if float(jsonList[i][8]) < 1: #去掉长度小于1的线段
        #     continue
        if len(dt) == 0:
            dt1 = []
            trajectory = jsonList[i]
            dt1.append(trajectory)
            dt.append(dt1)
            continue
        isAdd = True
        for j in range(len(dt)):
            trajectory = jsonList[i]
            dt1 = dt[j][0]
            if (trajectory[parameter] in dt1[parameter]):
                dt[j].append(trajectory)
                isAdd = False
                break
        if isAdd:
            dt1 = []
            dt1.append(trajectory)
            dt.append(dt1)
    if parameter == 7:
        unchanged_line_label_list = dt
    elif parameter == 9:
        change_line_label_list = dt

    return dt


def getSort(Json, IsACC=False):
    # 速度排序
    '''

    Parameters
    ----------
    Json: 进行排序的json列表
    IsACC：True 根据初速度从小到大排，Flase，反之

    Returns：返回list，元素是json
    -------

    '''
    for i in range(len(Json)):
        for j in range(len(Json) - i - 1):
            if IsACC:
                if (Json[j][StopSpeedIndex] > Json[j + 1][StopSpeedIndex]):
                    temp = Json[j + 1]
                    Json[j + 1] = Json[j]
                    Json[j] = temp
            else:
                if Json[j][StartSpeedIndex] < Json[j + 1][StartSpeedIndex]:
                    temp = Json[j + 1]
                    Json[j + 1] = Json[j]
                    Json[j] = temp
    return Json


def parsingObs(obsList, obj, point):
    '''
    Parameters
    ----------
    obsList: 轨迹列表，必须包含（x,y）
    obj : 轨迹的名称
    point : 起点，格式是（x,y）

    Returns: 返回处理后的轨迹列表
    -------

    '''
    position = []
    i = 0
    # 拼出一条直线
    for result in obsList:
        x = round(float(result[CSVInXIndex]), 8) - round(point.x, 8)
        y = float(result[CSVInYIndex]) - point.y
        position.append(
            ObsPosition(round(i / 10, 1), str(obj), str(obj),
                        x,
                        y,
                        round(float(result[1]), 2), float(result[10])))
        i += 1
    return position


def parsingPed(obsList, obj, pY):
    '''
    Parameters
    ----------
    obsList: 轨迹列表，必须包含（x,y）
    obj : 轨迹的名称
    point : 起点，格式是（x,y）

    Returns: 返回处理后的轨迹列表
    -------

    '''
    position = []
    i = 0
    h = getHead(Point(obsList.at[0, 'ped_e'], obsList.at[0, 'ped_n']),
                Point(obsList.at[1, 'ped_e'], obsList.at[1, 'ped_n']))
    if pY == 1:
        h -= 0.5 * math.pi
    elif pY == 2:
        h -= math.pi
    elif pY == 3:
        h -= 1.5 * math.pi

    obsList = pedSpinTransform(obsList, "ped_e", "ped_n", obsList.copy(), h)
    point = Point(obsList.at[0, 'ped_e'], obsList.at[0, 'ped_n'])
    # 拼出一条直线
    for result in obsList.values.tolist():
        x = round(float(result[2]), 8) - round(point.x, 8)
        y = float(result[1]) - point.y
        position.append(
            ObsPosition(round(i / 10, 1), str(obj), str(obj),
                        x,
                        y,
                        round(float(result[1]), 2), float(result[10])))
        i += 1
    return position


# 判断泛化两个集合交集，暂时没用
def inter(a, b):
    return list(set(a) & set(b))


def getSideBySideSort(Json, IsAcc):
    '''

    Parameters：获取批量的轨迹json，返回的list，每一个元素就是一条轨迹，
                例如list1中包含多个josn，这些json对应去csv文件中读取
                轨迹后，拼在一起变成符合条件的轨迹
    ----------
    Json: 根据速度排序后的Json
    IsAcc：True 为加速，False 为减速

    Returns：返回轨迹的list,格式[list1，list2，list3]，每个元素是一条轨迹，
            list1中的元素是Json
    -------
    '''
    intersectList = intersectSet(Json, IsAcc)
    trajectoryJsonList = []
    startList = []
    startList.append(0)
    # automaticCombination(intersectList, startList,trajectoryJsonList)
    for cnt in range(100):
        for i in range(len(Json)):
            dt = []
            for j in range(len(intersectList)):
                if i == intersectList[j][0]:
                    pos = intersectList[j]
                    dt.append(i)  # 轨迹的起始轨迹
                    for k in range(j + 1, len(intersectList)):
                        if len(inter(pos, intersectList[k])) == 0:
                            dt.append(intersectList[k][cnt % len(intersectList[k])])
                            pos = intersectList[k]
                    if len(dt) > cnt:
                        trajectoryJsonList.append(dt)
                    break
            if len(trajectoryJsonList) >= NumberOfTracks:
                break
    return trajectoryJsonList


# 判断加速轨迹速度相交
def intersectSet(Json, IsAcc):
    '''

    Parameters:将速度有相交的json放到同一个列表中，后面拼轨迹时，同一个list中的值，不能出现在同一条轨迹
    ----------
    Json:根据速度排序后的Json
    IsAcc:True 为加速，False 为减速

    Returns：返回格式[list1，list2，list3]
            list1中的元素是json, 同一list中的元素（json）速度有相交
    -------
    '''
    dl = []
    for i in range(len(Json)):
        dl1 = []
        dl1.append(i)
        for j in range(i + 1, len(Json)):
            if IsAcc:
                if Json[i][StopSpeedIndex] > Json[j][StartSpeedIndex]:  # 速度相交
                    dl1.append(j)
                else:
                    break
            else:
                if Json[i][StopSpeedIndex] < Json[j][StartSpeedIndex]:  # 速度相交
                    dl1.append(j)
                else:
                    break
        dl.append(dl1)
    return dl


# 自动组合
def automaticCombination(dl, ddl1, dList):
    '''

    Parameters
    ----------
    dl: intersectSet方法生成的list
    ddl1: 固定值：[0]
    dList：出参，最后要返回的值，每个元素包含一条轨迹所需要的json
    全局变量
    NumberOfTracks：决定dList的长度
    Returns
    -------

    '''
    if (len(dList) >= NumberOfTracks):
        return
    for l in range(len(dl) - 1):
        if dl[l][0] == ddl1[(len(ddl1) - 1)]:
            maxStart = dl[l][len(dl[l]) - 1]
            break
    for k in range(l + 1, len(dl)):
        if dl[k][0] > maxStart:
            for n in range(len(dl[k])):
                ddl2 = ddl1.copy()
                ddl2.append(dl[k][n])
                if k == len(dl) - 1 or dl[k][n] == dl[len(dl) - 1][0]:
                    dList.append(ddl2)
                    return
                automaticCombination(dl, ddl2, dList)
            break


def resample_bytime(data, minnum, dt, flag=True):
    """
    resample by time window
    return first value of resampled data
    :param data: 输入数据，dataframe
    :param minnum: 按几分钟resample，float
    :param dt: 日期时间变量名，str
    :param flag: True 向下采样; False 向上采样
    :return: 输出结果，dataframe
    """
    data.index = dt
    if minnum == 0:
        minnum = 1
    if flag:
        scale = str(minnum) + 'T'
        r = data.resample(scale).first()
    else:
        scale = str(minnum) + 'S'
        r = data.resample(scale).interpolate()
    r = r.reset_index(drop=True)
    return r


# 加速直线或者减速直线的获取
def getAccelarateOrDecelarate(car_trails, IsAcc, trails_json_list, period, deg):
    '''

    Parameters
    ----------
    IsAcc: True 批量生成加速轨迹, False 生成减速轨迹

    Returns：返回多条加速轨迹，轨迹的条数由全局变量NumberOfTracks决定
    （如果所能生成的轨迹数量大于NumberOfTracks，返回轨迹条数是NumberOfTracks，
    不然就是能生成多少就返回多少）
    -------

    '''
    trails_json = getJson(trails_json_list)
    position_list = []
    for trails_list in trails_json:
        # 加速不变道和减速不变道路
        if (trails_list[0][TrajectoryTypeIndex] == "No change lane") and \
                ((IsAcc and trails_list[0][LongituteTypeIndex] == 'Accelarate') or
                 (not IsAcc and trails_list[0][LongituteTypeIndex] == 'Decelarate')):
            acc_trails_json_list = getSort([trail for trail in trails_list
                                            if math.fabs(trail[StartHeadingIndex] -
                                                         trail[StopHeadingIndex]) <= 1], IsAcc)
            trajectory_json_list = getSideBySideSort(acc_trails_json_list, IsAcc)
            for trajectory_json in trajectory_json_list:
                acc_csv_list = []
                trails = car_trails.copy()
                acc_json_List = [acc_trails_json_list[j] for j in trajectory_json]
                for acc_json in acc_json_List:
                    trail_new = trails[(trails['Time'] <= float(acc_json[StopTime]))
                                       & (trails['Time'] >= float(acc_json[StartTime]))].reset_index(drop=True)
                    if len(trail_new) >= 5:
                        acc_csv_list.append(trail_new)
                slice_trail = acc_csv_list[0]
                final_trail = acc_csv_list[0]
                for single_trail in acc_csv_list:
                    # 格式化处理后过滤掉第一帧
                    format_slice_trail = get_merge_trails(slice_trail, single_trail)[1:].reset_index(drop=True)
                    slice_trail = format_slice_trail
                    final_trail = pd.concat([final_trail, format_slice_trail], axis=0).reset_index(drop=True)
                final_trail = SpinTransform(final_trail, "ego_e", "ego_n", final_trail.copy(),
                                            -final_trail.at[0, 'headinga'] + deg)
                trails_n = math.ceil(period * 10 / len(final_trail))
                rng = pd.date_range('2020-05-10 00:00:00', periods=len(final_trail), freq='T')
                if trails_n > 1:
                    sample = math.floor(60 / trails_n)
                    final_trail = resample_bytime(data=final_trail, minnum=sample, dt=rng, flag=False)[:period * 10]
                    start_point = Point(final_trail.at[0, 'ego_e'], final_trail.at[0, 'ego_n'])
                    final_trail['ego_e'] = final_trail['ego_e'] - start_point.x
                    final_trail['ego_n'] = final_trail['ego_n'] - start_point.y
                else:
                    sample = math.floor(len(final_trail) / period * 10)
                    final_trail = resample_bytime(data=final_trail, minnum=sample, dt=rng, flag=False)[:period * 10 - 1]
                    start_point = Point(final_trail.at[0, 'ego_e'], final_trail.at[0, 'ego_n'])
                    final_trail['ego_e'] = 0
                    final_trail['ego_n'] = final_trail['ego_n'] - start_point.y
                final_trail = final_trail.reset_index(drop=True)
                position_list.append(final_trail)
    return position_list


def getHead(point1, point2):
    '''
    由两个点返回线的角度
    Parameters
    ----------
    point1（x,y）
    point2 (x,y）

    Returns
    -------

    '''
    h = math.atan2((point2.y - point1.y), (point2.x - point1.x))
    return h


def rotate_trajectory(position_list, ox, oy, deg):
    '''
    rotate trajectory around point O
    ----------
    args:
        position_list (list): a list of tuples; (x, y, z, h, p, r)
        ox (number): x of point O
        oy (number): y of point O
        deg (number): rotate degree(rad), clockwise
    ----------
    return:
        list: result of rotating
    '''
    deg = math.pi / 180 * deg
    result = []
    for point in position_list:
        x = (point.x - ox) * math.cos(deg) + (point.y - oy) * math.sin(deg) + ox
        y = -(point.x - ox) * math.sin(deg) + (point.y - oy) * math.cos(deg) + oy
        result.append(Point(x, y))
    return result


def getChangeLane(carTrails, jsonList, isLeft, changeCnt, period, deg):
    '''
    Parameters
    ----------
    isLeft : True 为左变道 False 为右变道
    changeCnt : 变化车道数
    Returns 轨迹
    -------
    '''
    allJson = getJson(jsonList, TrajectoryTypeIndex)
    uniformSpeedJson = []
    for i in range(len(allJson)):
        jsoni = allJson[i][0]
        if isLeft is True:
            if jsoni[TrajectoryTypeIndex] in ['Left change lane', "Left change lane+No change lane"]:
                uniformSpeedJson += allJson[i]
                continue
        else:
            if jsoni[TrajectoryTypeIndex] in ["Right change lane", 'Right change lane+No change lane']:
                uniformSpeedJson += allJson[i]
                continue
    uniformSpeedJson = getSort(uniformSpeedJson, True)
    changeLaneJsonList = []
    # 过滤掉角度变化小于30的轨迹，这样的轨迹认为不适合做转向处理
    for i in range(len(uniformSpeedJson)):
        jsoni = uniformSpeedJson[i]
        if isLeft == True and (jsoni[3] - jsoni[4] > 1) and math.fabs(jsoni[3] - jsoni[4]) < 30:  # 向左变道
            changeLaneJsonList.append(jsoni)
        if isLeft == False and (jsoni[3] - jsoni[4] < -1) and math.fabs(jsoni[3] - jsoni[4]) < 30:  # 向右变道
            changeLaneJsonList.append(jsoni)

    trails = carTrails.copy()
    pos = []

    # 对新数据使用
    for i in range(len(changeLaneJsonList)):
        jsoni = changeLaneJsonList[i]
        trail_new = trails[(trails['Time'] <= float(jsoni[StopTime])) & (trails['Time'] >= float(jsoni[StartTime]))]
        trail_new = trail_new.reset_index(drop=True)
        trail_new = originTrails(trail_new)
        if math.fabs(trail_new.at[len(trail_new) - 1, 'ego_e'] - trail_new.at[0, 'ego_e']) > (
                changeCnt * (LaneWidth / 2)):
            for j in range(len(trail_new)):
                if math.fabs(trail_new.at[j, 'ego_e'] - trail_new.at[0, 'ego_e']) > (changeCnt * (LaneWidth / 2)):
                    # 获取偏差更小的点
                    if math.fabs(math.fabs(trail_new.at[j, 'ego_e'] - trail_new.at[0, 'ego_e']) - (
                            changeCnt * (LaneWidth / 2))) > math.fabs(
                        math.fabs(trail_new.at[j - 1, 'ego_e'] - trail_new.at[0, 'ego_e']) - (
                                changeCnt * (LaneWidth / 2))):
                        c = trail_new[:j]
                    else:
                        if j + 1 < len(trail_new):
                            c = trail_new[:j + 1]
                        else:
                            c = trail_new[:j]
                    b = SpinTransform(c, "ego_e", "ego_n", c.copy()).iloc[::-1]
                    b = b[1:]
                    c = pd.concat([c, b], axis=0)
                    c = c.reset_index(drop=True)
                    n = math.ceil(period * 10 / len(c))
                    c = SpinTransform(c, "ego_e", "ego_n", c.copy(), deg)
                    rng = pd.date_range("2020-05-10 00:00:00", periods=len(c), freq="T")
                    if n > 1:
                        sample = math.floor(60 / n)
                        c = resample_bytime(c, sample, rng, flag=False)
                    else:
                        sample = math.floor(len(c) / (period * 10))
                        c = resample_bytime(c, sample, rng)
                    startPoint = Point(c.at[0, 'ego_e'], c.at[0, 'ego_n'])
                    c['ego_e'] = c['ego_e'] - startPoint.x
                    c['ego_n'] = c['ego_n'] - startPoint.y
                    c = c.reset_index(drop=True)
                    pos.append(c)
                    break
        else:
            tLength = math.fabs(trail_new.at[len(trail_new) - 1, 'ego_e'] - trail_new.at[0, 'ego_e'])
            num = math.ceil((changeCnt * (LaneWidth / 2)) / tLength)
            a = trail_new
            c = trail_new
            isAdd = False
            for tl in range(1, num):
                b = get_merge_trails(a, trail_new)
                b = b[1:]
                b = b.reset_index(drop=True)
                a = b
                c = pd.concat([c, b], axis=0)
                c = c.reset_index(drop=True)
                trail_new = c
                for j in range(len(trail_new)):
                    if math.fabs(trail_new.at[j, 'ego_e'] - trail_new.at[0, 'ego_e']) > (
                            changeCnt * (LaneWidth / 2)):
                        # 获取偏差更小的点
                        if math.fabs(math.fabs(trail_new.at[j, 'ego_e'] - trail_new.at[0, 'ego_e']) - (
                                changeCnt * (LaneWidth / 2))) > math.fabs(
                            math.fabs(trail_new.at[j - 1, 'ego_e'] - trail_new.at[0, 'ego_e']) - (
                                    changeCnt * (LaneWidth / 2))):
                            c = trail_new[:j]
                        else:
                            if j + 1 < len(trail_new):
                                c = trail_new[:j + 1]
                            else:
                                c = trail_new[:j]
                        b = SpinTransform(c, "ego_e", "ego_n", c.copy()).iloc[::-1]
                        b = b[1:]
                        c = pd.concat([c, b], axis=0)
                        c = c.reset_index(drop=True)
                        n = math.ceil(period * 10 / len(c))
                        c = SpinTransform(c, "ego_e", "ego_n", c.copy(), deg)
                        rng = pd.date_range("2020-05-10 00:00:00", periods=len(c), freq="T")
                        if n > 1:
                            sample = math.floor(60 / n)
                            c = resample_bytime(c, sample, rng, flag=False)
                        else:
                            sample = math.floor(len(c) / (period * 10))
                            c = resample_bytime(c, sample, rng)
                        startPoint = Point(c.at[0, 'ego_e'], c.at[0, 'ego_n'])
                        c['ego_e'] = c['ego_e'] - startPoint.x
                        c['ego_n'] = c['ego_n'] - startPoint.y
                        c = c.reset_index(drop=True)
                        pos.append(c)
                        isAdd = True
                        break
                    if isAdd == True:
                        break
    if len(pos) <= MaximumNumberNfSameTrajectories / 10:
        return pos
    spacing = int(len(pos) / (MaximumNumberNfSameTrajectories / 10))
    if spacing == 1:
        pos1 = pos[:int(MaximumNumberNfSameTrajectories / 10)]
    else:
        pos1 = pos[0:len(pos):spacing]
    return pos1


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


def getUniformSpeed(carTrails, jsonList, period, deg):
    '''

    Returns:返回一条直线轨迹
    -------

    '''
    allJson = getJson(jsonList)
    # trailpath = CSVTrajectoryPath
    # carTrails = pd.read_csv(trailpath)
    uniformSpeedJson = []
    for i in range(len(allJson)):
        if allJson[i][0][7] not in 'Uniform speed':
            continue
        for j in range(len(allJson[i])):
            jsoni = allJson[i][j]
            if (math.fabs(jsoni[StartHeadingIndex] - jsoni[StopHeadingIndex]) > 1) or float(jsoni[8]) < 1:
                continue
            if jsoni[StartSpeedIndex] < 0 or jsoni[StopSpeedIndex] < 0:
                continue
            uniformSpeedJson.append(jsoni)
    uniformSpeedJson = getSort(uniformSpeedJson)
    trails = carTrails.copy()
    pos = []
    for i in range(len(uniformSpeedJson)):
        jsoni = uniformSpeedJson[i]
        trail_new = trails[(trails['Time'] <= float(jsoni[StopTime])) & (trails['Time'] >= float(jsoni[StartTime]))]
        trail_new = trail_new.reset_index(drop=True)
        if len(trail_new) < 10:
            continue

        trail_res = trail_new.copy()
        n = math.ceil(period * 10 ** 3 / (float(jsoni[StopTime]) - float(jsoni[StartTime])))
        if n > 1:
            for j in range(n - 1):
                b = get_merge_trails(trail_res, trail_new)
                b = b[1:]
                trail_res = pd.concat([trail_res, b], axis=0)
                trail_res = trail_res.reset_index(drop=True)

        trail_res = trail_res[:period * 10]
        c = SpinTransform(trail_res, "ego_e", "ego_n", trail_res.copy(), -trail_res.at[0, 'headinga'] + deg)
        startPoint = Point(c.at[0, 'ego_e'], c.at[0, 'ego_n'])
        c['ego_e'] = c['ego_e'] - startPoint.x
        c['ego_n'] = c['ego_n'] - startPoint.y
        c = c.reset_index(drop=True)
        pos.append(c)

        if len(pos) >= MaximumNumberNfSameTrajectories:
            return pos

    # spacing = int(len(pos) / (MaximumNumberNfSameTrajectories/10))
    # if spacing == 1:
    #     pos1 = pos[:int(MaximumNumberNfSameTrajectories/10)]
    # else:
    #     pos1 = pos[0:len(pos):spacing]
    return pos


def translationAndRotation(x, y, deg, ox, oy):
    '''
    将一条线拼接到另一条线，获取需要拼接的线最后一个点拼接后的坐标
    Parameters
    ----------
    x : 第二条线最后一个点的x
    y :第二条线最后一个点的y
    deg: 第一条线最后一个点的角度
    ox :第一条线最后一个点的x
    oy :第一条线最后一个点的y

    Returns ：
    -------

    '''
    e_offset = ox
    n_offset = oy
    x += e_offset
    y += n_offset
    rad = deg / 180 * math.pi
    x = (x - ox) * math.cos(rad) + (y - oy) * math.sin(rad) + ox
    y = - (x - ox) * math.sin(rad) + (y - oy) * math.cos(rad) + oy
    return x, y


def rotate(x_list, y_list, ox, oy, deg):
    '''
    position_list (list): a list of tuples; (x, y, z, h, p, r)
    deg: clock-wise radius
    ox: rotate center point x coordination
    oy: rotate center point y coordination
    '''
    x_res = []
    y_res = []
    for i in range(len(x_list)):
        x = (x_list[i] - ox) * math.cos(deg) + (y_list[i] - oy) * math.sin(deg) + ox
        y = - (x_list[i] - ox) * math.sin(deg) + (y_list[i] - oy) * math.cos(deg) + oy
        x_res.append(x)
        y_res.append(y)

    return x_res, y_res


def SpinTransform(trail, e, n, trail_new, deg=180):
    '''
    根据trail1对trail2做旋转变换

    Parameters
    trail : TYPE
        要拼接的轨迹.
    e : TYPE
        e列名称.
    n : TYPE
        n列名称.
    rad : TYPE
        旋转角度，弧度值.
    trail_new : TYPE
        处理后的trail2.

    Returns
    -------
    trail_new : TYPE
        处理后的trail2.

    '''
    e_offset = trail.at[0, e]
    n_offset = trail.at[0, n]
    trail_new[e] += e_offset
    trail_new[n] += n_offset
    red = deg / 180 * math.pi
    a, b = rotate(trail_new[e], trail_new[n], trail_new.at[len(trail_new) - 1, e], trail_new.at[len(trail_new) - 1, n],
                  red)
    trail_new[e] = a
    trail_new[n] = b
    trail_new['headinga'] += deg
    return trail_new


def pedSpinTransform(trail, e, n, trail_new, red):
    '''
    根据trail1对trail2做旋转变换

    Parameters
    trail : TYPE
        要拼接的轨迹.
    e : TYPE
        e列名称.
    n : TYPE
        n列名称.
    rad : TYPE
        旋转角度，弧度值.
    trail_new : TYPE
        处理后的trail2.

    Returns
    -------
    trail_new : TYPE
        处理后的trail2.

    '''
    e_offset = trail.at[0, e]
    n_offset = trail.at[0, n]
    trail_new[e] += e_offset
    trail_new[n] += n_offset
    a, b = rotate(trail_new[e], trail_new[n], trail_new.at[len(trail_new) - 1, e], trail_new.at[len(trail_new) - 1, n],
                  red)
    trail_new[e] = a
    trail_new[n] = b
    return trail_new


def corTransform(trail, e, n, rad, trail_new):
    '''
    根据trail1对trail2做旋转变换

    Parameters
    trail : TYPE
        要拼接的轨迹.
    e : TYPE
        e列名称.
    n : TYPE
        n列名称.
    rad : TYPE
        旋转角度，弧度值.
    trail_new : TYPE
        处理后的trail2.

    Returns
    -------
    trail_new : TYPE
        处理后的trail2.

    '''
    e_offset = -trail.at[0, e]
    n_offset = -trail.at[0, n]
    trail_new[e] += e_offset
    trail_new[n] += n_offset
    a, b = rotate(trail_new[e], trail_new[n], trail_new.at[0, e], trail_new.at[0, n], rad)
    trail_new[e] = a
    trail_new[n] = b
    return trail_new


def originTrails(trail):
    '''
    想要将trail2拼接到trail1之后，保证拼接部位平滑，需要对trail2做平移和旋转变换，返回处理后的trail2

    Parameters
    ----------
    trail : TYPE
        轨迹的数据.

    Returns
    -------
    trail_new : TYPE
        处理后的trail.

    '''
    startDeg = 0
    trail_new = trail.copy()
    trail = trail.reset_index(drop=True)
    deg = startDeg - trail_new.at[0, 'headinga']
    rad = deg / 180 * math.pi
    trail_new = corTransform(trail, 'ego_e', 'ego_n', rad, trail_new)
    trail_new = corTransform(trail, 'left_e', 'left_n', rad, trail_new)
    trail_new = corTransform(trail, 'right_e', 'right_n', rad, trail_new)
    trail_new['headinga'] += deg
    return trail_new


def trailBatchRun(self, absPath):
    carTrail = os.path.join(absPath, 'carTrails.csv')
    jsonTrail = os.path.join(absPath, 'Trails.json')
    summaryjsons = os.path.join(absPath, 'summary1.json')

    # 读取文件数据
    data = pd.read_csv(carTrail)
    jsonlist = pd.read_json(jsonTrail).values.tolist()
    with open(jsonTrail) as f:
        slices = json.load(f)
    with open(summaryjsons) as f:
        sumslices = json.load(f)

    # 直线轨迹原始数据
    acc_dec_jsons = [x for x in sumslices[0]['Slices'] if (
            ((x['longituteType'] == 'Accelarate') | (x['longituteType'] == 'Decelarate')) & (
            x['longituteOffset'] > 3))]
    acc_dec_jsondf = pd.DataFrame(acc_dec_jsons)
    acc_dec_jsonList = acc_dec_jsondf.values.tolist()
    acc_dec_data = self.getTargetTrails(acc_dec_jsons, data)

    # 曲线轨迹原始数据
    left_right_jsons = [x for x in sumslices[2]['Slices'] + sumslices[3]['Slices']]  # 分好类的弯曲直线
    left_right_jsonList = pd.DataFrame(left_right_jsons).values.tolist()
    left_right_data = self.getTargetTrails(acc_dec_jsons, data)

    # 加减速轨迹拼接数据
    acc_obs = getAccelarateOrDecelarate(acc_dec_data, True, acc_dec_jsonList, 5)  # False 减速轨迹拼接, True 加速轨迹拼接
    dec_obs = getAccelarateOrDecelarate(acc_dec_data, False, acc_dec_jsonList, 10)  # False 减速轨迹拼接, True 加速轨迹拼接

    # 匀速轨迹拼接数据
    uni_obs = getUniformSpeed(data, jsonlist, 20)

    # 变道轨迹拼接数据
    left_obs = getChangeLane(data, jsonlist, True, 1, 6)
    right_obs = getChangeLane(data, jsonlist, False, 1, 8)

    print('acc ', len(acc_obs))
    print('dec ', len(dec_obs))
    print('uni ', len(uni_obs))
    print('left_obs ', len(left_obs))
    print('right_obs ', len(right_obs))
    print('uni len ', len(uni_obs[0]))
    print('-------------------')
    for a in acc_obs:
        print(len(a))
    print('-------------------')
    for a in dec_obs:
        print(len(a))
    print('-------------------')
    for a in left_obs:
        print(len(a))
    print('-------------------')
    for a in right_obs:
        print(len(a))
    print('-------------------')

    obs_x = 50
    obs_y = 0

    # 自车轨迹
    # gps =

    # egoSpeed = 5
    # s = Scenario(gps, acc_obs, 0, 0, egoSpeed, 0, 0, 0)
    # s.print_permutations()
    # filename = absPath
    # files = s.generate(filename)
    # print(files)


def parsingConfigurationFile(absPath, ADAS_module):
    car_trail = os.path.join(absPath + '/trails/', 'CarTrails_Merge.csv')
    ped_trail = os.path.join(absPath + '/trails/', 'pedTrails.csv')
    json_trail = os.path.join(absPath + '/json/', 'Trails_Merge.json')
    with open(json_trail) as f:
        trails_json_dict = json.load(f)
    trails_json_dict = dump_json(trails_json_dict)
    fileCnt = 0
    car_trail_data = pd.read_csv(car_trail)
    ped_trail_data = pd.read_csv(ped_trail)
    parm_data = pd.read_excel(os.path.join(absPath, "配置参数表样例0210.xlsx"),
                              sheet_name=ADAS_module, keep_default_na=False, engine='openpyxl')
    ADAS_list = [ADAS for ADAS in ADAS_module]
    scenario_df = [parm_data[scenario_list] for scenario_list in ADAS_list][0]
    for index, scenario_series in scenario_df.iterrows():
        print(scenario_series['场景编号'], 'Start')
        scenario = ADASScenario(scenario_series)
        scenario_list = scenario.get_scenario_model()
        for single_scenario in scenario_list:
            ego_position_list = list()
            ego_road_point_list = list()
            obs_road_point_list = list()
            # 根据场景速度情况选择轨迹
            ego_trail_section = 0
            for ego_speed_status in single_scenario['ego_velocity_status']:
                trail_type = TrailType.ego_trail
                if ego_trail_section == 0:
                    start_speed = single_scenario['ego_start_velocity']
                    heading_angle = float(single_scenario['ego_heading_angle'])
                else:
                    start_speed = ego_position_list[-1].iloc[-1]['vel_filtered']
                    heading_angle = float(ego_position_list[-1].iloc[-1]['headinga'])
                # start_speed = change_speed(start_speed)
                ego_trail_slices = Trail(trail_type, car_trail_data, ped_trail_data, trails_json_dict, ego_speed_status,
                                         single_scenario, ego_trail_section, start_speed, heading_angle).position
                '''需要增加未找到轨迹的报错判断'''
                if not ego_trail_slices.empty:
                    ego_position_list.append(ego_trail_slices)
                ego_trail_section += 1

            if ego_position_list:
                if len(ego_position_list) == 1:
                    print(single_scenario['scene_id'], "ego不需要拼接")
                    ego_trail = ego_position_list[0]
                elif len(ego_position_list) > 1:
                    ego_trail, ego_road = get_connect_trail(ego_position_list, scenario.scenario_dict['ego_trajectory'])
                else:
                    raise ValueError('请检查传参问题')

            else:
                print(scenario_series['场景编号'], "ego没有符合条件的轨迹, 失败")

            object_position_list = list()  # 二维数组,第一维度为不同的目标物，第二维度为相同目标物的分段轨迹形态
            for object_index in range(len(scenario['obs_start_velocity'])):
                object_status = scenario['obs_velocity_status'][object_index]
                object_trail_list = list()

                # 根据场景速度情况选择轨迹
                object_trail_section = 0
                for object_split_status in object_status:
                    trail_type = TrailType.vehicle_trail
                    object_trail = Trail(trail_type, car_trail_data, ped_trail_data, trails_json_dict,
                                         object_split_status,
                                         scenario, object_trail_section, object_index)

                    object_trail_section += 1
                    object_trail_list.append(object_trail.position)
                object_position_list.append(object_trail_list)
                if not object_trail_list:
                    print(scenario_series['场景编号'], "obs没有符合条件的轨迹")

                single_object_trail_list = list()
                object_position_trail_list = list()
                for object_trail in object_position_list:
                    single_obs_road_position_list = list()
                    pass
                    # 单个目标物有多种轨迹
                    # if len(object_trail) > 1:
                    #     obs_start_trail = object_trail[0].copy
                    #     single_obs_road_position = Point(obs_start_trail.iloc[-1]['ego_e'],
                    #                                      obs_start_trail.iloc[-1]['ego_n'])
                    #     pass
                    # elif not object_trail and scenario_series['场景编号'] not in "PCW":
                    #     print(scenario_series['场景编号'], "目标物轨迹为空", "匹配轨迹失败")
                    # # 单个目标物只有一种轨迹
                    # else:
                    #     single_object_trail_list.append(object_trail[0])

    print(fileCnt)


def variableSpeedObs(obsList, multiple):
    '''
    Parameters
    ----------
    obsList: 轨迹列表，必须包含（x,y）

    Returns: 返回处理后的轨迹列表
    -------

    '''
    dataFrameList = obsList
    rng = pd.date_range("2020-05-10 00:00:00", periods=len(dataFrameList), freq="T")
    if multiple >= 1:
        position = resample_bytime(dataFrameList, math.floor(multiple), rng, flag=True)
    else:
        position = resample_bytime(dataFrameList, math.ceil(multiple * 60), rng, flag=False)
    return position


def moveObs(obsList, mx, my):
    '''
    Parameters
    ----------
    obsList: 轨迹列表，必须包含（x,y）

    Returns: 返回处理后的轨迹列表
    -------

    '''
    obsList['ego_e'] = obsList['ego_e'] + mx
    obsList['ego_n'] = obsList['ego_n'] + my
    return obsList


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


def SpinTransformPoint(trail, deg):
    red = deg / 180 * math.pi
    a, b = rotate(trail['ego_e'], trail['ego_n'], 0, 0, red)
    trail['ego_e'] = a
    trail['ego_n'] = b
    trail['headinga'] += deg
    return trail


def trackStitching(egoST, splicedPosList, pos, trajectory, trajectoryPos):
    '''
    在轨迹list中寻找合适的轨迹拼接到egoST上，
    然后返回拼接egoST
    Parameters
    ----------
    egoST : 任意一条轨迹
    egoPosList ： 轨迹list
    pos : 上一类轨迹位置
    Returns
    -------

    '''
    if pos > len(splicedPosList):
        pos = pos % len(splicedPosList)
    for i in range(pos, len(splicedPosList)):  # 从pos开始匹配下一段路线轨迹
        for egoL in range(len(egoST) - 1):
            stSpeed = get_distance(
                Point(egoST.at[len(egoST) - egoL - 2, 'ego_e'], egoST.at[len(egoST) - egoL - 2, 'ego_n']),
                Point(egoST.at[len(egoST) - egoL - 1, 'ego_e'], egoST.at[len(egoST) - egoL - 1, 'ego_n'])) / 0.1
            if stSpeed > 0:
                break
        mPoint = Point(egoST.at[len(egoST) - 1, 'ego_e'], egoST.at[len(egoST) - 1, 'ego_n'])
        splicedPos = splicedPosList[i]
        splicedPos = splicedPos.reset_index(drop=True)

        for spL in range(len(splicedPos) - 1):
            splicedPosSpeed = get_distance(Point(splicedPos.at[spL, 'ego_e'], splicedPos.at[spL, 'ego_n']),
                                           Point(splicedPos.at[spL + 1, 'ego_e'],
                                                 splicedPos.at[spL + 1, 'ego_n'])) / 0.1
            if splicedPosSpeed > 0:
                break
        if np.isnan(stSpeed) or np.isnan(splicedPosSpeed):
            return [], []
        bIsAdd = False
        if BIsStitchingModificationSpeed == True:
            if trajectory[trajectoryPos - 1] not in '1':
                oldLength = len(splicedPos)
                multiple = stSpeed / splicedPosSpeed
                dataFrameList = splicedPos
                rng = pd.date_range("2020-05-10 00:00:00", periods=len(dataFrameList), freq="T")
                if multiple >= 1:
                    splicedPos = resample_bytime(dataFrameList, math.floor(multiple), rng, flag=True)
                else:
                    splicedPos = resample_bytime(dataFrameList, math.ceil(multiple * 60), rng, flag=False)
                if len(splicedPos) > oldLength:
                    splicedPos = splicedPos[:oldLength]
            else:
                oldLength = len(egoST)
                multiple = splicedPosSpeed / stSpeed
                dataFrameList = egoST
                rng = pd.date_range("2020-05-10 00:00:00", periods=len(dataFrameList), freq="T")
                if multiple >= 1:
                    egoST = resample_bytime(dataFrameList, math.floor(multiple), rng, flag=True)
                else:
                    egoST = resample_bytime(dataFrameList, math.ceil(multiple * 60), rng, flag=False)
                if (trajectoryPos - 1) == 0 and len(egoST) > oldLength:
                    egoST = egoST[:oldLength]
                mPoint = Point(egoST.at[len(egoST) - 1, 'ego_e'], egoST.at[len(egoST) - 1, 'ego_n'])
            bIsAdd = True
        elif math.fabs(stSpeed - splicedPosSpeed) < 2000:  # 两个轨迹间的速度差值小于2米每秒，认定适合拼接
            bIsAdd = True

        if bIsAdd:  # 两个轨迹间的速度差值小于2米每秒，认定适合拼接
            splicedPos['ego_e'] = splicedPos['ego_e'] + mPoint.x
            splicedPos['ego_n'] = splicedPos['ego_n'] + mPoint.y
            splicedPos = splicedPos[1:]
            oldegoST = copy.deepcopy(egoST)
            egoST = pd.concat([egoST, splicedPos], axis=0)
            egoST = egoST.reset_index(drop=True)
            return oldegoST, egoST
    for i in range(pos):  # 从pos开始匹配下一段路线轨迹
        egoL = 0
        for egoL in range(len(egoST) - 1):
            stSpeed = get_distance(
                Point(egoST.at[len(egoST) - egoL - 2, 'ego_e'], egoST.at[len(egoST) - egoL - 2, 'ego_n']),
                Point(egoST.at[len(egoST) - egoL - 1, 'ego_e'], egoST.at[len(egoST) - egoL - 1, 'ego_n'])) / 0.1
            if stSpeed > 0:
                break
        mPoint = Point(egoST.at[len(egoST) - 1, 'ego_e'], egoST.at[len(egoST) - 1, 'ego_n'])
        splicedPos = splicedPosList[i]
        splicedPos = splicedPos.reset_index(drop=True)
        spL = 0
        for spL in range(len(splicedPos) - 1):
            splicedPosSpeed = get_distance(Point(splicedPos.at[spL, 'ego_e'], splicedPos.at[spL, 'ego_n']),
                                           Point(splicedPos.at[spL + 1, 'ego_e'],
                                                 splicedPos.at[spL + 1, 'ego_n'])) / 0.1
            if splicedPosSpeed > 0:
                break
        bIsAdd = False
        if BIsStitchingModificationSpeed == True:
            if trajectory[trajectoryPos - 1] not in '1':
                oldLength = len(splicedPos)
                multiple = stSpeed / splicedPosSpeed
                dataFrameList = splicedPos
                rng = pd.date_range("2020-05-10 00:00:00", periods=len(dataFrameList), freq="T")
                if multiple >= 1:
                    splicedPos = resample_bytime(dataFrameList, math.floor(multiple), rng, flag=True)
                else:
                    splicedPos = resample_bytime(dataFrameList, math.ceil(multiple * 60), rng, flag=False)
                if len(splicedPos) > oldLength:
                    splicedPos = splicedPos[:oldLength]
            else:
                oldLength = len(egoST)
                multiple = splicedPosSpeed / stSpeed
                dataFrameList = egoST
                rng = pd.date_range("2020-05-10 00:00:00", periods=len(dataFrameList), freq="T")
                if multiple >= 1:
                    egoST = resample_bytime(dataFrameList, math.floor(multiple), rng, flag=True)
                else:
                    egoST = resample_bytime(dataFrameList, math.ceil(multiple * 60), rng, flag=False)
                if (trajectoryPos - 1) == 0 and len(egoST) > oldLength:
                    egoST = egoST[:oldLength]
                mPoint = Point(egoST.at[len(egoST) - 1, 'ego_e'], egoST.at[len(egoST) - 1, 'ego_n'])
            bIsAdd = True
        elif math.fabs(stSpeed - splicedPosSpeed) < 2000:  # 两个轨迹间的速度差值小于2米每秒，认定适合拼接
            bIsAdd = True

        if bIsAdd:  # 两个轨迹间的速度差值小于2米每秒，认定适合拼接
            splicedPos['ego_e'] = splicedPos['ego_e'] + mPoint.x
            splicedPos['ego_n'] = splicedPos['ego_n'] + mPoint.y
            splicedPos = splicedPos[1:]
            oldegoST = copy.deepcopy(egoST)
            egoST = pd.concat([egoST, splicedPos], axis=0)
            egoST = egoST.reset_index(drop=True)
            return oldegoST, egoST
    return [], []


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


def getTurnTo(carTrails, jsonList, turnAround, deg):
    '''

    Parameters
    ----------
    carTrails
    jsonList
    turnAround : 1 掉头，2 左转，3 右转

    Returns：返回List，每个元素是一条轨迹
    -------

    '''
    allJson = getJson(jsonList, TrajectoryTypeIndex)
    uniformSpeedJson = []
    for i in range(len(allJson)):
        jsoni = allJson[i][0]
        if turnAround == 1:
            if jsoni[TrajectoryTypeIndex] in ['uturn_left']:
                uniformSpeedJson += allJson[i]
        if turnAround == 2:
            # if jsoni[TrajectoryTypeIndex] in ['Left change lane']:
            if jsoni[TrajectoryTypeIndex] in ['crossing turn_left normal']:
                # if jsoni[TrajectoryTypeIndex] not in ["Right change lane", 'Right change lane+No change lane']:
                uniformSpeedJson += allJson[i]
        else:
            if jsoni[TrajectoryTypeIndex] in ['crossing turn_right normal']:
                # if jsoni[TrajectoryTypeIndex] in ["Right change lane", 'Right change lane+No change lane']:
                # if jsoni[TrajectoryTypeIndex] not in ['Left change lane','No change lane+Left change lane']:
                uniformSpeedJson += allJson[i]
    uniformSpeedJson = getSort(uniformSpeedJson, True)
    changeLaneJsonList = []
    for i in range(len(uniformSpeedJson)):
        jsoni = uniformSpeedJson[i]
        if turnAround == 1 and (jsoni[3] - jsoni[4] > 1):  # 掉头
            changeLaneJsonList.append(jsoni)
        elif turnAround == 2 and (jsoni[3] - jsoni[4] > 1):  # 左转向
            changeLaneJsonList.append(jsoni)
        elif turnAround == 3 and (jsoni[3] - jsoni[4] < -5):  # 右转向
            changeLaneJsonList.append(jsoni)
    trails = carTrails.copy()
    pos = []
    manyCsvList = []
    for i in range(len(changeLaneJsonList)):
        jsoni = changeLaneJsonList[i]
        trail_new = trails[(trails['Time'] <= float(jsoni[StopTime])) & (trails['Time'] >= float(jsoni[StartTime]))]
        trail_new = trail_new.reset_index(drop=True)
        trail_new = originTrails(trail_new)
        if len(trail_new) < 5:
            continue
        flag = trail_new.duplicated(subset=['ego_e', 'ego_n'])
        flag = flag.values.tolist()
        if True in flag:
            continue
        tCsvList = []
        bIsAddTrajectory = False
        previousX = trail_new.at[len(trail_new) - 1, 'ego_e']
        previousY = trail_new.at[len(trail_new) - 1, 'ego_n']
        previousAngle = trail_new.at[len(trail_new) - 1, 'headinga']
        tCsvList.append(trail_new)
        if turnAround == 3 or turnAround == 2:
            # if (math.fabs(trail_new.at[len(trail_new) - 1, 'headinga'] - trail_new.at[0, 'headinga']) >= 90
            #      and (math.fabs(trail_new.at[len(trail_new) - 1, 'headinga'] - trail_new.at[0, 'headinga']) <= 100)):
            manyCsvList.append(tCsvList)
            continue
        elif turnAround == 1:
            # if (math.fabs(trail_new.at[len(trail_new) - 1, 'headinga'] - trail_new.at[0, 'headinga']) >= 180
            #      and (math.fabs(trail_new.at[len(trail_new) - 1, 'headinga'] - trail_new.at[0, 'headinga']) <= 190)):
            manyCsvList.append(tCsvList)
            continue
        for j in range(i + 1, len(changeLaneJsonList)):
            jsoni = changeLaneJsonList[j]
            trail_new = trails[(trails['Time'] <= float(jsoni[StopTime])) & (trails['Time'] >= float(jsoni[StartTime]))]
            # if len(trail_new) < 5:
            #     continue
            trail_new = trail_new.reset_index(drop=True)
            trail_new = originTrails(trail_new)

            x, y = translationAndRotation(trail_new.at[len(trail_new) - 1, 'ego_e'],
                                          trail_new.at[len(trail_new) - 1, 'ego_n'], previousAngle, previousX,
                                          previousY)
            if math.fabs(previousX - x) / len(trail_new) < 0.01:
                continue
            if turnAround == 3:
                if trail_new.at[len(trail_new) - 1, 'headinga'] + previousAngle > 90 and trail_new.at[
                    len(trail_new) - 1, 'headinga'] + previousAngle < (90 + 10):
                    tCsvList.append(trail_new)
                    bIsAddTrajectory = True
                    break
                elif trail_new.at[len(trail_new) - 1, 'headinga'] + previousAngle < 90:
                    previousX = x
                    previousY = y
                    previousAngle = trail_new.at[len(trail_new) - 1, 'headinga'] + previousAngle
                    tCsvList.append(trail_new)
            elif turnAround == 2 or turnAround == 1:
                if turnAround == 2:
                    steeringAngle = -90
                else:
                    steeringAngle = -180
                if trail_new.at[len(trail_new) - 1, 'headinga'] + previousAngle > (steeringAngle - 50) and trail_new.at[
                    len(trail_new) - 1, 'headinga'] + previousAngle < steeringAngle:
                    tCsvList.append(trail_new)
                    bIsAddTrajectory = True
                    break
                elif trail_new.at[len(trail_new) - 1, 'headinga'] + previousAngle > steeringAngle:
                    previousX = x
                    previousY = y
                    previousAngle = trail_new.at[len(trail_new) - 1, 'headinga'] + previousAngle
                    tCsvList.append(trail_new)
        if bIsAddTrajectory == True:
            manyCsvList.append(tCsvList)
            if len(manyCsvList) >= MaximumNumberNfSameTrajectories:
                break
    for l in range(len(manyCsvList)):
        tCsvList = manyCsvList[l]
        a = tCsvList[0]
        c = tCsvList[0]
        for k in range(1, len(tCsvList)):
            b = get_merge_trails(a, tCsvList[k])
            b = b[1:]
            b = b.reset_index(drop=True)
            a = b
            c = pd.concat([c, b], axis=0)
            c = c.reset_index(drop=True)

        for index in range(len(c)):
            if (turnAround == 2 and c.at[index, 'headinga'] < -90) \
                    or (turnAround == 3 and c.at[index, 'headinga'] > 90) \
                    or (turnAround == 1 and c.at[index, 'headinga'] < -180):
                c = c[:index]
                break

        # if math.fabs(math.fabs(c.at[len(c) - 1,'ego_e']) - math.fabs(c.at[len(c) - 1,'ego_n'])) > 1 and turnAround != 1:
        #     continue
        c = SpinTransform(c, "ego_e", "ego_n", c.copy(), -c.at[0, 'headinga'] + deg)
        startPoint = Point(c.at[0, 'ego_e'], c.at[0, 'ego_n'])
        c['ego_e'] = c['ego_e'] - startPoint.x
        c['ego_n'] = c['ego_n'] - startPoint.y
        c = c.reset_index(drop=True)
        pos.append(c)
        # fig = plt.figure(figsize=(20, 10))
        # ax1 = fig.add_subplot(1, 1, 1)
        # ax1.set_title('ENU Coordinates')
        # ax1.set_xlabel('East')
        # ax1.set_ylabel('North')
        # ax1.scatter(c['ego_e'], c['ego_n'], s=20, marker='.', label="Ego car" + str(i))
        # plt.show()
        if len(pos) >= MaximumNumberNfSameTrajectories:
            return pos
    # spacing = int(len(pos) / (MaximumNumberNfSameTrajectories / 10))
    # if spacing == 1:
    #     pos1 = pos[:int(MaximumNumberNfSameTrajectories / 10)]
    # else:
    #     pos1 = pos[0:len(pos):spacing]
    return pos


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


def zhuanDataFram(dataList):
    time = []
    ObjectID = []
    ObjectType = []
    y = []
    x = []
    h = []
    vel = []
    for i in range(len(dataList)):
        time.append(dataList[i].time)
        ObjectID.append(dataList[i].ObjectID)
        ObjectType.append(dataList[i].ObjectType)
        y.append(dataList[i].y)
        x.append(dataList[i].x)
        h.append(dataList[i].h)
        vel.append(dataList[i].vel)
    c = {"time": time,
         "ObjectID": ObjectID,
         "ObjectType": ObjectType,
         "y": y,
         "x": x,
         "h": h,
         "vel": vel}
    return pd.DataFrame(c)


if __name__ == "__main__":
    parsingConfigurationFile("D:/泛化", ['AEB'])
