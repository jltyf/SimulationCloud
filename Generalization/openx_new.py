#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 15:44:01 2022

@author: lxj
"""
import xml.etree.ElementTree as ET
from scenariogeneration import xodr
from scenariogeneration import xosc
from scenariogeneration import ScenarioGenerator
from scenariogeneration.xodr import RoadSide, Object, ObjectType, Dynamic, Orientation
import math, os
from xodr_generator2 import road_detector_new
from datetime import datetime
import traceback
import json
import pandas as pd


class Scenario(ScenarioGenerator):
    def __init__(self, gps, obs, ObjectID, gpsTime, egoSpeed, Speed, intersectime, augtype, sceperiod, abspath):
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
        self.abspath = abspath

    def road_ego(self, **kwargs):
        positionEgo = self.gps
        planview = xodr.PlanView()

        for i in range(len(positionEgo) - 1):
            x = 0.000001 if abs(positionEgo[i].x) < 0.000001 else positionEgo[i].x
            y = 0.000001 if abs(positionEgo[i].y) < 0.000001 else positionEgo[i].y
            nextx = 0.000001 if abs(positionEgo[i + 1].x) < 0.000001 else positionEgo[i + 1].x
            nexty = 0.000001 if abs(positionEgo[i + 1].y) < 0.000001 else positionEgo[i + 1].y
            h = float(positionEgo[i].h)

            planview.add_fixed_geometry(xodr.Line(math.sqrt(math.pow(nextx - x, 2) + math.pow(nexty - y, 2))), x, y, h)

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
        odr = xodr.OpenDrive('myroad')
        # 静态元素
        tree = ET.parse(os.getcwd() + '/models/static_object_models.xodr')
        root = tree.getroot()
        objects_dict = root.iter(tag='object')
        road = create_static_object(road, objects_dict)

        # road = create_static_object(road, object_id=0, object_type=ObjectType.railing, repeat_flag=1)
        odr.add_road(road)
        odr.adjust_roads_and_lanes()
        return odr

    def get_section(self, left_lanemark):
        return None

    def split_road_section(self, enu_file, lane_file):
        lane_content = pd.read_csv(lane_file)
        # 把车道分割开来，一个车道段，多种geometry
        # 首先判断车道线数值是否有断裂，断裂处根据自车轨迹生成道路参数
        left_lanemark = lane_content[lane_content['LaneID'] == 1][['Time', 'FrameID', 'LanePosition', 'LaneQuality']]
        right_lanemark = lane_content[lane_content['LaneID'] == 2][['Time', 'FrameID', 'LanePosition', 'LaneQuality']]

        left_break_section = self.get_section(left_lanemark, 1)
        right_break_section = self.get_section(right_lanemark, 1)
        break_section = []
        normal_section = []

        # 判断是否变道，然后判断是否弯道

        # 最终目标是得到多个geometry参数，确定每个连接线处的s/t偏移量?，以及左右道路的个数和宽度

        return None

    def road(self, **kwargs):
        polyfit_fig_path = os.path.join(self.abspath, 'simulation', 'polyfit.jpg')

        # run road detector
        enu_file = os.path.join(self.abspath, 'pos.csv')
        lane_file = os.path.join(self.abspath, 'lane.csv')

        # road split sections
        self.split_road_section(enu_file, lane_file)

        try:
            laneid_tuple = [0, 1, 2, 3]
            uv_coord_info, road_info, left_lane_info, right_lane_info = road_detector_new(enu_file, lane_file,
                                                                                          laneid_tuple,
                                                                                          polyfit_fig_path)
        except:
            print('road detection failed!!!!  Use ego trail road.')
            error = {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 'traceback': traceback.format_exc()}
            with open('error.log', 'a+') as f:
                json.dump(error, f, indent=4)
                f.write('\n')
            return self.road_ego()

        origin_x = uv_coord_info[0]
        origin_y = uv_coord_info[1]
        uv_coord_hdg = uv_coord_info[2]

        reference_line_offset = road_info[0]
        model_u = road_info[1]  # in fomrat [c3, c2, c1, c0]
        model_v = road_info[2]  # in fomrat [c3, c2, c1, c0]
        road_length = road_info[3]
        print(uv_coord_info)
        print(road_info)
        # generate xodr file
        planview = xodr.PlanView(origin_x, origin_y, uv_coord_hdg)

        # Create geometry and add it to the planview
        # parampoly3 = xodr.ParamPoly3(au=model_u[3], bu=model_u[2], cu=model_u[1], du=model_u[0], av=model_v[3], bv=model_v[2], cv=model_v[1], dv=model_v[0], prange='arcLength',length=road_length)
        parampoly3 = xodr.ParamPoly3(au=0, bu=model_u[2], cu=model_u[1], du=model_u[0], av=0, bv=model_v[2],
                                     cv=model_v[1], dv=model_v[0], prange='arcLength', length=road_length)
        planview.add_geometry(parampoly3)

        # create two different roadmarkings
        rm_solid = xodr.RoadMark(xodr.RoadMarkType.solid, 0.2)
        rm_dashed = xodr.RoadMark(xodr.RoadMarkType.broken, 0.2, laneChange=xodr.LaneChange.both)

        ##4. Create centerlane 
        centerlane = xodr.Lane(a=reference_line_offset)
        centerlane.add_roadmark(rm_dashed)

        ##5. Create lane section form the centerlane
        lanesec = xodr.LaneSection(0, centerlane)

        ##6. Create left and right lanes
        lane_id = 0
        for lane in left_lane_info:
            lane_id += 1
            lane_width = lane[0]
            spd_limit = lane[1]
            lane_left = xodr.Lane(a=lane_width)
            lane_left.add_roadmark(rm_dashed)
            # Add lanes to lane section 
            lanesec.add_left_lane(lane_left)

        lane_id = 0
        for lane in right_lane_info:
            lane_id -= 1
            lane_width = lane[0]
            spd_limit = lane[1]
            lane_right = xodr.Lane(a=lane_width)
            lane_right.add_roadmark(rm_dashed)
            # Add lanes to lane section 
            lanesec.add_right_lane(lane_right)

        ##8. Add lane section to Lanes 
        lanes = xodr.Lanes()
        lanes.add_laneoffset(xodr.LaneOffset(s=0, a=reference_line_offset))
        lanes.add_lanesection(lanesec)

        ##9. Create Road from Planview and Lanes
        road = xodr.Road(1, planview, lanes)

        ##10. Create the OpenDrive class (Master class)
        odr = xodr.OpenDrive('myroad')

        ##11. Finally add roads to Opendrive 
        odr.add_road(road)

        ##12. Adjust initial positions of the roads looking at succ-pred logic 
        odr.adjust_roads_and_lanes()

        # ##13. Print the .xodr file
        # xodr.prettyprint(odr.get_element())

        # ##14. Run the .xodr with esmini 
        # xodr.run_road(odr,os.path.join('..','pyoscx','esmini'))

        return odr

    def getXoscPosition(egodata, t, e, n, h, offset_x, offset_y, offset_h):
        '将dataframe的轨迹转换为场景文件的轨迹数据, Time, ego_e, ego_n, headinga'

        position = []
        time = []
        egodata = egodata[[t, e, n, h]]
        egodata = egodata.reset_index(drop=True)
        egodata[t] = egodata.index / 10
        egodata[e] = egodata[e] + offset_x
        egodata[n] = egodata[n] + offset_y
        egodata[h] = egodata[h] + offset_h
        egodata[h] = egodata.apply(lambda x: x[h] if x[h] < 360 else x[h] - 360, axis=1)

        lasth = float(egodata.at[0, h])
        init_flag = True

        for row in egodata.iterrows():
            hhh = math.radians(row[1][h])
            if init_flag:
                position.append(xosc.WorldPosition(x=float(row[1][e]), y=float(row[1][n]), z=0, h=hhh, p=0, r=0))
                init_flag = False
            else:
                if float(row[1][h]) - lasth > 300:
                    hhh = math.radians(float(row[1][h]) - 360)
                elif float(row[1][h]) - lasth < -300:
                    hhh = math.radians(float(row[1][h]) + 360)
                position.append(xosc.WorldPosition(x=float(row[1][e]), y=float(row[1][n]), z=0, h=hhh, p=0, r=0))
                lasth = hhh
            time.append(float(row[1][t]))
        return position, time

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
            entities.add_scenario_object(objname + str(0), male_ped)
            if len(self.obs) >= 2:
                for i in range(1, len(self.obs)):
                    row = self.obs[i]
                    entities.add_scenario_object(objname + str(i), white_veh, cnt2)

        positionEgo = self.gps
        positionObj = self.obs
        init = xosc.Init()
        step_time = xosc.TransitionDynamics(xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 0)
        step_time1 = xosc.TransitionDynamics(xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 1)
        egospeed = xosc.AbsoluteSpeedAction(self.egoSpeed, step_time)
        objspeed = xosc.AbsoluteSpeedAction(self.Speed, step_time1)

        # ego car init
        ego_init_h = positionEgo[0].h
        init.add_init_action(egoname, xosc.TeleportAction(
            xosc.WorldPosition(x=positionEgo[0].x, y=positionEgo[0].y, z=0, h=ego_init_h, p=0, r=0)))
        init.add_init_action(egoname, egospeed)

        # object car init
        if positionObj:
            for i in range(len(positionObj)):
                row = positionObj[i]
                name = objname + str(i)
                x = row[0][0].x
                y = row[0][0].y
                obj_init_h = row[0][0].h
                init.add_init_action(name,
                                     xosc.TeleportAction(xosc.WorldPosition(x=x, y=y, z=0, h=obj_init_h, p=0, r=0)))
                init.add_init_action(name, objspeed)

        # ego car trail
        trajectory = xosc.Trajectory('egoTrajectory', False)
        polyline = xosc.Polyline(self.gpsTime, positionEgo)
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

        # object car trail
        if positionObj:
            pedflag = False
            if self.augtype == 7:
                pedflag = True
            for i in range(len(positionObj)):
                row = positionObj[i]
                name = objname + str(i)

                trajectoryM = xosc.Trajectory('objectTrajectory', False)
                polylineM = xosc.Polyline(row[1], row[0])
                trajectoryM.add_shape(polylineM)

                speedaction2 = xosc.FollowTrajectoryAction(trajectoryM, xosc.FollowMode.position,
                                                           xosc.ReferenceContext.absolute, 1, 0)

                event2 = xosc.Event('Event1', xosc.Priority.overwrite)
                # trigger2 = xosc.EntityTrigger("obj-start-trigger", step_dataM[0], xosc.ConditionEdge.rising, xosc.SpeedCondition(0, xosc.Rule.greaterThan),'Ego')
                trigger2 = xosc.EntityTrigger("obj-start-trigger", 0, xosc.ConditionEdge.rising,
                                              xosc.SpeedCondition(0, xosc.Rule.greaterThan), 'Ego')
                event2.add_trigger(trigger2)

                if pedflag:
                    pedaction = xosc.FollowTrajectoryAction(trajectoryM, xosc.FollowMode.position,
                                                            xosc.ReferenceContext.absolute, 1, 0)
                    event2.add_action('newspeed', pedaction)
                    # walp_trigger =  xosc.EntityTrigger('ped_walp_trigger', 0, xosc.ConditionEdge.rising,\
                    # xosc.TimeToCollisionCondition(self.intersectime, xosc.Rule.lessThan, entity=name), 'Ego')
                    # event2.add_trigger(walp_trigger)

                else:
                    event2.add_action('newspeed', speedaction2)

                man = xosc.Maneuver('my maneuver')
                man.add_event(event2)

                event3 = xosc.Event('Event_ped', xosc.Priority.overwrite)
                event3.add_trigger(trigger)

                if pedflag:
                    action3 = xosc.CustomCommandAction(0, 0, 0, 0, 1, 0, 0)
                    action3.add_element(self.createUDAction())
                    event3.add_action('newspeed', action3)
                    man.add_event(event3)

                    # finish_trigger = xosc.EntityTrigger('finish_trigger', 0, xosc.ConditionEdge.rising, xosc.ReachPositionCondition(position=row[1][0],tolerance=1),name)
                    # event4 = xosc.Event('Event_ped',xosc.Priority.overwrite)
                    # event4.add_trigger(finish_trigger)
                    # be_still_action = xosc.AbsoluteSpeedAction(0, xosc.TransitionDynamics(xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 1))
                    # event4.add_action('ped_be_still_action',be_still_action)
                    # man.add_event(event4)

                mangr2 = xosc.ManeuverGroup('mangroup', selecttriggeringentities=True)
                mangr2.add_actor(name)
                mangr2.add_maneuver(man)

                act2 = xosc.Act('Act1', trigger0)
                act2.add_maneuver_group(mangr2)

                story2 = xosc.Story('mystory_' + name)
                story2.add_act(act2)

                sb.add_story(story2)
                pedflag = False
        # prettyprint(sb.get_element())

        paramet = xosc.ParameterDeclarations()

        sce = xosc.Scenario('my scenario', 'Maggie', paramet, entities, sb, road, catalog)
        return sce

    def createUDAction(self, **kwargs):
        tree = ET.parse(
            '/home/lxj/Documents/git_project/SimulationCloud/SimulationCloud/Generalization/models/ped_CDATA.xosc')
        root = tree.getroot()
        ele = root[5][2][1][0][1][1][0][0][0]
        newnode = ET.Element("CustomCommandAction")
        newnode.attrib = {'type': 'scp'}
        newnode.text = '<![CDATA[' + ele.text + ']]>'
        return newnode


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


def change_CDATA(filepath):
    '行人场景特例，对xosc文件内的特殊字符做转换'
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


def path_changer(xosc_path, xodr_path, osgb_path):
    """
    provided by Dongpeng Ding
    :param xosc_path:
    :param xodr_path:
    :param osgb_path:
    :return:
    """
    tree = ET.parse(xosc_path)
    treeRoot = tree.getroot()

    # for OpenScenario v0.9, v1.0
    for RoadNetwork in treeRoot.findall('RoadNetwork'):

        for Logics in RoadNetwork.findall('LogicFile'):
            Logics.attrib['filepath'] = xodr_path
        for SceneGraph in RoadNetwork.findall('SceneGraphFile'):
            SceneGraph.attrib['filepath'] = osgb_path

        for Logics in RoadNetwork.findall('Logics'):
            Logics.attrib['filepath'] = xodr_path
        for SceneGraph in RoadNetwork.findall('SceneGraph'):
            SceneGraph.attrib['filepath'] = osgb_path

    # for VTD xml
    for Layout in treeRoot.findall('Layout'):
        Layout.attrib['File'] = xodr_path
        Layout.attrib['Database'] = osgb_path

    tree.write(xosc_path, xml_declaration=True)


def readXML(xoscPath):
    xodrFileName = ""
    osgbFileName = ""

    tree = ET.parse(xoscPath)
    treeRoot = tree.getroot()

    for RoadNetwork in treeRoot.findall('RoadNetwork'):

        for Logics in RoadNetwork.findall('LogicFile'):
            xodrFileName = Logics.attrib['filepath']
        for SceneGraph in RoadNetwork.findall('SceneGraphFile'):
            osgbFileName = SceneGraph.attrib['filepath']

        for Logics in RoadNetwork.findall('Logics'):
            xodrFileName = Logics.attrib['filepath']
        for SceneGraph in RoadNetwork.findall('SceneGraph'):
            osgbFileName = SceneGraph.attrib['filepath']

    return xodrFileName[xodrFileName.rindex("/") + 1:], osgbFileName[osgbFileName.rindex("/") + 1:]


def formatThree(rootDirectory):
    """
    xodr and osgb file path are fixed
    :return:
    """

    for root, dirs, files in os.walk(rootDirectory):
        for file in files:
            if ".xosc" == file[-5:]:
                # xodrFilePath = "/volume4T/goodscenarios/generalization/toyiqi/model/Rd_001.xodr" # 泛化效果好的场景用的
                # osgbFilePath = "/volume4T/goodscenarios/generalization/toyiqi/model/Rd_001.osgb" # 泛化效果好的场景用的
                # xodrFilePath = "/volume4T/goodscenarios/generalization/toyiqi/model/Cross.xodr"  # 泛化效果好的场景用的
                # osgbFilePath = "/volume4T/goodscenarios/generalization/toyiqi/model/Cross.osgb"  # 泛化效果好的场景用的
                xodrFilePath = "/home/lxj/wendang_lxj/L4/L4_scenarios/piliang_model/China_UrbanRoad_014.xodr"  # 直路，泛化好用
                osgbFilePath = "/home/lxj/wendang_lxj/L4/L4_scenarios/piliang_model/China_UrbanRoad_014.opt.osgb"  # 直路，泛化好用
                # xodrFilePath = "/home/lxj/wendang_lxj/L4/L4_scenarios/piliang_model/China_Crossing_002.xodr"       # 十字路口，泛化好用
                # osgbFilePath = "/home/lxj/wendang_lxj/L4/L4_scenarios/piliang_model/China_Crossing_002.opt.osgb"   # 十字路口，泛化好用
                # xodrFilePath = "/home/lxj/wendang_lxj/Sharing_VAN/homework/test/DF_yuexiang_1224.xodr"       # Sharing-van还原用的
                # osgbFilePath = "/home/lxj/wendang_lxj/Sharing_VAN/homework/test/DF_yuexiang_1224.opt.osgb"   # Sharing-van还原用的

                path_changer(root + "/" + file, xodrFilePath, osgbFilePath)
                print("Change success: " + root + "/" + file)


def formatTwo(rootDirectory):
    """
    data format:
    simulation
        file.xosc
        file.xodr
        file.osgb
    :return:
    """
    for root, dirs, files in os.walk(rootDirectory):
        for file in files:
            if ".xosc" == file[-5:]:

                xodrFilePath = ""
                osgbFilePath = ""

                for odrFile in os.listdir(root):
                    if ".xodr" == odrFile[-5:]:
                        xodrFilePath = root + "/" + odrFile
                        break

                for osgbFile in os.listdir(root):
                    if ".osgb" == osgbFile[-5:]:
                        osgbFilePath = root + "/" + osgbFile
                        break

                path_changer(root + "/" + file, xodrFilePath, osgbFilePath)
                print("Change success: " + root + "/" + file)


def formatOne(rootDirectory):
    """
    data format:
        openx
            xosc
                file.xosc
            xodr
                file.xodr
            osgb
                file.osgb
    :return:
    """
    for root, dirs, files in os.walk(rootDirectory):
        for file in files:
            if "xosc" == file[-4:]:

                xodrFilePath = ""
                osgbFilePath = ""

                for odrFile in os.listdir(root[:-4] + "xodr"):
                    if "xodr" == odrFile[-4:]:
                        xodrFilePath = root[:-4] + "xodr/" + odrFile
                        break

                for osgbFile in os.listdir(root[:-4] + "osgb"):
                    if "osgb" == osgbFile[-4:]:
                        osgbFilePath = root[:-4] + "osgb/" + osgbFile
                        break

                path_changer(root + "/" + file, xodrFilePath, osgbFilePath)
                print("Change success: " + root + "/" + file)


def chongQingFormat(rootDirectory):
    """
    supporting file format: chong qing folder format
    :return:
    """

    counter = 1

    for root, dirs, files in os.walk(rootDirectory):
        for file in files:
            if "xosc" == file[-4:]:
                if "ver1.0.xosc" == file[-11:]:

                    xodrFileName, osgbFileName = readXML(root + "/" + file)

                    xodrFilePath = "/Xodrs/" + xodrFileName
                    osgbFilePath = "/Databases/" + osgbFileName

                    path_changer(root + "/" + file, xodrFilePath, osgbFilePath)
                    print(counter, "Change success: " + root + "/" + file)
                else:
                    xodrFileName, osgbFileName = readXML(root + "/" + file)

                    xodrFilePath = "/Xodrs/" + xodrFileName
                    osgbFilePath = "/Databases/" + osgbFileName

                    path_changer(root + "/" + file, xodrFilePath, osgbFilePath)
                    print(counter, "Change success: " + root + "/" + file)
                counter += 1
