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
    """
    uniform = auto()
    Accelerate = auto()
    Decelerate = auto()


class ObjectType(Enum):
    """
    物体的类型：
    自车       1
    目标车     2
    行人      3
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
