## 使用YOLO进行图像识别的插件实现

from core.Plugin import Plugin
import os

### ========== 全局参数 ========== ###
DET_WEI_PATH = './/weights//YOLO_World//yolov8s-worldv2.pt' # 默认的图像检测类插件的权重路径
POSE_WEI_PATH = ".//weights//YOLO11//yolo11s-pose.pt" # 默认的人体姿态估计类插件的权重路径


### ========== 具体实现 ========== ###

class ObjDetectYOLOPlugin(Plugin):
    """
    图像物体检测插件实现。\n
    参数：{'image_path': str, 'weight_path': str (可选), 'is_show': bool (可选)}\n
    """

    def __init__(self):
        super().__init__('ObjectDetect', 
                        "使用YOLO进行图像物体检测。",
                         [{'name': 'image_path', 'description': '待检测的图像路径', 'required': True},
                          {'name': 'weight_path', 'description': 'YOLO权重路径', 'required': False, 'default': DET_WEI_PATH},
                          {'name': 'is_show', 'description': '是否显示检测结果', 'required': False, 'default': True}])
        self.execute = self.objDetect
    
    # 图像物体识别（YOLO）
    def objDetect(self, params):
        """
        物体检测插件实现。\n
        参数：{'image_path': str, 'weight_path': str (可选), 'is_show': bool (可选)}\n
        """
        from ultralytics import YOLO
        image_path = params['image_path']
        weight_path = params.get('weight_path', DET_WEI_PATH)
        is_show = params.get('is_show', False)

        # 加载 YOLO 模型
        model = YOLO(weight_path)
        print("正在进行物体检测")
        results = model.predict(source=image_path, 
                                save=False, save_txt=False, save_conf=False, project='./results',  
                                verbose=False, line_width=2)
        print("检测完成")

        # 格式化结果
        detection_results = ['检测到以下对象：']
        for result in results:
            # result是一个检测结果对象，通常包含边界框、标签、置信度等信息
            detection_result = ''
            for box in result.boxes:  # 访问每个检测的框
            # 提取边界框坐标、置信度和标签
                x1, y1, x2, y2 = box.xyxy[0]  # 左上角和右下角坐标
                conf = box.conf[0]  # 置信度
                conf = 100*conf
                cls = int(box.cls[0])  # 类别索引
                label = model.names[cls]  # 获取类别名称
                detection_result += f"检测到有一个{conf:.2f}%置信度的 {label} 对象\n"
            if is_show: result.show(line_width=2)
            detection_results.append(detection_result)
        if is_show: detection_results.append("显示状态：检测结果已经显示于屏幕上")
        return '\n'.join(detection_results)
    

class HummanPoseTrackYOLOPlugin(Plugin):
    """
    人体姿态跟踪插件实现。\n
    参数：{'image_path': str, 'weight_path': str (可选), 'is_show': bool (可选)}\n
    """
    def __init__(self):
        super().__init__('HumanPoseEstimate', 
                         "使用YOLO进行人体姿态跟踪。", 
                         [{'name': 'image_path', 'description': '待检测的图像路径', 'required': True},
                          {'name': 'weight_path', 'description': 'YOLO权重路径', 'required': False, 'default': POSE_WEI_PATH},
                          {'name': 'is_show', 'description': '是否显示检测结果', 'required': False, 'default': True}])
        self.execute = self.hummanPoseTrack

    # 人体姿态跟踪（YOLO）
    def hummanPoseTrack(self, params):
        """
        人体姿态跟踪插件实现。\n
        参数：{'image_path': str, 'weight_path': str (可选), 'is_show': bool (可选)}\n
        """
        from ultralytics import YOLO
                
        image_path = params['image_path']
        weight_path = params.get('weight_path', POSE_WEI_PATH)
        is_show = params.get('is_show', False)
        
        model = YOLO(weight_path)
        
        results = model.track(source=image_path, show=is_show, stream=True)
        if results : return("已经显示于屏幕上")
