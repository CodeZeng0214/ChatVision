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
        # 定义任务相关的关键词
        self.task_keywords = {
            "image_recognition": [
                "识别", "检测", "识别物体", "detect", "recognize", "recognition", 
                "物体", "找出", "有什么东西", "yolo", "是什么"
            ],
            "image_description": [
                "描述", "describe", "告诉我这是什么", "这张图", "看到了什么", 
                "内容是什么", "图中是什么", "解释图片", "blip"
            ],
            "pose_estimation": [
                "姿势", "姿态", "pose", "人体姿态", "肢体", "动作", "站姿", 
                "人体关键点", "关键点检测", "skeleton"
            ],
            "batch_processing": [
                "批量", "文件夹", "目录", "batch", "多个图片", "多张图片",
                "所有图片", "一组", "一批", "处理多个"
            ],
            "realtime_processing": [
                "实时", "摄像头", "相机", "camera", "realtime", "视频", "video",
                "直播", "stream", "流"
            ]
        }
    
    def analyze_intent(self, user_message, attached_files=None):
        """
        分析用户消息意图
        
        Args:
            user_message: 用户消息文本
            attached_files: 附加文件列表（图片、视频等）
            
        Returns:
            dict: 分析结果，包含任务类型和参数
        """
        # 默认设置为普通聊天
        task_type = "general_chat"  
        parameters = {}
        
        # 文本为空且没有附件，肯定是普通聊天
        if not user_message.strip() and not attached_files:
            return {"task_type": task_type, "parameters": parameters}
            
        # 如果有附加文件，可能需要进行图像处理
        has_image_files = False
        has_video_files = False
        
        if attached_files:
            # 分析附加文件类型
            file_types = [self._get_file_type(f) for f in attached_files]
            has_image_files = "image" in file_types
            has_video_files = "video" in file_types
            
            # 获取图像和视频文件列表
            image_files = [f for i, f in enumerate(attached_files) if file_types[i] == "image"]
            video_files = [f for i, f in enumerate(attached_files) if file_types[i] == "video"]
        
        # 任务意图检测 - 先检查明确的任务关键词
        detected_task = self._detect_task_from_keywords(user_message)
        
        if detected_task:
            # 如果检测到明确的任务关键词，使用该任务
            task_type = detected_task
            
            # 准备任务参数
            if task_type == "image_recognition" and has_image_files:
                parameters["image"] = image_files[0]
                parameters["files"] = image_files
            elif task_type == "image_description" and has_image_files:
                parameters["image"] = image_files[0]
                parameters["files"] = image_files
            elif task_type == "pose_estimation" and has_image_files:
                parameters["image"] = image_files[0]
                parameters["files"] = image_files
            elif task_type == "batch_processing" and has_image_files:
                parameters["files"] = image_files
            elif task_type == "realtime_processing":
                if has_video_files:
                    parameters["video"] = video_files[0]
                    parameters["files"] = video_files
                else:
                    parameters["camera_id"] = 0  # 默认摄像头
        
        # 如果没有检测到明确任务，但有图像或视频文件附件
        elif has_image_files or has_video_files:
            # 根据消息内容和文件类型推断可能的任务
            
            # 如果消息很短或为空，判断为用户想要处理附加的媒体文件
            if len(user_message.strip()) <= 10:
                # 短消息+图片：默认为图像描述
                if has_image_files:
                    task_type = "image_description"
                    parameters["image"] = image_files[0]
                    parameters["files"] = image_files
                # 短消息+视频：默认为实时处理
                elif has_video_files:
                    task_type = "realtime_processing"
                    parameters["video"] = video_files[0]
                    parameters["files"] = video_files
            else:
                # 如果消息较长，则可能是普通聊天，保持默认的general_chat
                # 但如果消息中有"这张图"、"这个视频"等指示词，可能是在询问媒体内容
                if has_image_files and any(phrase in user_message.lower() for phrase in ["这张图", "图中", "图像", "图片里"]):
                    task_type = "image_description"
                    parameters["image"] = image_files[0]
                    parameters["files"] = image_files
        
        return {
            "task_type": task_type,
            "parameters": parameters
        }
    
    def _detect_task_from_keywords(self, message):
        """从消息中检测任务类型"""
        # 转换为小写以进行大小写不敏感匹配
        lower_message = message.lower()
        
        # 检查每种任务类型的关键词
        for task_type, keywords in self.task_keywords.items():
            for keyword in keywords:
                # 使用正则表达式进行单词边界匹配，避免部分匹配
                if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', lower_message) or keyword.lower() in lower_message:
                    return task_type
        
        # 没有找到明确的任务关键词
        return None
    
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
        # 普通聊天不需要额外参数
        if task_type == "general_chat":
            return True, []
            
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
