#-*- coding:utf-8 -*-
import os
import math
import numpy as np
import pandas as pd
import random as rnd
import matplotlib.pyplot as plt
from os.path import isfile, join
from os import walk

#import pyodrx      # may switch to this lib later
#from lxml import etree as ET      # seems it has a bug in function SubElement()
import xml.etree.ElementTree as ET      # not support <!CDATA>, but might be ok for .xodr


####
# this is a script to generate xodr files, contains 2 API:
# 1. road_generator(...): generate xodr with real estimated road information from lane.csv
# 2. road_generator_ego(...): generate xodr with fake road along the trajactory of ego car
# this script can be excuted alone, see the main function at the bottom

# Args:
# <enu_file> path to gps_filtered.csv 
# <lane_file> path to lane.csv
# <out_file> path to output xodr file

# note: <!CDATA> will not be printed in the xodr file
####



def indent(elem, level=0): # pretty print xml from Stackoverflow.com, for python version < 3.9
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def add_lane(mother, lane_id, lane_type, lane_width=None, spd_limit=None):
    lane = ET.SubElement(mother, 'lane', attrib={'id':str(lane_id), 'type':lane_type, 'level':'false'})
    #ET.SubElement(lane, 'link')

    if lane_width:
        ET.SubElement(lane, 'width', attrib={'sOffset':"0.0", 'a':str(lane_width), 'b':"0.0", 'c':"0.0", 'd':"0.0"})

    roadMark = ET.SubElement(lane, 'roadMark', attrib={'sOffset':"0.0", 'type':"broken", 'weight':"standard", 'color':"white", 'material':"standard", 'width':"0.2", 'laneChange':"both", 'height':"0.05"})
    #ET.SubElement(roadMark, 'type')

    if spd_limit:
        ET.SubElement(lane, 'speed', attrib={'sOffset':"0.0", 'max':str(spd_limit), 'unit':'m/s'})


def write_header(xodr):
    header = ET.SubElement(xodr, 'header', attrib={'revMajor':"1", 'revMinor':"4", 'name':"Dummy", 'version':"1.00", 'date':"2017-03-10", 'north':"1.9000000000000000e+03", 'south':"-1.1500000000000000e+03", 'east':"3.3000000000000000e+03", 'west':"-4.8000000000000000e+02"})

    #geoReference = ET.SubElement(header, 'geoReference')
    #geoReference.text = ET.CDATA('[CDATA[+proj=tmerc +lon_0=12.0 +lat_0=48.0 +ellps=WGS84 +k_0=1.0 +x_0=0.0 +y_0=0.0]]') # only works with lxml, python's xml does not support <!CDATA[]> in xml 
    #geoReference.text = '[CDATA[+proj=tmerc +lon_0=12.0 +lat_0=48.0 +ellps=WGS84 +k_0=1.0 +x_0=0.0 +y_0=0.0]]'


def wirte_xodr_file(out_path, uv_coord_info, road_info, left_lane_info, right_lane_info): # generate xodr file with real road
    origin_x = uv_coord_info[0]
    origin_y = uv_coord_info[1]
    uv_coord_hdg = uv_coord_info[2]

    reference_line_offset = road_info[0]
    model_u = road_info[1] # in fomrat [c3, c2, c1, c0]
    model_v = road_info[2] # in fomrat [c3, c2, c1, c0]
    road_length = road_info[3]
    
    # model = road_info[1] # in fomrat [c3, c2, c1, c0]
    # road_length = road_info[2]

    xodr = ET.Element('OpenDRIVE')
    write_header(xodr)

    # add road
    road = ET.SubElement(xodr, 'road', attrib={'name':"", 'length':str(road_length), 'id':"1", 'junction':"-1"})
    #link = ET.SubElement(road, 'link')

    planView = ET.SubElement(road, 'planView')
    print('uv_origin:', uv_coord_info)
    print(model_u)
    print(model_v)
    geometry = ET.SubElement(planView, 'geometry', attrib={'s':str(0.0),'x':str(origin_x),'y':str(origin_y),'hdg':str(uv_coord_hdg),'length':str(road_length)})
    ET.SubElement(geometry, 'paramPoly3', attrib={'aU':str(model_u[3]), 'bU':str(model_u[2]), 'cU':str(model_u[1]), 'dU':str(model_u[0]), 'aV':str(model_v[3]), 'bV':str(model_v[2]), 'cV':str(model_v[1]), 'dV':str(model_v[0]), 'PRange':'arcLength'})
    # ET.SubElement(geometry, 'poly3', attrib={'a':str(model[3]), 'b':str(model[2]), 'c':str(model[1]), 'd':str(model[0])})

    elevationProfile = ET.SubElement(road, 'elevationProfile')
    ET.SubElement(elevationProfile, 'elevation', attrib={'s':str(0.0),'a':str(0.0),'b':str(0.0),'c':str(0.0),'d':str(0.0)})
    
    #ET.SubElement(road, 'lateralProfile')
    
    # lanes
    lanes = ET.SubElement(road, 'lanes')
    if reference_line_offset:
        ET.SubElement(lanes, 'laneOffset', attrib={'sOffset':"0.0", 'a':str(reference_line_offset), 'b':"0.0", 'c':"0.0", 'd':"0.0"})

    laneSection = ET.SubElement(lanes, 'laneSection')

    left = ET.SubElement(laneSection, 'left')
    lane_id = 0
    for lane in left_lane_info:
        lane_id += 1
        lane_width = lane[0]
        spd_limit = lane[1]
        add_lane(left, lane_id, 'none', lane_width=lane_width, spd_limit=spd_limit)

    center = ET.SubElement(laneSection, 'center')
    add_lane(center, 0, 'none', lane_width=None)

    right = ET.SubElement(laneSection, 'right')
    lane_id = 0
    for lane in right_lane_info:
        lane_id -= 1
        lane_width = lane[0]
        spd_limit = lane[1]
        add_lane(right, lane_id, 'driving', lane_width=lane_width, spd_limit=spd_limit)

    
    # write
    try:
        root = ET.indent(ET.ElementTree(xodr)) # python version >= 3.9 
    except:
        indent(xodr)
        root = ET.ElementTree(xodr) # using built in indent function

    #root.write(out_path, pretty_print=True) # lxml
    root.write(out_path)

    print('wirte xodr file:',out_path)
    return 


def wirte_xodr_file_ego(out_path, positions, road_length, spd_limit):  # generate xodr file with fake road
    xodr = ET.Element('OpenDRIVE')
    write_header(xodr)

    # add road
    road = ET.SubElement(xodr, 'road', attrib={'name':"", 'length':str(road_length), 'id':"1", 'junction':"-1"})
    #link = ET.SubElement(road, 'link')

    planView = ET.SubElement(road, 'planView')

    for row in positions:
        geometry = ET.SubElement(planView, 'geometry', attrib={'s':str(row[4]),'x':str(row[0]),'y':str(row[1]),'hdg':str(row[2]),'length':str(row[3])})
        ET.SubElement(geometry, 'line')

    elevationProfile = ET.SubElement(road, 'elevationProfile')
    ET.SubElement(elevationProfile, 'elevation', attrib={'s':str(0.0),'a':str(0.0),'b':str(0.0),'c':str(0.0),'d':str(0.0)})
    
    #ET.SubElement(road, 'lateralProfile')
    
    # lanes
    lanes = ET.SubElement(road, 'lanes')
    ET.SubElement(lanes, 'laneOffset', attrib={'sOffset':"0.0", 'a':"1.5", 'b':"0.0", 'c':"0.0", 'd':"0.0"})
    laneSection = ET.SubElement(lanes, 'laneSection')

    left = ET.SubElement(laneSection, 'left')
    add_lane(left, 1, 'none', lane_width=15)

    center = ET.SubElement(laneSection, 'center')
    add_lane(center, 0, 'none', lane_width=None)

    right = ET.SubElement(laneSection, 'right')
    add_lane(right, -1, 'driving', lane_width=3, spd_limit=spd_limit)
    add_lane(right, -2, 'none', lane_width=15)

    
    # write
    try:
        root = ET.indent(ET.ElementTree(xodr)) # python version >= 3.9 
    except:
        indent(xodr)
        root = ET.ElementTree(xodr) # using built in indent function

    #root.write(out_path, pretty_print=True) # lxml
    root.write(out_path)

    print('wirte xodr file:',out_path)


def calculate_road_length(enu_data):
    e_last = None
    n_last = None
    length = 0
    for row in enu_data:
        if e_last is None or n_last is None:
            e_last = row[1]
            n_last = row[2]
            continue
        e = row[1]
        n = row[2]  
        de = e - e_last
        dn = n - n_last
        length += np.sqrt(de*de + dn*dn)
        e_last = e
        n_last = n
    return length

def change_handing_coord(heading): # from north 0-2pi clockwise, to, east +/-pi clockwise
    heading -= (math.pi/2)
    if heading < math.pi:
        heading = - heading
    else:
        heading = 2*math.pi - heading
    return heading

def change_handing_coord2(heading): # from north 0.5-2.5pi unclockwise, to, east +/-pi unclockwise
    if heading < math.pi:
        heading = heading
    else:
        heading = heading - 2*math.pi
    return heading

def Heading_from_ve_vn_360(v_e, v_n): # 0-2pi, clockwise
    r = np.sqrt(v_e*v_e + v_n*v_n)
    if v_e > 0 and v_n >= 0:
        heading = np.arcsin(v_e / r)
    elif v_e > 0 and v_n < 0:
        heading = np.pi - np.arcsin(v_e / r)
    elif v_e < 0 and v_n < 0:
        heading = np.pi - np.arcsin(v_e / r)
    elif v_e < 0 and v_n >= 0:
        heading = np.pi*2 + np.arcsin(v_e / r)
    else:
        if v_n < 0:
            heading = np.pi
        else:
            heading = 0.
    return heading



def veh_to_enu_coord(lane_data):
    lane_enu = []
    for row in lane_data:
        time = row[0]
        left_lane_pos = row[1]
        right_lane_pos = row[2]
        headinga = math.radians(row[5] + 90)

        # note: in ME's data, right is positive

        # transform from vehicle coordinate to enu coordinate
        leftlane_e = row[3] + left_lane_pos * math.cos(headinga) 
        leftlane_n = row[4] - left_lane_pos * math.sin(headinga)

        # transform from vehicle coordinate to enu coordinate
        rightlane_e = row[3] + right_lane_pos * math.cos(headinga) 
        rightlane_n = row[4] - right_lane_pos * math.sin(headinga)
   
        lane_enu.append([time, leftlane_e, leftlane_n, rightlane_e, rightlane_n, row[3], row[4], row[5]])
    return lane_enu


def enu_to_uv_coord(lane_data, init_theta, init_headinga):
    lane_uv = []
    angle = init_theta + init_headinga
    for row in lane_data:
        time = row[0]
        leftlane_e = row[1]
        leftlane_n = row[2]
        rightlane_e = row[3]
        rightlane_n = row[4]

        # note: in ME's data, right is positive

        # transform from enu coordinate to uv coordinate
        leftlane_u = leftlane_e * math.sin(angle) + leftlane_n * math.cos(angle)
        leftlane_v = -leftlane_e * math.cos(angle) + leftlane_n * math.sin(angle)

        # transform from enu coordinate to uv coordinate
        rightlane_u = rightlane_e * math.sin(angle) + rightlane_n * math.cos(angle)
        rightlane_v = -rightlane_e * math.cos(angle) + rightlane_n * math.sin(angle)

        lane_uv.append([time, leftlane_u, leftlane_v, rightlane_u, rightlane_v, row[3], row[4], row[5]])
    return lane_uv


def RANSAC(points, sample_num=20, max_iterations=500, thresh=0.1): # RANSAC to find indices of inliers
    length = len(points)
    best_inlier_num = 0
    best_inlier_indices = []

    for _ in range(max_iterations):
        sample_index = rnd.sample(range(length), sample_num)
        sample_x = []
        sample_y = []
        for i in sample_index:
            sample_x.append(points[i][0])
            sample_y.append(points[i][1])
        model = np.polyfit(sample_x,sample_y,3)
        

        inlier_num = 0
        inlier_indices = []
        for i, p in enumerate(points):
            x = p[0]
            y = p[1]
            error = np.abs(y - (model[0] * x ** 3) - (model[1] * x ** 2) - (model[2] * x) - model[3]) # note: simple method, only distance in y direction is considered
            if error < thresh:
                inlier_num += 1 
                inlier_indices.append(i)

        if inlier_num > best_inlier_num:
            best_inlier_num = inlier_num
            best_inlier_indices = inlier_indices

        if best_inlier_num == length:
            break

    return best_inlier_indices


def get_lane_inliers(lane_uv):
    left_points = [[row[1], row[2]] for row in lane_uv]
    right_points = [[row[3], row[4]] for row in lane_uv]
    left_indices = RANSAC(left_points)
    right_indices = RANSAC(right_points)

    final_indices = [i for i in left_indices if i in right_indices]
    return final_indices

def road_detector_new(enu_file, lane_file, laneid_tuple, polyfit_fig_path=None, save_fig=True):
    # read data
    lane_content = pd.read_csv(lane_file)
    enu_content = pd.read_csv(enu_file)
    enu_content = enu_content[enu_content['ID'] == -1]
    enu_content = enu_content.sort_values(by="FrameID")
    
    left_lanemark = np.array(lane_content[lane_content['LaneID'] == laneid_tuple[1]][['Time','LanePosition','LaneQuality']])
    right_lanemark = np.array(lane_content[lane_content['LaneID'] == laneid_tuple[2]][['Time','LanePosition','LaneQuality']])
    leftleft_lanemark = np.array(lane_content[lane_content['LaneID'] == laneid_tuple[0]][['Time','LanePosition','LaneQuality']])
    rightright_lanemark = np.array(lane_content[lane_content['LaneID'] == laneid_tuple[3]][['Time','LanePosition','LaneQuality']])

    init_theta_left = sorted(np.array(lane_content[(lane_content['LaneID'] == 1)&(lane_content['LaneHeadingAngle']!='nan')&(lane_content['LaneQuality']>1)][['Time','LaneHeadingAngle']]).tolist(),key = lambda x:x[0])[0][1]
    # init_theta_leftleft = sorted(np.array(lane_content[(lane_content['LaneID'] == 0)&(lane_content['LaneHeadingAngle']!='nan')][['Time','LaneHeadingAngle']]).tolist(),key = lambda x:x[0])[0][1]
    # init_theta_right = sorted(np.array(lane_content[(lane_content['LaneID'] == 2)&(lane_content['LaneHeadingAngle']!='nan')][['Time','LaneHeadingAngle']]).tolist(),key = lambda x:x[0])[0][1]
    # init_theta_rightright = sorted(np.array(lane_content[(lane_content['LaneID'] == 3)&(lane_content['LaneHeadingAngle']!='nan')][['Time','LaneHeadingAngle']]).tolist(),key = lambda x:x[0])[0][1]

    ego_info = np.array(enu_content[['Time','East','North','HeadingAngle','AbsVel']])
    ego_info[:,1] -= ego_info[0,1] # offset to origin
    ego_info[:,2] -= ego_info[0,2]
    # print(ego_info)
    road_length = calculate_road_length(ego_info)

    
    # create groups: center, left, right lane, with additional ego trajctory data
    center_lane = []
    left_lane = []
    right_lane = []
    for i in range(len(left_lanemark)):
        target_time = left_lanemark[i][0]
        left_data = left_lanemark[i][1]
        leftleft_data = leftleft_lanemark[i][1]
        right_data = right_lanemark[i][1]
        rightright_data = rightright_lanemark[i][1]
        ego_data = ego_info[i][1:4]   # 0 east, 1 north, 2 heading 
        
        if left_lanemark[i][2] > 1 and right_lanemark[i][2] > 1:
            center_lane.append([target_time, left_data, right_data, ego_data[0], ego_data[1], ego_data[2]])
        if left_lanemark[i][2] > 1 and leftleft_lanemark[i][2] > 1:
            left_lane.append([target_time, leftleft_data, left_data, ego_data[0], ego_data[1], ego_data[2]])
        if rightright_lanemark[i][2] > 1 and right_lanemark[i][2] > 1:
            right_lane.append([target_time, right_data, rightright_data, ego_data[0], ego_data[1], ego_data[2]])
        
    assert(len(center_lane)>0)
    
    center_lane = sorted(center_lane, key=lambda row: row[0])
    left_lane = sorted(center_lane, key=lambda row: row[0])
    right_lane = sorted(center_lane, key=lambda row: row[0])
    
    init_headinga = math.radians(center_lane[0][5] + 90)
    
    # rotate to the uv coordinate, prepare for RANSAC or polygon fitting
    center_lane_enu = veh_to_enu_coord(center_lane)
    left_lane_enu = veh_to_enu_coord(left_lane)
    right_lane_enu = veh_to_enu_coord(right_lane)
    
    center_lane_uv = enu_to_uv_coord(center_lane_enu, init_theta_left, init_headinga)
    left_lane_uv = enu_to_uv_coord(left_lane_enu, init_theta_left, init_headinga)
    right_lane_uv = enu_to_uv_coord(right_lane_enu, init_theta_left, init_headinga)

    # RANSAC to find inliers' indices
    index_center_lane_inliers = get_lane_inliers(center_lane_uv)
    index_left_lane_inliers = get_lane_inliers(left_lane_uv)
    index_right_lane_inliers = get_lane_inliers(right_lane_uv)

    #index_center_lane_inliers = list(range(len(center_lane_uv))) # DEBUG
    #index_left_lane_inliers = list(range(len(left_lane_uv)))
    #index_right_lane_inliers = list(range(len(right_lane_uv)))

    center_lane = [x for i, x in enumerate(center_lane) if i in index_center_lane_inliers]
    left_lane = [x for i, x in enumerate(left_lane) if i in index_left_lane_inliers]
    right_lane = [x for i, x in enumerate(right_lane) if i in index_right_lane_inliers]

    center_lane_enu = [x for i, x in enumerate(center_lane_enu) if i in index_center_lane_inliers]
    left_lane_enu = [x for i, x in enumerate(left_lane_enu) if i in index_left_lane_inliers]
    right_lane_enu = [x for i, x in enumerate(right_lane_enu) if i in index_right_lane_inliers]

    # rotate the uv coordiante to find a position where parameter b == 0   (a + b*x + c*x**2 + d*x**3)
    b_limit = 0.000000001
    loop_limit = 1000 
    count = 0  
    angle = init_theta_left + init_headinga
    print('init angle', angle)
    print(len(center_lane_enu))
    # print(center_lane_enu)
    while 1:
        count+=1
        u = []
        v = []
        for row in center_lane_enu: 
            leftlane_e = row[1]
            leftlane_n = row[2]
            rightlane_e = row[3]
            rightlane_n = row[4]

            center_e = (leftlane_e + rightlane_e)/2 # the center line of current lane will be used as the reference line of the road in xodr
            center_n = (leftlane_n + rightlane_n)/2

            center_u = center_e * math.sin(angle) + center_n * math.cos(angle)
            center_v = -center_e * math.cos(angle) + center_n * math.sin(angle)

            u.append(center_u)
            v.append(center_v)

        center_lane_model = np.polyfit(u,v,3) #三次多项式（弃用）
        
        p = list(np.linspace(0, u[-1], len(u)))
        # p = [i*u[-1]/len(u) for i in range(len(u))]
        center_lane_model_u = np.polyfit(p,u,3) #参数三次曲线
        center_lane_model_v = np.polyfit(p,v,3) #参数三次曲线

        # if abs(center_lane_model[2]) < b_limit or count >= loop_limit:
        #     break
        # print(center_lane_model_v[2])
        if (abs(center_lane_model_v[2]) < b_limit and abs(center_lane_model_u[2]) > b_limit) or count >= loop_limit:
            break
    print(math.atan(center_lane_model_v[2] / center_lane_model_u[2]))    
    # angle -= math.atan(center_lane_model_v[2] / center_lane_model_u[2])
    print('new angle', angle)
    print('count', count)
    # calculate lane width in new ST coordinate, form 2 part: c0 of fitted left lane mark, mean c0 of first 5 ME's data
    u_l = []
    v_l = []
    u_r = []
    v_r = []
    for row in center_lane_enu: # fit left lane to calculate left lane offset
        # left lanemark
        leftlane_e = row[1]
        leftlane_n = row[2]
        center_u = leftlane_e * math.sin(angle) + leftlane_n * math.cos(angle)
        center_v = -leftlane_e * math.cos(angle) + leftlane_n * math.sin(angle)
        u_l.append(center_u)
        v_l.append(center_v)

        # right lanemark
        rightlane_e = row[3]
        rightlane_n = row[4]
        center_u = rightlane_e * math.sin(angle) + rightlane_n * math.cos(angle)
        center_v = -rightlane_e * math.cos(angle) + rightlane_n * math.sin(angle)
        u_r.append(center_u)
        v_r.append(center_v)

    left_offset_1 =  np.polyfit(u_l,v_l,3)[3] # fit left lanemark

    temp = []
    for i in range(5): # mean value of first n mobile eye left lane offset
        temp.append(-center_lane[i][1])
    left_offset_2 = np.mean(temp)

    # calculate final parameters
    left_offset = (left_offset_1 + left_offset_2)/2
    # left_offset = left_offset_1
    # left_offset = left_offset_2
    print('road detector: left offset', left_offset, left_offset_1, left_offset_2)
    uv_coord_hdg = change_handing_coord2(angle)

    w = []
    for row in center_lane:
        w.append(row[2]-row[1])
    width_center = abs(np.mean(w))


    # simple check if left and right lane exist
    has_left_lane = False
    temp = []
    for row in left_lane:
        temp.append(row[2]-row[1])  # right-left # should be positive
    width_left = abs(np.mean(temp))
    if width_left > 2:
       has_left_lane = True 
       print('road detector: has left lane! width:', width_left)

    has_right_lane = False
    temp = []
    for row in right_lane:
        temp.append(row[2]-row[1])  # right-left
    width_right = abs(np.mean(temp))
    if width_right > 2:
       has_right_lane = True 
       print('road detector: has right lane! width:', width_right)

    # calculate speed limit
    max_spd = 0
    for row in center_lane:
        if row[5] > max_spd:
            max_spd = row[5]

    if max_spd<=50:
        spd_limit = 50
    elif max_spd<=80:
        spd_limit = 80
    else:
        spd_limit = 120
    spd_limit /= 3.6

    # plot for debug
    if save_fig and polyfit_fig_path is not None:
        # calculate ego waypoint in new coordinate
        e = []
        n = []
        for row in ego_info: 
            n_ = row[2] * math.cos(angle) + row[1] *math.sin(angle)
            e_ = -row[1] * math.cos(angle) + row[2] * math.sin(angle)
            e.append(e_)
            n.append(n_)

        # calculate leftleft lanemark and rightright lanemark in new coordinate
        u_ll = []
        v_ll = []
        if has_left_lane:
            for row in left_lane_enu: # fit left lane to calculate left lane offset
                leftlane_e = row[1]
                leftlane_n = row[2]
                center_u = leftlane_e * math.sin(angle) + leftlane_n * math.cos(angle)
                center_v = -leftlane_e * math.cos(angle) + leftlane_n * math.sin(angle)
                u_ll.append(center_u)
                v_ll.append(center_v)
        u_rr = []
        v_rr = []
        if has_right_lane:
            for row in right_lane_enu: # fit left lane to calculate left lane offset
                rightlane_e = row[3]
                rightlane_n = row[4]
                center_u = rightlane_e * math.sin(angle) + rightlane_n * math.cos(angle)
                center_v = -rightlane_e * math.cos(angle) + rightlane_n * math.sin(angle)
                u_rr.append(center_u)
                v_rr.append(center_v)

        # plot
        fig = plt.figure()
        ax1 = fig.add_subplot(1,1,1)

        ax1.set_title('en')
        ax1.set_xlabel('s')
        ax1.set_ylabel('t')
        ax1.scatter(n,e,s=5,c = 'b',marker = 'x')  # ego trail
        ax1.scatter(u,v,s=5,c = 'y',marker = 'x')  # lane center line
        ax1.scatter(u_r,v_r,s=5,c = 'r',marker = 'o')  # right lane
        ax1.scatter(u_l,v_l,s=5,c = 'r',marker = 'o')  # left lane
        ax1.scatter(u_rr,v_rr,s=5,c = 'r',marker = '.') # right right lane
        ax1.scatter(u_ll,v_ll,s=5,c = 'r',marker = '.') # left left lane

        x = np.linspace(0, u[-1], len(u))
        y = center_lane_model[0] * x ** 3 + center_lane_model[1] * x ** 2 + center_lane_model[2] * x + center_lane_model[3]
        plt.plot(x,y,color = 'green',linewidth = 1.5)  # lane center line model
        
        p = np.linspace(0, u[-1], len(u))
        # print(n)
        # print(e)
        xu = center_lane_model_u[0] * p ** 3 + center_lane_model_u[1] * p ** 2 + center_lane_model_u[2] * p + center_lane_model_u[3]
        yv = center_lane_model_v[0] * p ** 3 + center_lane_model_v[1] * p ** 2 + center_lane_model_v[2] * p + center_lane_model_v[3]
        # ax1.scatter(xu,yv,s=15,c = 'black',marker = '.')
        plt.plot(xu,yv,color = 'black',linewidth = 1)
        # print(center_lane_model)
        print('u:',center_lane_model_u)
        print('v:',center_lane_model_v)
        plt.savefig(polyfit_fig_path)
        #plt.show()  # DEBUG

    
    # prepair output
    en_coord_info = (ego_info[0][1], ego_info[0][2], math.pi/2 - uv_coord_hdg) # 自车初始点
    # en_coord_info = (center_lane_enu[0][5], center_lane_enu[0][6], math.pi/2 - uv_coord_hdg) # 拟合车道中心线初始点
    road_info = (left_offset, center_lane_model_u, center_lane_model_v, road_length)
    right_lane_info = []
    right_lane_info.append((width_center, spd_limit))
    if has_right_lane:
        right_lane_info.append((width_right, spd_limit))
    left_lane_info = []
    if has_left_lane:
        left_lane_info.append((width_left, spd_limit))
  
    return en_coord_info, road_info, left_lane_info, right_lane_info



def road_generator(enu_file, lane_file, out_file, save_fig=True): # use road_detector to generate road
    temp = out_file.split('/')[0:-1]
    out_dir = ''
    for s in temp:
        if s == '':
            continue
        out_dir += ('/'+s)
    polyfit_fig_path = os.path.join(out_dir, 'polyfit.jpg')

    # run road detector
    uv_coord_info, road_info, left_lane_info, right_lane_info = road_detector_new(enu_file, lane_file, polyfit_fig_path, save_fig=True)

    # write xodr file
    wirte_xodr_file(out_file, uv_coord_info, road_info, left_lane_info, right_lane_info)


def road_generator_ego(enu_file, lane_file, out_file, save_fig=True): # use ego postion as fake road

    # read data
    enu_content = pd.read_csv(enu_file)
    enu_content = np.array(enu_content[['Time','East','North','HeadingAngle','Velocity']])
    enu_content[:,1] -= enu_content[0,1]
    enu_content[:,2] -= enu_content[0,2]
    enu_content = enu_content.tolist()
    assert(len(enu_content)>2),'enu file does not has enough data!'

    # append data into list, calculate road length and max. ego speed
    positions = []
    max_spd = 0
    road_length = 0
    for i in range(len(enu_content)-1):
        frame1 = enu_content[i]
        frame2 = enu_content[i+1]
        e1 = frame1[1]
        n1 = frame1[2]
        e2 = frame2[1]
        n2 = frame2[2]
        de = e2 - e1
        dn = n2 - n1
        length = np.sqrt(de*de + dn*dn)
        hdg = change_handing_coord2(Heading_from_ve_vn_360(de, dn))
        positions.append((e1,n1,hdg,length,road_length))
        road_length += length
        if frame2[4]>max_spd:
            max_spd = frame2[4]

    if max_spd<=50:
        spd_limit = 50
    elif max_spd<=80:
        spd_limit = 80
    else:
        spd_limit = 120
    spd_limit /= 3.6

    # write xodr file
    wirte_xodr_file_ego(out_file, positions, road_length, spd_limit)


regenerate = True
if __name__ == '__main__':
    root_dir = '/home/lxj/wendang_lxj/Temp/DongPeng_Legacy/new_scenarios/follow/cicv_2020-07-21-08-04-11_1'
    for root, dirs, files in walk(root_dir):
        if 'fusion' not in dirs:
            continue

        name = root.split('/')[-1]
        enu_file = join(root,'fusion','gps_filtered.csv')
        lane_file = join(root, 'lane.csv')

        out_file_ego = join(root,'fusion',name+'_ego.xodr')
        if not regenerate and isfile(out_file_ego):
            pass
        elif isfile(enu_file):
            road_generator_ego(enu_file, lane_file, out_file_ego)

        out_file = join(root,'fusion',name+'.xodr')
        road_generator(enu_file, lane_file, out_file)
        # if not regenerate and isfile(out_file):
        #     pass
        # elif isfile(enu_file) and isfile(lane_file):
        #     road_generator(enu_file, lane_file, out_file)






