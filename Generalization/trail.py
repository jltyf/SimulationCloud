import ast
import math

from Generalization.get_trails import get_uniform_speed_trail, get_variable_speed_trail, get_turn_round_trail, \
    get_change_lane_trail, get_static_trail, get_start_stop_trail, get_ped_trail, get_curve_point
from Generalization.utils import get_ped_data
from enumerations import TrailType, TrailMotionType, SpeedType, RoadType


class Trail(object):

    def __init__(self, trail_type, car_trail, ped_trail, json_trail, speed_status, scenario, trail_section, start_speed,
                 heading_angle, rotate_tuple, start_point, ego_delta_col, object_index=0):
        self.scenario = scenario
        self.speed_status = speed_status
        if trail_type == TrailType.ped_trail:
            self.ped_trail, self.ped_trail_sketch_df = get_ped_data(ped_trail)
        self.json_trail = json_trail
        self.car_trail = car_trail
        self.trail_type = trail_type
        self.trail_section = trail_section
        self.start_point = start_point
        self.ego_delta_col = ego_delta_col
        self.lane_width = 3.5  # 车道线宽宽度
        if scenario['obs_start_x']:
            try:
                lateral_acc = int(ast.literal_eval(scenario['obs_lateral_acceleration'][object_index])[trail_section])
            except:
                lateral_acc = int(scenario['obs_lateral_acceleration'][object_index])
            try:
                longitudinal_acc = int(
                    ast.literal_eval(scenario['obs_longitudinal_acceleration'][object_index])[trail_section])
            except:
                longitudinal_acc = int(scenario['obs_longitudinal_acceleration'][object_index])
            self.acc_limit = (lateral_acc, longitudinal_acc)
        else:
            self.acc_limit = (-1, -1)
        # self.turning_angle = 0
        # 判断是自车轨迹还是目标物轨迹，忽略行人判断，归到目标物，待确认
        # self.start_speed = self.scenario['ego_start_speed'] if trail_type.value == TrailType.ego_trail.value else \
        #     self.scenario['obs_start_speed'][object_index]
        self.start_speed = start_speed
        self.heading_angle = heading_angle
        self.trail_motion_status = self.scenario['ego_trajectory'][trail_section] \
            if trail_type.value == TrailType.ego_trail.value \
            else self.scenario['obs_trajectory'][object_index][trail_section]
        self.trail_speed_status = self.scenario['ego_velocity_status'][trail_section] \
            if trail_type.value == TrailType.ego_trail.value \
            else self.scenario['obs_velocity_status'][object_index][trail_section]
        # 由于自车和目标车轨迹持续时间储存方式不同，需要区分
        self.duration_time = self.scenario['ego_velocity_time'][self.trail_section] \
            if trail_type.value == TrailType.ego_trail.value \
            else eval(self.scenario['obs_velocity_time'][object_index])[trail_section]
        self.rotate_tuple = rotate_tuple
        self.position = self.select_trail(int(self.trail_motion_status), int(self.speed_status))

    def select_trail(self, motion_status, speed_status):
        period = int(self.duration_time)

        # 静止
        if motion_status == TrailMotionType.static.value:
            return get_static_trail(period=period, start_point=self.start_point, heading_angle=self.heading_angle,
                                    lane_width=self.lane_width)
        # 判断是否是行人轨迹
        elif not self.trail_type == TrailType.ped_trail:
            # 直线
            if motion_status == TrailMotionType.direct.value:
                # 匀速
                if speed_status == SpeedType.uniform.value:
                    return get_uniform_speed_trail(car_trails=self.car_trail, trails_json_dict=self.json_trail,
                                                   start_speed=self.start_speed, period=period,
                                                   rotate_tuple=self.rotate_tuple, ego_delta_col=self.ego_delta_col)

                # 变速
                elif speed_status == SpeedType.Decelerate.value or speed_status == SpeedType.Accelerate.value:
                    required_speed = int(self.scenario['obs_start_velocity'][0])
                    return get_variable_speed_trail(car_trails=self.car_trail, trails_json_dict=self.json_trail,
                                                    start_speed=self.start_speed, period=period,
                                                    speed_status_num=speed_status, acc_limit=self.acc_limit,
                                                    rotate_tuple=self.rotate_tuple, ego_delta_col=self.ego_delta_col,
                                                    required_speed=required_speed)

                # 起步 or 刹停
                elif speed_status == SpeedType.Start.value or speed_status == SpeedType.Stop.value:
                    return get_start_stop_trail(car_trails=self.car_trail, trails_json_dict=self.json_trail,
                                                start_speed=self.start_speed, period=period,
                                                speed_status_num=speed_status,
                                                rotate_tuple=self.rotate_tuple, ego_delta_col=self.ego_delta_col)
            # 变道和连续变道
            elif TrailMotionType.lane_change_left.value <= motion_status <= TrailMotionType.lane_change_right_twice.value:
                return get_change_lane_trail(car_trails=self.car_trail, trails_json_dict=self.json_trail,
                                             lane_width=self.lane_width, start_speed=self.start_speed,
                                             period=period, motion_status=motion_status, rotate_tuple=self.rotate_tuple)
            # 左转 or 右转 or 左掉头 or 右掉头
            elif TrailMotionType.turn_left.value <= motion_status <= TrailMotionType.turn_around_right.value:
                if self.scenario['scenario_road_type'] == RoadType.city_curve_left.value or \
                        self.scenario['scenario_road_type'] == RoadType.city_curve_right.value:
                    r = abs(int(self.scenario['scenario_radius_curvature'][0]))
                    straight_trail = get_uniform_speed_trail(car_trails=self.car_trail,
                                                             trails_json_dict=self.json_trail,
                                                             start_speed=self.start_speed, period=period,
                                                             rotate_tuple=self.rotate_tuple,
                                                             ego_delta_col=self.ego_delta_col,
                                                             demand_distance=math.pi * 0.5 * r)
                    return get_curve_point(straight_trail, r, self.rotate_tuple, motion_status)
                else:
                    return get_turn_round_trail(car_trails=self.car_trail, trails_json_dict=self.json_trail,
                                                start_speed=self.start_speed, turn_round_flag=motion_status,
                                                period=period, rotate_tuple=self.rotate_tuple)
        else:
            return get_ped_trail(period=period, ped_trails=self.ped_trail, sketch=self.ped_trail_sketch_df)
