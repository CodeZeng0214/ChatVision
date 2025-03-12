from PySide6.QtCore import QObject, Signal, Slot
import json
import os
import re
import importlib
import inspect

class TaskProcessor(QObject):
    """处理任务并协调插件之间的交互
    
    任务处理器是应用程序的核心组件，负责:
    1. 分析用户请求，确定需要执行的视觉任务
    2. 调用适当的视觉处理插件执行任务
    3. 在需要时请求用户提供额外参数
    4. 将结果发送回UI界面显示
    """
    result_ready = Signal(dict)  # 当结果准备好时发出的信号，包含结果数据
    parameter_needed = Signal(list, str)  # 当需要参数时发出的信号，包含参数列表和描述文字
    task_completed = Signal(dict)  # 当任务完成时发出的信号，包含最终结果
    
    def __init__(self, llm_client=None):
        super().__init__()
        self.llm_client = llm_client
        self.active_task = None
        self.pending_params = None
        self.plugins = {}
        self.load_plugins()
    
    def load_plugins(self):
        """加载可用的视觉任务插件
        
        这是一个简化版本。在实际应用中，你会扫描插件目录
        并基于可用的插件动态加载模块。当前实现使用硬编码的插件定义。
        每个插件包含名称、描述、关键字和处理函数等信息。
        """
        # 这是一个简化版本。在实际应用中，你会扫描插件目录
        # 并基于可用的插件动态加载模块。
        self.plugins = {
            "object_detection": {
                "name": "物体检测",
                "description": "使用YOLO在图像中检测物体",
                "enabled": True,
                "keywords": ["检测", "物体", "查找", "识别", "识别图中的"],
                "required_params": ["image_path"],
                "optional_params": ["confidence_threshold"],
                "handler": self.handle_object_detection
            },
            "pose_estimation": {
                "name": "姿态估计",
                "description": "估计图像中的人体姿态",
                "enabled": True,
                "keywords": ["姿态", "姿势", "身体位置"],
                "required_params": ["image_path"],
                "optional_params": [],
                "handler": self.handle_pose_estimation
            },
            "image_caption": {
                "name": "图像描述",
                "description": "为图像生成描述文本",
                "enabled": True,
                "keywords": ["描述", "说明", "这是什么", "解释"],
                "required_params": ["image_path"],
                "optional_params": ["language"],
                "handler": self.handle_image_caption
            },
            "face_detection": {
                "name": "人脸检测",
                "description": "在图像中检测人脸",
                "enabled": True,
                "keywords": ["人脸", "脸部", "人", "人物"],
                "required_params": ["image_path"],
                "optional_params": [],
                "handler": self.handle_face_detection
            }
        }
    
    def process_task(self, task_info):
        """处理来自聊天窗口的新任务
        
        分析任务信息，确定是否需要额外参数，然后执行任务或请求参数。
        如果缺少必要参数或需要用户指定摄像头，会发出信号请求这些信息。
        
        参数:
            task_info (dict): 包含任务信息的字典，通常包括消息文本和媒体路径
        """
        self.active_task = task_info
        
        # 检查是否提供了媒体
        if not task_info.get("media_path") and "camera" not in task_info.get("message", "").lower():
            # 确定任务需要什么类型的媒体
            needed_params = self.determine_needed_parameters(task_info.get("message", ""))
            if needed_params:
                self.pending_params = needed_params
                self.parameter_needed.emit(needed_params, "请提供以下信息以完成您的请求:")
                return
        
        # 如果是摄像头请求但未指定摄像头
        if "camera" in task_info.get("message", "").lower() and task_info.get("media_path") != "camera":
            self.pending_params = [{
                "name": "camera_id",
                "label": "选择摄像头",
                "type": "camera_selector"
            }]
            self.parameter_needed.emit(self.pending_params, "请选择要使用的摄像头:")
            return
        
        # 使用可用信息处理任务
        self.execute_task(task_info)
    
    def determine_needed_parameters(self, message):
        """根据消息确定需要哪些参数
        
        分析用户消息，识别任务类型，然后确定缺少哪些必要参数。
        当前主要检查是否需要图像输入。
        
        参数:
            message (str): 用户消息文本
            
        返回:
            list: 包含需要请求的参数定义的列表
        """
        # 尝试识别用户请求的任务类型
        task_type = self.identify_task_type(message)
        if not task_type:
            return []  # 无法确定任务类型
        
        # 获取此任务的必要参数
        plugin_info = self.plugins.get(task_type)
        if not plugin_info:
            return []
        
        # 检查我们需要询问哪些参数
        needed_params = []
        
        for param_name in plugin_info.get("required_params", []):
            if param_name == "image_path":
                needed_params.append({
                    "name": "image_path",
                    "label": "选择一张图片",
                    "type": "image_selector"
                })
        
        return needed_params
    
    def identify_task_type(self, message):
        """识别用户请求的视觉任务类型
        
        通过检查消息中的关键词来确定最合适的视觉处理任务。
        如果找不到明确的匹配，对于包含特定词语的查询会默认使用图像描述功能。
        
        参数:
            message (str): 用户消息文本
            
        返回:
            str or None: 识别出的任务类型ID，如果无法识别则返回None
        """
        message = message.lower()
        
        for plugin_id, plugin_info in self.plugins.items():
            if not plugin_info["enabled"]:
                continue
                
            for keyword in plugin_info["keywords"]:
                if keyword.lower() in message:
                    return plugin_id
        
        # 如果无法确定，对包含"什么"、"解释"、"描述"等词语的查询默认使用图像描述
        if any(word in message for word in ["什么", "解释", "描述"]):
            return "image_caption"
            
        return None
    
    def execute_task(self, task_info):
        """执行已识别的任务
        
        调用相应的处理器执行任务。如果无法确定任务类型但有图像，则默认执行图像描述。
        如果无法识别任务且没有图像，则返回错误信息。
        
        参数:
            task_info (dict): 包含任务信息的字典
        """
        # 识别任务类型
        task_type = self.identify_task_type(task_info.get("message", ""))
        
        if not task_type:
            # 如果有图像但没有明确的任务，默认使用图像描述
            if task_info.get("media_path") and task_info.get("media_type") == "image":
                task_type = "image_caption"
            else:
                # 无法识别任务且没有图像，返回错误
                self.result_ready.emit({"text": "我不确定您想要执行什么任务。请提供更具体的描述或上传图像。"})
                return
        
        # 获取此任务类型的处理器
        plugin_info = self.plugins.get(task_type)
        if not plugin_info or not plugin_info["enabled"]:
            self.result_ready.emit({"text": f"抱歉，{task_type}插件不可用。"})
            return
            
        # 调用适当的处理器
        if "handler" in plugin_info:
            plugin_info["handler"](task_info)
        
    def handle_object_detection(self, task_info):
        """处理物体检测任务
        
        在真实实现中，这会调用YOLO模型。当前实现提供模拟的检测结果。
        检测图像中的物体并返回物体类型和数量。
        
        参数:
            task_info (dict): 包含任务信息的字典
        """
        # 在真实实现中，这会调用YOLO模型
        if task_info.get("media_path") and task_info.get("media_type") == "image":
            # 模拟YOLO检测
            objects = ["人", "椅子", "笔记本电脑", "杯子"]
            counts = {"人": 2, "椅子": 3, "笔记本电脑": 1, "杯子": 2}
            
            # 格式化结果
            result_text = "物体检测结果:\n\n"
            for obj in objects:
                result_text += f"- {obj}: {counts[obj]}\n"
            
            self.result_ready.emit({
                "text": result_text,
                "image_path": task_info["media_path"]  # 在真实应用中，这将是带注释的图像路径
            })
        else:
            self.result_ready.emit({"text": "请提供图像进行物体检测。"})
    
    def handle_pose_estimation(self, task_info):
        """处理姿态估计任务
        
        在真实实现中，这会调用姿态估计模型。当前实现提供模拟的结果。
        识别图像中人物的姿势并返回描述信息。
        
        参数:
            task_info (dict): 包含任务信息的字典
        """
        if task_info.get("media_path") and task_info.get("media_type") == "image":
            # 模拟姿态估计
            result_text = "姿态估计结果:\n\n"
            result_text += "图像中检测到2人。\n"
            result_text += "人物1: 站立姿势，双臂抬起\n"
            result_text += "人物2: 坐姿\n"
            
            self.result_ready.emit({
                "text": result_text,
                "image_path": task_info["media_path"]  # 在真实应用中，这将是带姿态注释的图像路径
            })
        else:
            self.result_ready.emit({"text": "请提供图像进行姿态估计。"})
    
    def handle_image_caption(self, task_info):
        """处理图像描述任务
        
        在真实实现中，这会调用BLIP或类似模型。当前实现提供模拟的描述结果。
        生成对图像内容的自然语言描述。
        
        参数:
            task_info (dict): 包含任务信息的字典
        """
        if task_info.get("media_path") and task_info.get("media_type") == "image":
            # 模拟图像描述
            result_text = "图像描述:\n\n"
            result_text += "一群人围坐在桌子旁，在咖啡馆里使用笔记本电脑工作。"
            
            self.result_ready.emit({
                "text": result_text,
                "image_path": task_info["media_path"]
            })
        else:
            self.result_ready.emit({"text": "请提供图像进行描述。"})
    
    def handle_face_detection(self, task_info):
        """处理人脸检测任务
        
        在真实实现中，这会调用人脸检测模型。当前实现提供模拟的结果。
        检测图像中的人脸并估计年龄范围。
        
        参数:
            task_info (dict): 包含任务信息的字典
        """
        if task_info.get("media_path") and task_info.get("media_type") == "image":
            # 模拟人脸检测
            result_text = "人脸检测结果:\n\n"
            result_text += "图像中检测到3张人脸。\n"
            result_text += "估计年龄: 25-30岁, 35-40岁, 20-25岁\n"
            
            self.result_ready.emit({
                "text": result_text,
                "image_path": task_info["media_path"]  # 在真实应用中，这将是带人脸标记的图像路径
            })
        else:
            self.result_ready.emit({"text": "请提供图像进行人脸检测。"})

    def request_camera_preview(self):
        """请求在侧边栏显示摄像头预览
        
        发出一个信号，通知侧边栏显示摄像头预览界面。
        """
        self.result_ready.emit({"camera": True})
    
    def preview_image(self, image_path):
        """将图像发送到侧边栏预览
        
        当用户选择图像或需要预览图像时使用此方法。
        
        参数:
            image_path (str): 图像文件的路径
        """
        self.result_ready.emit({
            "image_path": image_path
        })
        
    def preview_video(self, video_path):
        """将视频发送到侧边栏预览
        
        当用户选择视频或需要预览视频时使用此方法。
        
        参数:
            video_path (str): 视频文件的路径
        """
        self.result_ready.emit({
            "video_path": video_path
        })
    
    @Slot(dict)
    def process_parameters(self, params):
        """处理从参数输入小部件接收的参数
        
        当用户提交额外参数后，更新当前任务信息并重新执行任务。
        
        参数:
            params (dict): 用户提供的参数字典
        """
        if self.pending_params and self.active_task:
            # 使用新参数更新活动任务
            for key, value in params.items():
                self.active_task[key] = value
            
            # 清除待定参数
            self.pending_params = None
            
            # 使用新参数重新执行任务
            self.execute_task(self.active_task)
            
    # 添加更新插件设置的方法
    @Slot(str, dict)
    def update_plugin_settings(self, plugin_id, settings):
        """更新特定插件的设置
        
        允许插件管理器更改插件的配置参数，如模型选择、阈值等。
        
        参数:
            plugin_id (str): 要更新的插件ID
            settings (dict): 新的设置值字典
        """
        if plugin_id in self.plugins:
            plugin = self.plugins[plugin_id]
            # 使用新设置更新插件参数
            for key, value in settings.items():
                if key in plugin.get("parameters", {}):
                    plugin["parameters"][key]["default"] = value
            
            print(f"已更新插件{plugin_id}的设置: {settings}")
