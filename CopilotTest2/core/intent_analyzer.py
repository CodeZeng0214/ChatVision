import re
import json
import logging
from enum import Enum, auto
import os

class TaskType(Enum):
    GENERAL_CHAT = auto()
    IMAGE_RECOGNITION = auto()
    IMAGE_DESCRIPTION = auto()
    POSE_ESTIMATION = auto()
    BATCH_PROCESSING = auto()
    REALTIME_PROCESSING = auto()

class IntentAnalyzer:
    """分析用户意图，确定任务类型和参数"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    def analyze_intent(self, user_message, attached_files=None):
        """
        分析用户消息意图
        
        Args:
            user_message: 用户消息文本
            attached_files: 附加文件列表（图片、视频等）
            
        Returns:
            dict: 分析结果，包含任务类型和参数
        """
        # 构建意图分析提示
        prompt = self._build_intent_prompt(user_message, attached_files)
        
        # 使用简单规则进行意图分析
        task_type = "general_chat"  # 默认为普通聊天
        parameters = {}
        
        # 如果有附加文件，进行进一步分析
        if attached_files:
            # 根据文件类型和消息内容判断任务类型
            file_types = [self._get_file_type(f) for f in attached_files]
            
            # 检查是否包含图像文件
            if "image" in file_types:
                image_files = [f for i, f in enumerate(attached_files) if file_types[i] == "image"]
                
                # 根据消息内容确定是图像识别还是图像描述
                if any(keyword in user_message.lower() for keyword in ["识别", "检测", "识别物体", "detect", "recognize"]):
                    task_type = "image_recognition"
                    parameters["image"] = image_files[0]  # 使用第一张图片
                    parameters["files"] = image_files
                elif any(keyword in user_message.lower() for keyword in ["姿势", "姿态", "pose", "人体姿态"]):
                    task_type = "pose_estimation"
                    parameters["image"] = image_files[0]
                    parameters["files"] = image_files
                elif any(keyword in user_message.lower() for keyword in ["批量", "文件夹", "目录", "batch", "多个图片", "多张图片"]):
                    task_type = "batch_processing"
                    parameters["files"] = image_files
                elif any(keyword in user_message.lower() for keyword in ["实时", "摄像头", "相机", "camera", "realtime", "视频", "video"]):
                    task_type = "realtime_processing"
                    if "video" in file_types:
                        video_files = [f for i, f in enumerate(attached_files) if file_types[i] == "video"]
                        parameters["video"] = video_files[0]
                else:
                    # 默认使用图像描述
                    task_type = "image_description"
                    parameters["image"] = image_files[0]
                    parameters["files"] = image_files
            
            # 检查是否包含视频文件
            elif "video" in file_types:
                video_files = [f for i, f in enumerate(attached_files) if file_types[i] == "video"]
                task_type = "realtime_processing"
                parameters["video"] = video_files[0]
                parameters["files"] = video_files
        
        return {
            "task_type": task_type,
            "parameters": parameters
        }
    
    def _build_intent_prompt(self, user_message, attached_files):
        """构建意图分析提示"""
        prompt = f"用户消息: {user_message}\n"
        
        if attached_files:
            prompt += "附加文件:\n"
            for file in attached_files:
                file_type = self._get_file_type(file)
                prompt += f"- {os.path.basename(file)} ({file_type})\n"
        
        prompt += "\n请分析用户意图，确定任务类型和所需参数。"
        return prompt
    
    def _get_file_type(self, filepath):
        """
        获取文件类型
        
        Args:
            filepath: 文件路径
            
        Returns:
            str: 文件类型 ("image", "video", "directory" 或 "unknown")
        """
        if not filepath or not os.path.exists(filepath):
            return "unknown"
            
        # 检查是否为目录
        if os.path.isdir(filepath):
            return "directory"
            
        # 检查文件扩展名
        ext = os.path.splitext(filepath)[1].lower()
        
        # 图像文件扩展名
        image_exts = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']
        if ext in image_exts:
            return "image"
            
        # 视频文件扩展名
        video_exts = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv']
        if ext in video_exts:
            return "video"
            
        return "unknown"
    
    def check_parameters(self, task_type, parameters):
        """
        检查任务类型的参数是否完整
        
        Args:
            task_type: 任务类型
            parameters: 已有参数
            
        Returns:
            tuple: (是否完整, 缺少的参数列表)
        """
        required_params = self._get_required_parameters(task_type)
        
        # 检查所有必需参数是否都存在
        missing_params = []
        for param in required_params:
            if param not in parameters:
                missing_params.append(param)
                
        return (len(missing_params) == 0), missing_params
    
    def _get_required_parameters(self, task_type):
        """
        获取指定任务类型所需的参数列表
        
        Args:
            task_type: 任务类型
            
        Returns:
            list: 参数名称列表
        """
        # 不同任务类型的必需参数
        param_map = {
            "general_chat": [],
            "image_recognition": ["image"],
            "image_description": ["image"],
            "pose_estimation": ["image"],
            "batch_processing": ["directory"],
            "realtime_processing": ["camera_id", "task"]
        }
        
        return param_map.get(task_type, [])
