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


def get_entity_properties(object_type_list):
    object_model = list()
    for index, object_type in enumerate(object_type_list):
        object_type = int(object_type)
        if object_type == ObjectType.vehicle.value:
            name = 'Audi_A3_2009_red'
            if index == 0:
                name = 'Audi_A3_2009_black'
            vehicle_type = xosc.VehicleCategory.car
            bounding_box = xosc.BoundingBox(width=1.776, length=4.3, height=1.423, x_center=1.317, y_center=0,
                                            z_center=0.8)
            front_axle = xosc.Axle(maxsteer=27.5, wheeldia=0.641, track_width=1.456, xpos=1.317, zpos=0.8)
            rear_axle = xosc.Axle(maxsteer=0, wheeldia=0.641, track_width=1.456, xpos=1.317, zpos=0.8)
            max_speed = 210
            max_acceleration = 7
            max_deceleration = 9.5
            car = xosc.Vehicle(name=name, vehicle_type=vehicle_type, boundingbox=bounding_box,
                               frontaxle=front_axle, rearaxle=rear_axle, max_speed=max_speed,
                               max_acceleration=max_acceleration, max_deceleration=max_deceleration)
            object_model.append(car)
        elif object_type == ObjectType.bus.value:
            name = 'MB_Citaro_2007_yellow'
            if index == 0:
                name = 'MB_Citaro_2007_red'
            vehicle_type = xosc.VehicleCategory.bus
            bounding_box = xosc.BoundingBox(width=2.56, length=11.957, height=3.14, x_center=2.5525, y_center=0,
                                            z_center=1.6)
            front_axle = xosc.Axle(maxsteer=27.5, wheeldia=1, track_width=2.07, xpos=3.5525, zpos=1.6)
            rear_axle = xosc.Axle(maxsteer=0, wheeldia=1, track_width=2.07, xpos=2.5525, zpos=1.6)
            max_speed = 109.8
            max_acceleration = 3
            max_deceleration = 9.5
            bus = xosc.Vehicle(name=name, vehicle_type=vehicle_type, boundingbox=bounding_box,
                               frontaxle=front_axle, rearaxle=rear_axle, max_speed=max_speed,
                               max_acceleration=max_acceleration, max_deceleration=max_deceleration)
            object_model.append(bus)
        elif object_type == ObjectType.truck.value:
            name = 'MANTGS_11_Green'
            if index == 0:
                name = 'MANTGS_11_LightBlue'
            vehicle_type = xosc.VehicleCategory.truck
            bounding_box = xosc.BoundingBox(width=2.8, length=8.744, height=3.78, x_center=2.028, y_center=0,
                                            z_center=1.8)
            front_axle = xosc.Axle(maxsteer=27.5, wheeldia=1.1, track_width=2.32, xpos=2.025, zpos=1.8)
            rear_axle = xosc.Axle(maxsteer=0, wheeldia=1.1, track_width=2.321, xpos=2.028, zpos=1.8)
            max_speed = 95.04
            max_acceleration = 3
            max_deceleration = 9.5
            truck = xosc.Vehicle(name=name, vehicle_type=vehicle_type, boundingbox=bounding_box,
                                 frontaxle=front_axle, rearaxle=rear_axle, max_speed=max_speed,
                                 max_acceleration=max_acceleration, max_deceleration=max_deceleration)
            object_model.append(truck)
        elif object_type == ObjectType.special_vehicle.value:
            name = 'VW_PassatVariant_2011_Police_green'
            if index == 0:
                name = 'VW_PassatVariant_2011_Police_blue'
            vehicle_type = xosc.VehicleCategory.car
            bounding_box = xosc.BoundingBox(width=1.798, length=4.749, height=1.468, x_center=1.2645, y_center=0,
                                            z_center=0.9)
            front_axle = xosc.Axle(maxsteer=27.5, wheeldia=1.1, track_width=1.473, xpos=1.2645, zpos=0.9)
            rear_axle = xosc.Axle(maxsteer=0, wheeldia=1.1, track_width=1.473, xpos=1.2645, zpos=0.9)
            max_speed = 212.4
            max_acceleration = 7
            max_deceleration = 9.5
            police_car = xosc.Vehicle(name=name, vehicle_type=vehicle_type, boundingbox=bounding_box,
                                      frontaxle=front_axle, rearaxle=rear_axle, max_speed=max_speed,
                                      max_acceleration=max_acceleration, max_deceleration=max_deceleration)
            object_model.append(police_car)
        elif object_type == ObjectType.motorcycle.value:
            name = 'Kawasaki_ZX-9R_white'
            if index == 0:
                name = 'Kawasaki_ZX-9R_green'
            vehicle_type = xosc.VehicleCategory.motorbike
            bounding_box = xosc.BoundingBox(width=0.85, length=2.076, height=1.928, x_center=0.618, y_center=0,
                                            z_center=0.9)
            front_axle = xosc.Axle(maxsteer=28.65, wheeldia=1.1, track_width=1.473, xpos=0.618, zpos=0.6)
            rear_axle = xosc.Axle(maxsteer=0, wheeldia=1.1, track_width=1.473, xpos=0.618, zpos=0.6)
            max_speed = 45
            max_acceleration = 7
            max_deceleration = 10
            moto = xosc.Vehicle(name=name, vehicle_type=vehicle_type, boundingbox=bounding_box,
                                frontaxle=front_axle, rearaxle=rear_axle, max_speed=max_speed,
                                max_acceleration=max_acceleration, max_deceleration=max_deceleration)
            object_model.append(moto)
        elif object_type == ObjectType.bicycle.value:
            # 暂时没有自行车模型 用摩托车代替
            name = 'Kawasaki_ZX-9R_white'
            if index == 0:
                name = 'Kawasaki_ZX-9R_green'
            vehicle_type = xosc.VehicleCategory.motorbike
            bounding_box = xosc.BoundingBox(width=0.85, length=2.076, height=1.928, x_center=0.618, y_center=0,
                                            z_center=0.9)
            front_axle = xosc.Axle(maxsteer=28.65, wheeldia=1.1, track_width=1.473, xpos=0.618, zpos=0.6)
            rear_axle = xosc.Axle(maxsteer=0, wheeldia=1.1, track_width=1.473, xpos=0.618, zpos=0.6)
            max_speed = 45
            max_acceleration = 7
            max_deceleration = 10
            bicycle = xosc.Vehicle(name=name, vehicle_type=vehicle_type, boundingbox=bounding_box,
                                   frontaxle=front_axle, rearaxle=rear_axle, max_speed=max_speed,
                                   max_acceleration=max_acceleration, max_deceleration=max_deceleration)
            object_model.append(bicycle)
        elif object_type == ObjectType.pedestrian.value:
            bounding_box = xosc.BoundingBox(width=0.7, length=0.6, height=1.8, x_center=0, y_center=0, z_center=0)
            male_ped = xosc.Pedestrian(name='Christian', model='male_adult', mass=70,
                                       category=xosc.PedestrianCategory.pedestrian, boundingbox=bounding_box)
            object_model.append(male_ped)

    return object_model


class Scenario(ScenarioGenerator):
    def __init__(self, gps, obs, gpsTime, period, single_scenario):
        ScenarioGenerator.__init__(self)
        self.gps = gps
        self.obs = obs
        self.gpsTime = gpsTime
        self.ObjectID = 0
        self.egoSpeed = 5
        self.Speed = 0
        self.period = period
        self.single_scenario = single_scenario
        time_list = single_scenario['scenario_time'][0].split(':')
        self.time = (True, 2019, 12, 19, int(time_list[0]), int(time_list[1]), int(time_list[2]))
        self.weather = single_scenario['scenario_weather'][0]
        self.entity_models = None

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
