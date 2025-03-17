import numpy as np
import cv2
import objtracker
from objdetector import Detector

VIDEO_PATH = './video/test_person.mp4'

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

def isInsidePolygon(point, polygon):
    isInside = False
    currentVertex = -1
    polygonLength = len(polygon)
    previousVertex = polygonLength - 1
    while currentVertex < polygonLength - 1:
        currentVertex += 1
        if ((polygon[currentVertex][0] <= point.x and point.x < polygon[previousVertex][0]) or 
            (polygon[previousVertex][0] <= point.x and point.x < polygon[currentVertex][0])):
            if (point.y < (polygon[previousVertex][1] - polygon[currentVertex][1]) * 
                (point.x - polygon[currentVertex][0]) / 
                (polygon[previousVertex][0] - polygon[currentVertex][0]) + polygon[currentVertex][1]):
                isInside = not isInside
        previousVertex = currentVertex
    return isInside

def drawAndFillPolygon(image, polygonPoints, fillColor):
    # Convert the polygon points to NumPy array
    polygonPoints = np.array([polygonPoints], dtype=np.int32)

    # Create a mask with the same size as the image
    mask = np.zeros_like(image)

    # Fill the polygon with the specified color on the mask
    mask = cv2.fillPoly(mask, [polygonPoints], color=fillColor)

    # Draw the polygon contour on the original image
    cv2.polylines(image, [polygonPoints], isClosed=True, color=(255, 0, 255), thickness=5)

    # Overlay the mask and the original image
    overlaidImage = cv2.addWeighted(image, 0.7, mask, 0.3, 0)

    return overlaidImage

# 指定敏感区域的多边形顶点坐标
polygonPoints = [[710, 200], [1110, 200], [810, 400], [410, 400]]
color_light_yellow = (0, 155, 255)   # Light yellow color

# Dictionary to store previous positions of each person
person_positions = {}

if __name__ == '__main__':
    capture = cv2.VideoCapture(VIDEO_PATH)
    if not capture.isOpened():
        print("Error opening video file.")
        exit()

    detector = Detector()

    while True:
        ret, frame = capture.read()
        if not ret:
            break

        # Draw the boundary monitoring area 绘制敏感区域
        frame = drawAndFillPolygon(frame, polygonPoints, color_light_yellow)

        # Update the tracker and get the bounding boxes of the persons
        output_image_frame, bbox_list = objtracker.update(detector, frame)

        for bbox in bbox_list:
            x1, y1, x2, y2, _, track_id = bbox

            # Get the center point of the person
            person_center = Point(x=(x1+x2)/2, y=(y1+y2)/2)

            # Check if the person is inside the polygon
            if isInsidePolygon(person_center, polygonPoints):
                warning_text = f'Warning! ID: {track_id}'
                cv2.putText(output_image_frame, warning_text, (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)

            # Add the current person's position to the trail
            if track_id in person_positions:
                person_positions[track_id].append((person_center.x, person_center.y))
                # Check if the trail length exceeds 50 frames, and remove the oldest position
                if len(person_positions[track_id]) > 50:
                    person_positions[track_id].pop(0)
            else:
                person_positions[track_id] = [(person_center.x, person_center.y)]

            # Draw the trail for each person
            trail_color = (0, 0, 255)  # Red color for the trail
            for prev_pos in person_positions[track_id]:
                cv2.circle(output_image_frame, (int(prev_pos[0]), int(prev_pos[1])), 3, trail_color, -1)

        cv2.imshow('Boundary Monitoring', output_image_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    capture.release()
    cv2.destroyAllWindows()
