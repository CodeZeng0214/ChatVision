## 测试插件

from core.Plugin import Plugin


### ========== 全局参数 ========== ###
DET_WEI_PATH = './/weights//YOLO_World//yolov8s-worldv2.pt' # 默认的图像检测类插件的权重路径

### ========== 具体实现 ========== ###

class TestPlugin(Plugin):
    """
    测试插件。\n
    参数：{'image_path': str, 'weight_path': str (可选), 'is_show': bool (可选)}\n
    """
    from ultralytics import YOLO
    
    def __init__(self):
        super().__init__( 'TestPlugin' ,
                         "测试插件。",
                         [{'name': 'image_path', 'description': '待检测的图像路径', 'required': True},
                          {'name': 'weight_path', 'description': 'YOLO权重路径', 'required': False, 'default': DET_WEI_PATH},
                          {'name': 'is_show', 'description': '是否显示检测结果', 'required': False, 'default': True}])
        self.execute = self.Test
    
    # 图像物体识别（YOLO）
    def Test(self, params):
        from ultralytics import YOLO
        pass