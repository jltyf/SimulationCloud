from Generalization.get_trails import get_uniform_speed_trail, get_variable_speed_trail, get_turn_round_trail, \
    get_change_lane_trail, get_static_trail
from enumerations import TrailType, TrailMotionType, SpeedType


class Trail(object):

    def __init__(self, trail_type, car_trail, ped_trail, json_trail, speed_status, scenario, trail_section, start_speed,
                 heading_angle, rotate_tuple, start_point, object_index=0):
        self.scenario = scenario
        self.speed_status = speed_status
        self.json_trail = json_trail
        self.ped_trail = ped_trail
        self.car_trail = car_trail
        self.trail_type = trail_type
        self.trail_section = trail_section
        self.start_point = start_point
        self.lane_width = 3.5  # 车道线宽宽度
        self.turning_angle = 0
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
            else self.scenario['obs_velocity_time'][object_index + trail_section]
        self.rotate_tuple = rotate_tuple
        self.position, self.turning_angle = self.select_trail(int(self.trail_motion_status), int(self.speed_status))

    def select_trail(self, motion_status, speed_status):
        period = int(self.duration_time)
        # 直线
        if motion_status == TrailMotionType.direct.value:
            # 匀速
            if speed_status == SpeedType.uniform.value:
                return get_uniform_speed_trail(car_trails=self.car_trail, trails_json_dict=self.json_trail,
                                               start_speed=self.start_speed, period=period,
                                               heading_angle=self.heading_angle, trail_section=self.trail_section,
                                               turning_angle=self.turning_angle, scenario=self.scenario,
                                               rotate_tuple=self.rotate_tuple)

            # 变速
            elif speed_status == SpeedType.Decelerate.value or speed_status == SpeedType.Accelerate.value:
                return get_variable_speed_trail(car_trails=self.car_trail, trails_json_dict=self.json_trail,
                                                start_speed=self.start_speed, period=period,
                                                speed_status_num=speed_status,
                                                heading_angle=self.heading_angle,
                                                turning_angle=self.turning_angle, scenario=self.scenario,
                                                rotate_tuple=self.rotate_tuple)

        # 变道和连续变道
        elif TrailMotionType.lane_change_left.value <= motion_status <= TrailMotionType.lane_change_right_twice.value:
            return get_change_lane_trail(car_trails=self.car_trail, trails_json_dict=self.json_trail,
                                         lane_width=self.lane_width, start_speed=self.start_speed,
                                         heading_angle=self.heading_angle, period=period, motion_status=motion_status,
                                         rotate_tuple=self.rotate_tuple)
        # 左转 or 右转 or 左掉头 or 右掉头
        elif TrailMotionType.turn_left.value <= motion_status <= TrailMotionType.turn_around_right.value:
            return get_turn_round_trail(car_trails=self.car_trail, trails_json_dict=self.json_trail,
                                        start_speed=self.start_speed, speed_status_num=speed_status,
                                        turn_round_flag=motion_status,
                                        period=period, turning_angle=self.turning_angle, rotate_tuple=self.rotate_tuple)

        # 静止
        elif motion_status == TrailMotionType.static.value:
            return get_static_trail(period=period, start_point=self.start_point, heading_angle=self.heading_angle,
                                    lane_width=self.lane_width)
