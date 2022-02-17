import math
import operator
import copy
import pandas as pd

from TrajectoryAugmentation import concat_trails
from enumerations import SpeedType, TrailMotionType
from utils import spin_trans_form, Point, resample_by_time, get_merge_trails, get_lane_distance, get_finale_trail, \
    change_speed, multiple_uniform_trail


def get_uniform_speed_trail(car_trails, trails_json_dict, start_speed, period, turning_angle, heading_angle, scenario):
    """
    return:直线轨迹
    从匀速的轨迹库中 分类别取出轨迹
    """
    uniform_json_dict = dict()
    trails = copy.deepcopy(car_trails)
    for motion in trails_json_dict.keys():
        for trail_speed, trail_value in trails_json_dict[motion].items():
            if trail_value and trail_speed in 'Uniform speed':
                selected_trail_list = []
                for single_trail in trail_value:
                    # 排除数据中初始速度和结束速度小于0的和结束heading angle减去开始heading angle大于0.5度的轨迹
                    if single_trail['startSpeed'] > 0 and single_trail['stopSpeed'] > 0 \
                            and math.fabs(single_trail['stopHeadinga'] - single_trail['startHeadinga'] < 0.5):
                        selected_trail_list.append(single_trail)
                        uniform_json_dict = {motion: selected_trail_list}

    for trail_motion in uniform_json_dict:
        uniform_json_dict[trail_motion] = sorted(uniform_json_dict[trail_motion],
                                                 key=operator.itemgetter('startSpeed'), reverse=True)
        previous_speed_difference = 100
        for single_json in uniform_json_dict[trail_motion]:
            speed_difference = abs(single_json['startSpeed'] - start_speed)
            if speed_difference < previous_speed_difference:
                final_trail = single_json
                previous_speed_difference = speed_difference

    start_time = final_trail['start']
    end_time = final_trail['stop']
    single_trail = (trails[(trails['Time'].values <= end_time)
                           & (trails['Time'].values >= start_time)]).reset_index(drop=True)
    if len(single_trail) > 10:
        temp_trail = single_trail.copy()
        for _ in range(8):
            # new_trail = get_merge_trails(trails_count=2, trail=single_trail, trail_next=temp_trail)[1:]
            new_trail = get_merge_trails(trails_count=1, trail=single_trail)[1:]
            single_trail = pd.concat([single_trail, new_trail], axis=0).reset_index(drop=True)
        single_trail = single_trail[:period * 100]
        trail_res = spin_trans_form(position_e='ego_e', position_n='ego_n', trail_new=single_trail.copy(),
                                    deg=-single_trail.at[0, 'headinga'] + turning_angle, trails_count=1,
                                    trail=single_trail)
        start_point = Point(trail_res.at[0, 'ego_e'], trail_res.at[0, 'ego_n'])
        trail_res['ego_e'] -= start_point.x
        trail_res['ego_n'] -= start_point.y
        trail_res = trail_res.reset_index(drop=True)
        time_min = trail_res.Time.values.min()
        for i in range(len(trail_res)):
            trail_res.loc[i, 'Time'] = time_min + 10 * i
    if previous_speed_difference < 0.5:
        return trail_res, turning_angle
    else:
        multiple = start_speed / trail_res.loc[0, 'vel_filtered']
        trail_res = multiple_uniform_trail(trail_res, 1, start_speed)
        return trail_res, turning_angle


def get_variable_speed_trail(car_trails, trails_json_dict, period, speed_status_num, turning_angle, heading_angle,
                             scenario):
    """
    Parameters
    ----------
    car_trails: 原始的轨迹数据
    trails_json_dict:标记所有轨迹类型的json数据
    period: 持续时间
    speed_status_num: 当前需要处理的轨迹属于哪种加速状态
    turning_angle: 跟在有转向的运动后需要转向的角度
    heading_angle: 此轨迹的朝向角，取值范围[0,360]，以真北为基准，顺时针递减
    scenario: 场景参数
    Return 返回多条变速轨迹，如果所能生成的轨迹数量大于max_trails，返回轨迹条数是max_trails
    -------
    """
    if speed_status_num == str(SpeedType.Accelerate.value):
        speed_status = 'Accelerate'
    else:
        speed_status = 'Decelerate'
    variable_json_dict = dict()
    total_json_index_list = list()
    for trail_motion in trails_json_dict.keys():
        if trail_motion == 'No change lane':
            for trail_speed, trail_value in trails_json_dict[trail_motion].items():
                if trail_speed in speed_status:
                    selected_trail_list = []
                    for single_trail in trail_value:
                        if math.fabs(single_trail['stopHeadinga'] - single_trail['startHeadinga'] < 0.5):
                            selected_trail_list.append(single_trail)
                        variable_json_dict = {trail_motion: {trail_speed: selected_trail_list}}

    for trail_motion in variable_json_dict:
        position_list = list()
        motion_json_index_list = list()
        index_list = list()
        for trail_value in variable_json_dict[trail_motion].values():
            reverse_flag = ('startSpeed', False) if speed_status == str(SpeedType.Decelerate.value) else (
                'stopSpeed', True)
            variable_json_dict[trail_motion] = sorted(trail_value, key=operator.itemgetter(reverse_flag[0]),
                                                      reverse=reverse_flag[1])
            temp_list = variable_json_dict[trail_motion]
            for index in range(len(temp_list)):
                json_index_list_temp = [index]
                for index_temp in range(index + 1, len(trail_value)):
                    if (speed_status_num == str(SpeedType.Accelerate.value) and temp_list[index]['stopSpeed'] <
                        temp_list[index_temp]['startSpeed']) or (
                            speed_status_num == str(SpeedType.Decelerate.value) and temp_list[index]['stopSpeed'] >
                            temp_list[index_temp]['startSpeed']):
                        json_index_list_temp.append(index_temp)
                    # else:
                    #     break
                motion_json_index_list.append(json_index_list_temp)
            for index in range(len(temp_list)):
                index_list = list()
                for json_index in range(len(motion_json_index_list)):
                    if index == motion_json_index_list[json_index][0]:
                        position = motion_json_index_list[json_index]
                        index_list.append(index)  # 起始轨迹
                        for i in range(json_index + 1, len(motion_json_index_list)):
                            if not len(list(set(position) & set(motion_json_index_list[i]))) == 0:
                                index_list.append(motion_json_index_list[i][index % len(motion_json_index_list[i])])
                                position = motion_json_index_list[i]
        for index in index_list:
            trails_total = copy.deepcopy(car_trails)
            trails_list = list()
            json_label_index_list = [json_index for json_index in index]
            for json_label in json_label_index_list:
                start_time = float(variable_json_dict[trail_motion][json_label]['start'])
                end_time = float(variable_json_dict[trail_motion][json_label]['stop'])
                trails = (trails_total[(trails_total['Time'].values <= end_time) &
                                       (trails_total['Time'].values >= start_time)]).reset_index(drop=True)
                if len(trails) >= 5:
                    trails_list.append(trails)

            if trails_list:
                original_trail = trails_list[0]
                merge_trail = trails_list[0]
                # merge_trail = trails_list[0].iloc[:, :14]
                for single_trail in trails_list[1:]:
                    temp_trail = concat_trails(original_trail, single_trail)[1:].reset_index(drop=True)
                    original_trail = temp_trail
                    merge_trail = pd.concat([merge_trail, temp_trail], axis=0).reset_index(drop=True)
                    merge_trail = spin_trans_form(position_e='ego_e', position_n='ego_n', trail_new=merge_trail.copy(),
                                                  deg=-merge_trail.at[0, 'headinga'] + turning_angle, trails_count=1,
                                                  trail=merge_trail)
                    frame = math.ceil(period * 10 / len(merge_trail))
                    static_time = pd.date_range('2021-01-01 00:00:00', periods=len(merge_trail), freq='T')
                    if frame > 1:
                        sample = math.floor(60 / frame)
                        merge_trail = resample_by_time(data=merge_trail, minutes=sample, datetime=static_time,
                                                       flag=False)[
                                      :period * 10]
                        start_point = Point(merge_trail.at[0, 'ego_e'], merge_trail.at[0, 'ego_n'])
                        merge_trail['ego_e'] = merge_trail['ego_e'] - start_point.x
                        merge_trail['ego_n'] = merge_trail['ego_n'] - start_point.y
                    else:
                        sample = math.floor(len(merge_trail) / (period * 10))
                        merge_trail = resample_by_time(data=merge_trail, minutes=sample, datetime=static_time,
                                                       flag=True)[
                                      :period * 10 - 1]
                        start_point = Point(merge_trail.at[0, 'ego_e'], merge_trail.at[0, 'ego_n'])
                        merge_trail.loc[:, ['ego_e']] = 0
                        merge_trail['ego_n'] = merge_trail['ego_n'] - start_point.y
                        position_list.append(merge_trail.reset_index(drop=True))
        return position_list, turning_angle


def get_change_lane_trail(car_trails, trails_json_dict, speed_status_num, lane_width, left_flag,
                          change_lane_count, period, turning_angle):
    """
    Parameters
    ----------
    car_trails: 原始的轨迹数据
    trails_json_dict:标记所有轨迹类型的json数据
    speed_status_num:速度状态编号
    lane_width: 车道宽度
    left_flag: 左变道为True 右变道为False
    change_lane_count:变化车道次数
    period:持续时间
    turning_angle: 跟在有转向的运动后需要转向的角度
    Returns 轨迹
    -------
    """
    if speed_status_num == str(SpeedType.Accelerate.value):
        speed_status = 'Accelerate'
    elif speed_status_num == str(SpeedType.Decelerate.value):
        speed_status = 'Decelerate'
    else:
        speed_status = 'Uniform speed'
    change_lane_json_dict = dict()
    position_list = list()
    trails = copy.deepcopy(car_trails)
    for motion in trails_json_dict:
        if (left_flag and 'Left change lane' in motion) or (not left_flag and 'Right change lane' in motion):
            change_lane_json_dict[motion] = trails_json_dict[motion]
    for motion in change_lane_json_dict:
        for json_speed_status, trails_list in change_lane_json_dict[motion].items():
            if trails_list and speed_status == json_speed_status:
                # for speed_status in f
                trails_list = sorted(trails_list, key=operator.itemgetter('startSpeed'), reverse=True)
                for single_json_trail in trails_list:
                    trail_select = trails[(trails['Time'] <= single_json_trail['stop']) & (
                            trails['Time'] >= single_json_trail['start'])].reset_index(drop=True)
                    trail_select = get_merge_trails(trails_count=1, trail=trail_select)
                    required_change_distance = change_lane_count * (lane_width / 2)
                    com_lane = get_lane_distance(trail_select, trail_select.iloc[-1], required_change_distance)
                    if com_lane > 0:
                        for trail_frame_index in range(1, len(trail_select)):
                            if get_lane_distance(trail_select, trail_select.iloc[trail_frame_index],
                                                 required_change_distance) > \
                                    get_lane_distance(trail_select, trail_select.iloc[trail_frame_index - 1],
                                                      required_change_distance):
                                merge_trail = trail_select[:trail_frame_index]
                            else:
                                try:
                                    merge_trail = trail_select[:trail_frame_index + 1]
                                except:
                                    merge_trail = trail_select[:trail_frame_index]
                            if not merge_trail.empty:
                                merge_trail = get_finale_trail(merge_trail, period, turning_angle)
                                position_list.append(merge_trail)
                                break
                    else:
                        origin_trail = trail_select
                        merge_trail = trail_select
                        for change_time in range(1, int(math.fabs(required_change_distance // com_lane))):
                            temp_trail = get_merge_trails(trails_count=2, trail=origin_trail, trail_next=trail_select)[
                                         1:].reset_index(drop=True)
                            origin_trail = temp_trail
                            merge_trail = (pd.concat([merge_trail, temp_trail], axis=0)).reset_index(drop=True)
                            trail_select = merge_trail
                            for trail_frame_index in trail_select:
                                merge_trail = trail_select[:trail_frame_index]
                                if not merge_trail.empty:
                                    merge_trail = get_finale_trail(merge_trail, period, turning_angle)
                                    position_list.append(merge_trail)
                                    break
        # if len(position_list) <= max_trails / 10:
        #     return position_list, turning_angle
        # spacing = int(len(position_list) / (max_trails / 10))
        # if spacing == 1:
        #     return position_list[:int(max_trails / 10)], turning_angle
        # else:
        #     return position_list[0:len(position_list):spacing], turning_angle
        return position_list[0:len(position_list)], turning_angle


# 目前之前的业务逻辑有明显漏洞，如有需求再完成
def get_turn_round_trail(car_trails, trails_json_dict, speed_status_num, turn_round_flag, max_trails, period,
                         turning_angle):
    """

    Parameters
    ----------
    car_trails: 原始的轨迹数据
    trails_json_dict:标记所有轨迹类型的json数据
    turn_round_flag: 参考枚举类TrailMotionType
    max_trails: 每种类型最多生成的轨迹数量
    period: 持续时间
    turning_angle: 跟在有转向的运动后需要转向的角度
    Returns：返回List，每个元素是一条轨迹
    -------

    """
    turn_round_json_dict = dict()
    trails_list = list()
    position_list = list()
    temp_list = list()
    trails = copy.deepcopy(car_trails)
    if turn_round_flag == str(TrailMotionType.turn_left.value):
        turn_round_status = 'crossing turn_left normal'
    elif turn_round_flag == str(TrailMotionType.turn_right.value):
        turn_round_status = 'crossing turn_right normal'
    elif turn_round_flag == str(TrailMotionType.turn_around_left.value):
        turn_round_status = 'uturn_left'
    elif turn_round_flag == str(TrailMotionType.turn_around_right.value):
        turn_round_status = 'uturn_right'
    else:
        raise TypeError('运动轨迹参数错误')

    for motion in trails_json_dict:
        if turn_round_status in motion:
            turn_round_json_dict[motion] = trails_json_dict[motion]
            turn_round_json_dict[motion] = sorted(turn_round_json_dict[motion],
                                                  key=operator.itemgetter('startSpeed'), reverse=True)
    for single_json in turn_round_json_dict:
        start_time = single_json['start']
        end_time = single_json['stop']
        trail_new = (trails[(trails['Time'].values <= end_time)
                            & (trails['Time'].values >= start_time)]).reset_index(drop=True)
        trail_new = get_merge_trails(trails_count=1, trail=trail_new)
        # 转向数据中不同帧如果有相同的坐标点表示自车静止，轨迹不能使用
        if len(trail_new) >= 5 and (True not in (trail_new.duplicated(subset=['ego_e', 'ego_n']).values.tolist())):
            previous_x = trail_new.iloc[-1]['ego_e']
            previous_y = trail_new.iloc[-1]['ego_n']
            previous_headinga = trail_new.iloc[-1]['headinga']
            temp_list.append(trail_new)
            for next_json in turn_round_json_dict:
                if next_json == single_json:
                    continue
                trail_next = (trails[(trails['Time'].values <= end_time)
                                     & (trails['Time'].values >= start_time)]).reset_index(drop=True)
                trail_next = get_merge_trails(trails_count=1, trail=trail_next)
                x_ = trail_next.iloc[-1]['ego_e'] + previous_x
                y_ = trail_next.iloc[-1]['ego_n'] + previous_y
                rad = math.radians(previous_headinga)
                x = (x_ - previous_x) * math.cos(rad) + (y_ - previous_y) * math.sin(rad) + previous_x
                y = -(x_ - previous_x) * math.sin(rad) + (y_ - previous_y) * math.sin(rad) + previous_y
                # 舍弃掉拼接过后移动距离过掉的轨迹
                if math.fabs(previous_x - x) / len(trail_next) >= 0.01:
                    trails_list.append(trail_new)
                    if len(trails_list) >= max_trails:
                        break

                    pass
    for single_trail in trails_list:
        pass
