# import sys
# import os
# # 获取当前脚本所在目录
# current_dir = os.path.dirname(os.path.abspath('./modules/YOLODeepsort/YOLO_Deepsort.py'))
# # 将modules和脚本所在目录路径添加到sys.path
# sys.path.append(current_dir)
# #print(sys.path)
from modules.YOLODeepsort.YOLO_Deepsort import PedCarTrack
params ={}
params['image_path'] = "D:\Code\YOLO_correlation\ChatYOLO\photos\\test_traffic.mp4"
PedCarTrack(params)