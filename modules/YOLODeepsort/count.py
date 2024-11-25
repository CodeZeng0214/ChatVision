import numpy as np
import objtracker
from objdetector import Detector
import cv2

VIDEO_PATH = './video/test_person.mp4'

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
                         (int(trail_points[i][j][0]), int(trail_points[i][j][1])), trail_color[i], thickness=3)
        if len(trail_points[i]) > trail_length:
            trail_points[i].pop(0)  # Remove the oldest point from the trail

def is_in_line(pt1, pt2, pt):
    x1, y1 = pt1.x, pt1.y
    x2, y2 = pt2.x, pt2.y
    x, y = pt.x, pt.y
    return np.sign((x2 - x1) * (y - y1) - (y2 - y1) * (x - x1))

def trigger(detections: Detections, pt1, pt2, prev_tracker_state, tracker_state, crossing_ids, in_count, out_count):
    for xyxy, _, _, tracker_id in detections.detections:
        x1, y1, x2, y2 = xyxy
        center = Point(x=(x1+x2)/2, y=(y1+y2)/2)
        tracker_state_new = is_in_line(pt1, pt2, center) >= 0  # Use the center to determine the side

        # Handle new detection
        if tracker_id not in tracker_state or tracker_state[tracker_id] is None:
            tracker_state[tracker_id] = {'state': tracker_state_new, 'direction': None}
            if tracker_id in prev_tracker_state and prev_tracker_state[tracker_id] is not None:
                # If the object was previously tracked and has a known direction,
                # we restore its direction.
                tracker_state[tracker_id]['direction'] = prev_tracker_state[tracker_id]['direction']

        # Handle detection on the same side of the line
        elif tracker_state[tracker_id]['state'] == tracker_state_new:
            continue

        # If the object has completely crossed the line
        else:
            if tracker_state[tracker_id]['state'] and not tracker_state_new:  # From up to down
                if tracker_state[tracker_id]['direction'] != 'down':  # Only count if the previous direction was not 'down'
                    in_count += 1  # Increment in_count for crossing from up to down
                tracker_state[tracker_id]['direction'] = 'down'
            elif not tracker_state[tracker_id]['state'] and tracker_state_new:  # From down to up
                if tracker_state[tracker_id]['direction'] != 'up':  # Only count if the previous direction was not 'up'
                    out_count += 1  # Increment out_count for crossing from down to up
                tracker_state[tracker_id]['direction'] = 'up'

            tracker_state[tracker_id]['state'] = tracker_state_new  # Update the tracker state

    # 更新已经消失的检测对象状态
    for tracker_id in list(tracker_state.keys()):
        if tracker_id not in [item[3] for item in detections.detections]:
            prev_tracker_state[tracker_id] = tracker_state[tracker_id]  # Save the state of the disappeared object
            tracker_state[tracker_id] = None

    return in_count, out_count


if __name__ == '__main__':
    # Initialize video capture to get video properties
    capture = cv2.VideoCapture(VIDEO_PATH)
    if not capture.isOpened():
        print("Error opening video file.")
        exit()

    # Get video properties (width and height)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Close the video capture
    capture.release()

    # 例如 width = 1364 height = 768 pt1 = Point(0, 384) pt2 = Point(1364, 384)
    pt1 = Point(0, height // 2)  # Line starting point at the center of the frame
    pt2 = Point(width, height // 2)  # Line ending point at the center of the frame

    in_count = 0
    out_count = 0
    in_count = 0
    out_count = 0
    prev_tracker_state = {}  # 用于记录上一帧的检测对象状态
    tracker_state = {}
    crossing_ids = set()  # 用于存储已经穿越线的检测对象的ID
    detector = Detector()
    capture = cv2.VideoCapture(VIDEO_PATH)

    # Dictionary to store the trail points of each object
    object_trails = {}

    while True:
        _, im = capture.read()
        if im is None:
            break

        detections = Detections()
        output_image_frame, list_bboxs = objtracker.update(detector, im)
        cv2.line(output_image_frame, (pt1.x, pt1.y), (pt2.x, pt2.y), (0, 0, 255), thickness=2)

        for item_bbox in list_bboxs:
            x1, y1, x2, y2, _, track_id = item_bbox
            detections.add((x1, y1, x2, y2), None, None, track_id)

        # 使用trigger方法来计数穿越
        in_count, out_count = trigger(detections, pt1, pt2, prev_tracker_state, tracker_state, crossing_ids, in_count, out_count)

        # 更新上一帧的检测目标状态
        prev_tracker_state = tracker_state.copy()

        # 清空穿越线集合，准备下一帧的计数
        crossing_ids.clear()

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
        draw_trail(output_image_frame, list(object_trails.values()), trail_colors)

        # Remove trails of objects that are not detected in the current frame
        for tracker_id in list(object_trails.keys()):
            if tracker_id not in [item[3] for item in detections.detections]:
                object_trails.pop(tracker_id)

        text_draw = 'DOWN: ' + str(out_count) + ' , UP: ' + str(in_count)
        output_image_frame = cv2.putText(img=output_image_frame, text=text_draw, org=(10, 50),
                                         fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                                         fontScale=0.75, color=(0, 0, 255), thickness=2)
        
        cv2.imshow('Counting Demo', output_image_frame)
        cv2.waitKey(1)

    capture.release()
    cv2.destroyAllWindows()



























