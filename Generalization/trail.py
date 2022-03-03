from Generalization.get_trails import get_uniform_speed_trail, get_variable_speed_trail, get_turn_round_trail, \
    get_change_lane_trail
from enumerations import TrailType, TrailMotionType, SpeedType


class Trail(object):

    def __init__(self, trail_type, car_trail, ped_trail, json_trail, speed_status, scenario, trail_section, start_speed,
                 heading_angle, object_index=0):
        self.scenario = scenario
        self.speed_status = speed_status
        self.json_trail = json_trail
        self.ped_trail = ped_trail
        self.car_trail = car_trail
        self.trail_type = trail_type
        self.trail_section = trail_section
        self.lane_width = 3  # 车道线宽宽度
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
        self.position, self.turning_angle = self.select_trail(self.trail_motion_status, self.speed_status)

    def select_trail(self, motion_status, speed_status):
        period = int(self.duration_time)
        # 直线
        if motion_status in str(TrailMotionType.direct.value):
            # 匀速
            if speed_status in str(SpeedType.uniform.value):
                return get_uniform_speed_trail(car_trails=self.car_trail, trails_json_dict=self.json_trail,
                                               start_speed=self.start_speed, period=period,
                                               heading_angle=self.heading_angle, trail_section=self.trail_section,
                                               turning_angle=self.turning_angle, scenario=self.scenario)

            # 变速
            elif speed_status in str(SpeedType.Decelerate.value) or speed_status in str(SpeedType.Accelerate.value):
                return get_variable_speed_trail(car_trails=self.car_trail, trails_json_dict=self.json_trail,
                                                start_speed=self.start_speed, period=period, speed_status_num=speed_status,
                                                heading_angle=self.heading_angle,
                                                turning_angle=self.turning_angle, scenario=self.scenario)

        # 左变道
        elif motion_status in str(TrailMotionType.lane_change_left.value):
            return get_change_lane_trail(car_trails=self.car_trail, trails_json_dict=self.json_trail,
                                         speed_status_num=speed_status, lane_width=self.lane_width, left_flag=True,
                                         change_lane_count=1, period=period,
                                         turning_angle=self.turning_angle)

        # 右偏
        elif motion_status in str(TrailMotionType.lane_change_right.value):
            return get_change_lane_trail(car_trails=self.car_trail, trails_json_dict=self.json_trail,
                                         speed_status_num=speed_status, lane_width=self.lane_width, left_flag=False,
                                         change_lane_count=1, period=period,
                                         turning_angle=self.turning_angle)
        # 左变道两次
        elif motion_status in str(TrailMotionType.lane_change_left_twice.value):
            return get_change_lane_trail(car_trails=self.car_trail, trails_json_dict=self.json_trail,
                                         speed_status_num=speed_status, lane_width=self.lane_width, left_flag=True,
                                         change_lane_count=2, period=period,
                                         turning_angle=self.turning_angle)
        # 右偏两次
        elif motion_status in str(TrailMotionType.lane_change_right_twice.value):
            return get_change_lane_trail(car_trails=self.car_trail, trails_json_dict=self.json_trail,
                                         speed_status_num=speed_status, lane_width=self.lane_width, left_flag=False,
                                         change_lane_count=2, period=period,
                                         turning_angle=self.turning_angle)
        # 左转
        elif motion_status in str(TrailMotionType.turn_left.value):
            return get_turn_round_trail(car_trails=self.car_trail, trails_json_dict=self.json_trail,
                                        speed_status_num=speed_status, turn_round_flag=motion_status,
                                        period=period, turning_angle=self.turning_angle)
        # 右转
        elif motion_status in str(TrailMotionType.turn_right.value):
            pass
        # 静止
        elif motion_status in str(TrailMotionType.static.value):
            pass
