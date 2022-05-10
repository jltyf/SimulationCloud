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
from scenariogeneration.xodr import RoadSide, Object, Dynamic, Orientation
import math
import os

from Generalization.utils import create_static_object
from enumerations import Weather, ObjectType


class Scenario(ScenarioGenerator):
    def __init__(self, gps, obs, ObjectID, gpsTime, egoSpeed, Speed, intersectime, aug_type, period, weather, time):
        ScenarioGenerator.__init__(self)
        self.gps = gps
        self.obs = obs
        self.gpsTime = gpsTime
        self.ObjectID = ObjectID
        self.egoSpeed = egoSpeed
        self.Speed = Speed
        self.intersectime = intersectime
        self.aug_type = aug_type
        self.period = period
        time_list = time.split(':')
        self.time = (True, 2019, 12, 19, int(time_list[0]), int(time_list[1]), int(time_list[2]))
        self.weather = weather

    def road(self):
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

    def scenario(self):
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
        if self.aug_type == ObjectType.motorcycle.value:
            white_veh = xosc.Vehicle('Kawasaki_ZX-9R_black', xosc.VehicleCategory.motorbike, bb, fa, ba, 69.444, 200, 10)

        prop = xosc.Properties()
        cnt = xosc.Controller('DefaultDriver', prop)
        cnt2 = xosc.Controller('No Driver', prop)

        egoname = 'Ego'
        entities = xosc.Entities()
        entities.add_scenario_object(egoname, red_veh, cnt)
        objname = 'Player'

        if self.aug_type != 1:

            # object car model
            for i in range(len(self.obs)):
                row = self.obs[i]
                entities.add_scenario_object(objname + str(i), white_veh, cnt2)

        elif self.aug_type == 1:

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
                                                                 xosc.SimulationTimeCondition(self.period,
                                                                                              xosc.Rule.greaterThan),
                                                                 'stop'))
        sb.add_story(story1)

        # object car trail
        if positionObj:
            pedflag = False
            if self.aug_type == 1:
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
        self.create_environment(init)

        sce = xosc.Scenario('my scenario', 'Maggie', paramet, entities, sb, road, catalog)
        return sce

    def createUDAction(self, **kwargs):
        ped_path = os.path.join(os.getcwd(), 'models/ped_CDATA.xosc')
        tree = ET.parse(ped_path)
        # '/home/lxj/Documents/git_project/SimulationCloud/SimulationCloud/Generalization/models/ped_CDATA.xosc')
        root = tree.getroot()
        ele = root[5][2][1][0][1][1][0][0][0]
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
