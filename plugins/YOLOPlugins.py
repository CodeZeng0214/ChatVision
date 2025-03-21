## 使用YOLO进行图像识别的插件实现

from core.Plugin import Plugin
import os
from core.AuxiliaryFunction import get_all_image_paths

### ========== 全局参数 ========== ###
DET_WEI_PATH = './/weights//YOLO_World//yolov8s-worldv2.pt' # 默认的图像检测类插件的权重路径
POSE_WEI_PATH = ".//weights//YOLO11//yolo11s-pose.pt" # 默认的人体姿态估计类插件的权重路径
RESULT_PATH = ".//results//YOLO//Temp" # 默认的检测结果保存路径


### ========== 具体实现 ========== ###

class ObjDetectYOLOPlugin(Plugin):
    """
    图像物体检测插件实现。\n
    """

    def __init__(self):
        from ultralytics import YOLO
        
        super().__init__('ObjectDetect', 
                        "使用YOLO进行图像物体检测。",
                         [{'name': 'image_path', 'description': '待检测的图像路径', 'required': True},
                          {'name': 'weight_path', 'description': 'YOLO权重路径', 'required': False, 'default': DET_WEI_PATH},
                          {'name': 'is_show', 'description': '是否显示检测结果', 'required': False, 'default': True},
                          {'name': 'is_save', 'description': '是否保存检测结果', 'required': False, 'default': False},
                          {'name': 'save_path', 'description': '检测结果的保存路径', 'required': False, 'default': RESULT_PATH}])
        self.execute = self.objDetect
        self.results:list[str] = [] # 存储检测结果的路径
    
    # 图像物体识别（YOLO）
    def objDetect(self, params):
        """
        物体检测插件实现。\n
        参数: \n
        'image_path':str (必选)\n
        'weight_path':str (可选)\n
        'is_show':bool (可选)\n
        'is_save':bool (可选)\n
        'result_path':str (可选)\n
        """
        from ultralytics import YOLO
        
        self.results.clear() # 清空检测结果路径
        
        image_path = params['image_path']
        weight_path = params.get('weight_path', DET_WEI_PATH)
        is_show = params.get('is_show', False)
        is_save = params.get('is_save', True)
        result_path = params.get('result_path', RESULT_PATH)

        # 加载 YOLO 模型
        model = YOLO(weight_path)
        print("正在使用'YOLO'进行物体检测")
        results = model.predict(source=image_path, 
                                save=is_save,save_txt=True, save_conf=True, project=result_path,  
                                verbose=False, line_width=2)
        
        print("检测完成")
    
        # 格式化结果
        detection_results = [f'在{image_path}上检测到以下对象：']
        for result in results:
            # result是一个检测结果对象，通常包含边界框、标签、置信度等信息
            self.results.extend(get_all_image_paths(result.save_dir))
            detection_result = ''
            for box in result.boxes:  # 访问每个检测的框
            # 提取边界框坐标、置信度和标签
                x1, y1, x2, y2 = box.xyxy[0]  # 左上角和右下角坐标
                conf = box.conf[0]  # 置信度
                conf = 100*conf
                cls = int(box.cls[0])  # 类别索引
                label = model.names[cls]  # 获取类别名称
                detection_result += f"检测到有一个{conf:.2f}%置信度的 {label} 对象\n"
            detection_results.append(detection_result)
        if is_show: detection_results.append("显示状态：检测结果已经显示于屏幕上")
        return '\n'.join(detection_results)
    

class HummanPoseTrackYOLOPlugin(Plugin):
    """
    人体姿态跟踪插件实现。\n
    """
    def __init__(self):
        from ultralytics import YOLO
        
        super().__init__('HumanPoseEstimate', 
                         "使用YOLO进行人体姿态跟踪。", 
                       [{'name': 'image_path', 'description': '待检测的图像路径', 'required': True},
                        {'name': 'weight_path', 'description': 'YOLO权重路径', 'required': False, 'default': POSE_WEI_PATH},
                        {'name': 'is_show', 'description': '是否显示检测结果', 'required': False, 'default': True},
                        {'name': 'is_save', 'description': '是否保存检测结果', 'required': False, 'default': False},
                        {'name': 'save_path', 'description': '检测结果的保存路径', 'required': False, 'default': RESULT_PATH}])
        self.execute = self.hummanPoseTrack

    # 人体姿态跟踪（YOLO）
    def hummanPoseTrack(self, params):
        """
        人体姿态跟踪插件实现。\n
        参数：\n
        'image_path':str (必选)\n
        'weight_path':str (可选)\n
        'is_show':bool (可选)\n
        'is_save':bool (可选)\n
        'result_path':str (可选)\n
        """
        from ultralytics import YOLO
                
        image_path = params['image_path']
        weight_path = params.get('weight_path', POSE_WEI_PATH)
        is_show = params.get('is_show', False)
        
        model = YOLO(weight_path)
        
        results = model.track(source=image_path, show=is_show, stream=True)
        if results : return("已经显示于屏幕上")