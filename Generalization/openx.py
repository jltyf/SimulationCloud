#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 15:44:01 2022

@author: lxj
"""
import math
import os
import json
import traceback
import pandas as pd
import xml.etree.ElementTree as ET
from scenariogeneration import xodr
from scenariogeneration import xosc
from scenariogeneration import ScenarioGenerator
from scenariogeneration.xodr import RoadSide, Object, ObjectType, Dynamic, Orientation
from datetime import datetime
from xodr_generator2 import road_detector_new
from Generalization.utils import create_static_object, get_entity_properties
from enumerations import Weather, ObjectType


class Scenario(ScenarioGenerator):
    def __init__(self, gps, obs, gpsTime, period, single_scenario, abspath):
        ScenarioGenerator.__init__(self)
        self.gps = gps
        self.obs = obs
        self.gpsTime = gpsTime
        self.ObjectID = 0
        self.egoSpeed = 5
        self.Speed = 0
        self.period = period
        self.abspath = abspath
        self.single_scenario = single_scenario
        time_list = single_scenario['scenario_time'][0].split(':')
        self.time = (True, 2019, 12, 19, int(time_list[0]), int(time_list[1]), int(time_list[2]))
        self.weather = single_scenario['scenario_weather'][0]
        self.entity_models = None

    def road_ego(self):
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

    def road(self):
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

    def scenario(self):
        road = xosc.RoadNetwork(self.road_file, scenegraph="/simulation0.osgb")

        catalog = xosc.Catalog()
        catalog.add_catalog('VehicleCatalog', 'Distros/Current/Config/Players/Vehicles')
        catalog.add_catalog('PedestrianCatalog', 'Distros/Current/Config/Players/Pedestrians')
        catalog.add_catalog('ControllerCatalog', 'Distros/Current/Config/Players/driverCfg.xml')
        if 'obs_type' in self.single_scenario.keys():
            self.entity_models = get_entity_properties([self.single_scenario['scenario_vehicle_model'],
                                                        *self.single_scenario['obs_type']])
        else:
            self.entity_models = get_entity_properties([self.single_scenario['scenario_vehicle_model']])
        prop = xosc.Properties()
        cnt = xosc.Controller('DefaultDriver', prop)
        cnt2 = xosc.Controller('No Driver', prop)

        egoname = 'Ego'
        entities = xosc.Entities()
        entities.add_scenario_object(egoname, self.entity_models[0], cnt)
        objname = 'Player'

        for index, entity in enumerate(self.entity_models[1:]):
            entities.add_scenario_object(objname + str(index), entity, cnt2)

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
                                                                 xosc.SimulationTimeCondition(self.period,
                                                                                              xosc.Rule.greaterThan),
                                                                 'stop'))
        sb.add_story(story1)

        # object car trail
        if positionObj:
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
                if int(self.single_scenario['obs_type'][i]) == ObjectType.pedestrian.value:
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

                if int(self.single_scenario['obs_type'][i]) == ObjectType.pedestrian.value:
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
        # prettyprint(sb.get_element())

        paramet = xosc.ParameterDeclarations()
        self.create_environment(init)

        sce = xosc.Scenario('my scenario', 'Maggie', paramet, entities, sb, road, catalog)
        return sce

    def createUDAction(self, **kwargs):
        ped_path = os.path.join(os.getcwd(), 'models/ped_CDATA.xosc')
        tree = ET.parse(ped_path)
        # '/home/lxj/Documents/git_project/SimulationCloud/SimulationCloud/Generalization/models/ped_CDATA.xosc')
        root = tree.getroot()
        ele = root[5][2][1][0][1][1][0][0][0]
        # ele.text.replace('speed="3"', f'speed="{}"')
        newnode = ET.Element("CustomCommandAction")
        newnode.attrib = {'type': 'scp'}
        newnode.text = '<![CDATA[' + ele.text + ']]>'
        return newnode

    # 创建场景天气
    def create_environment(self, init):
        cloud_state = xosc.CloudState.free
        precipitation = xosc.PrecipitationType.dry
        visual_fog_range = 2000
        if self.weather == Weather.foggy.value:
            visual_fog_range = 500
        if self.weather == Weather.rainy.value:
            precipitation = xosc.PrecipitationType.rain
        elif self.weather == Weather.snowy.value:
            precipitation = xosc.PrecipitationType.snow
        init.add_global_action(
            xosc.EnvironmentAction(name="InitEnvironment", environment=xosc.Environment(
                xosc.TimeOfDay(*self.time),
                xosc.Weather(
                    sun_intensity=2000, sun_azimuth=40, sun_elevation=20,
                    cloudstate=cloud_state,
                    precipitation=precipitation,
                    precipitation_intensity=1,
                    visual_fog_range=visual_fog_range),
                xosc.RoadCondition(friction_scale_factor=0.7))))
