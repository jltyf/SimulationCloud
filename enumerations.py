from enum import Enum, auto


class TrailMotionType(Enum):
    """
    轨迹形态
    直线            1
    左偏            2
    右偏            3
    连续左变道       4
    连续右变道       5
    左转            6
    右转            7
    左掉头          8
    右掉头          9
    静止            0
    """
    static = 0
    direct = auto()
    lane_change_left = auto()
    lane_change_right = auto()
    lane_change_left_twice = auto()
    lane_change_right_twice = auto()
    turn_left = auto()
    turn_right = auto()
    turn_around_left = auto()
    turn_around_right = auto()


class SpeedType(Enum):
    """
    速度状态
    匀速      1
    匀加      2
    匀减      3
    起步      4
    刹停      5
    静止      0
    """
    static = 0
    uniform = auto()
    Accelerate = auto()
    Decelerate = auto()
    Start = auto()
    Stop = auto()


class ObjectType(Enum):
    """
    物体的类型：
    自车       1
    目标车     2
    行人       3
    """
    ego = auto()
    vehicle = auto()
    pedestrian = auto()


class TrailType(Enum):
    """
    轨迹的类型：
    自车轨迹    1
    他车轨迹    2
    行人轨迹    3
    """
    ego_trail = auto()
    vehicle_trail = auto()
    ped_trail = auto()


class OrientationType(Enum):
    """
    目标物的朝向类型：
    自南向北    1
    自东向西    2
    自北向南    3
    自西向东    4
    """
    south_to_north = auto()
    west_to_east = auto()
    north_to_south = auto()
    east_to_west = auto()


class DataType(Enum):
    """
    目标物的朝向类型：
    固定值      1
    可以泛化    2
    需要计算    3
    """
    static = auto()
    generalizable = auto()
    calculative = auto()


class ScenarioType(Enum):
    """
    场景类型：
    自然驾驶    1
    交通法规    2
    事故场景    3
    泛化场景    4
    """
    natural = auto()
    office = auto()
    accident = auto()
    generalization = auto()


class CollisionStatus(Enum):
    """
    碰撞情况：
    碰撞     1
    未碰撞   0
    """
    no_collision = 0
    collision = auto()


class Weather(Enum):
    """
    天气情况：
    晴       1
    雨       2
    雪       3
    雾       4
    """
    sunny = auto()
    rainy = auto()
    snowy = auto()
    foggy = auto()


class VehicleModel(Enum):
    """
    车辆模型：
    Audi_A3_2009_black     1
    Audi_A3_2009_red       2
    """
    audi_black = auto()
    audi_red = auto()


class RoadType(Enum):
    """
    车辆模型：
    城市直道	        1
    城市左弯道	    2
    城市右弯道	    3
    城市十字路口	    4
    匝道	            5
    高速路	        6
    桥梁	            7
    隧道	            8
    """
    city_straight = auto()
    city_curve_left = auto()
    city_curve_right = auto()
    city_crossroads = auto()
    ramp = auto()
    freeway = auto()
    bridge = auto()
    tunnel = auto()
