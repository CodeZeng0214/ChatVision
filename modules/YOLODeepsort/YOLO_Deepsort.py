## 模块主程序脚本
## 实现了行人车辆的跟踪任务2024.11.25

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
# 将modules和脚本所在目录路径添加到sys.path
sys.path.append(current_dir)
import numpy as np
import objtracker
from objdetector import Detector
import cv2
import time


RESULT_PATH = './results\\Track_results\\result.mp4'
TRA_WEI_PATH = './weights/YOLOv8\yolov8x_UAV.pt' # 默认的图像跟踪类任务的权重路径

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Detections:
    def __init__(self):
        self.detections = []

    def add(self, xyxy, confidence, class_id, tracker_id):
        self.detections.append((xyxy, confidence, class_id, tracker_id))

def draw_trail(output_image_frame, trail_points, trail_color, trail_length=50):
    for i in range(len(trail_points)):
        if len(trail_points[i]) > 1:
            for j in range(1, len(trail_points[i])):
                cv2.line(output_image_frame, (int(trail_points[i][j-1][0]), int(trail_points[i][j-1][1])),
                         (int(trail_points[i][j][0]), int(trail_points[i][j][1])), trail_color[i], thickness=2)
        if len(trail_points[i]) > trail_length:
            trail_points[i].pop(0)  # Remove the oldest point from the trail

def PedCarTrack(params):
    """
    行人车辆的跟踪任务实现。\n
    参数：{'image_path': str, 'weight_path': str (可选), 'save_path': str (可选)}\n
    """
    image_path = params['image_path']
    weight_path = params.get('weight_path', TRA_WEI_PATH)
    save_path = params.get('save_path', RESULT_PATH)
    
    video_capture = cv2.VideoCapture(image_path)
    
    if not video_capture.isOpened():
        print("Error opening video file.")
        exit()

    # Get video properties (width and height)
    width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Close the video capture
    video_capture.release()

    detector = Detector(weight_path)
    video_capture = cv2.VideoCapture(image_path)
    videoWriter = None
    fps = int(video_capture.get(5))
    # print('fps:', fps)

    # Dictionary to store the trail points of each object
    object_trails = {}
    
    start_time = time.time()
    print("正在处理文件，已经弹出实时追踪的窗口")
    while True:
        _, im = video_capture.read()
        if im is None:
            break

        detections = Detections()
        output_image_frame, list_bboxs = objtracker.update(detector, im)

        for item_bbox in list_bboxs:
            x1, y1, x2, y2, _, track_id = item_bbox
            detections.add((x1, y1, x2, y2), None, None, track_id)

        # Add the current object's position to the trail
        for xyxy, _, _, track_id in detections.detections:
            x1, y1, x2, y2 = xyxy
            center = Point(x=(x1+x2)/2, y=(y1+y2)/2)
            if track_id in object_trails:
                object_trails[track_id].append((center.x, center.y))
            else:
                object_trails[track_id] = [(center.x, center.y)]

        # Draw the trail for each object
        trail_colors = [(255, 0, 255)] * len(object_trails)  # Red color for all trails
        draw_trail(output_image_frame, list(object_trails.values()), trail_colors, trail_length=27)

        # Remove trails of objects that are not detected in the current frame
        for tracker_id in list(object_trails.keys()):
            if tracker_id not in [item[3] for item in detections.detections]:
                object_trails.pop(tracker_id)
        
        if videoWriter is None:
            fourcc = cv2.VideoWriter_fourcc(
                'm', 'p', '4', 'v')  # opencv3.0
            videoWriter = cv2.VideoWriter(
                save_path, fourcc, fps, (output_image_frame.shape[1], output_image_frame.shape[0]))

        videoWriter.write(output_image_frame)
        cv2.imshow('Demo', output_image_frame)
        cv2.waitKey(1)

    video_capture.release()
    videoWriter.release()
    cv2.destroyAllWindows()
    spend_time = time.time() - start_time
    print("处理完成")
    print(f'处理耗时: {spend_time}s')
    
    return f"已经实时显示追踪结果于屏幕上，结果文件保存在{save_path}"



























