import os
import cv2
import tempfile
import logging
import numpy as np
import random
from plugins.base_plugin import BasePlugin

class BlipPlugin(BasePlugin):
    """BLIP图像描述插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "BLIP图像描述"
        self.description = "使用BLIP模型生成图像描述"
        self.config = {
            "model_path": "",  # 模型路径
            "use_gpu": False,  # 是否使用GPU
            "result_dir": os.path.join(tempfile.gettempdir(), "chatvision_results")
        }
        
        # 创建结果目录
        os.makedirs(self.config["result_dir"], exist_ok=True)
        
        # 尝试加载模型
        self.model = None
        try:
            self._load_model()
        except Exception as e:
            logging.error(f"加载BLIP模型失败: {e}")
    
    def _load_model(self):
        """加载BLIP模型"""
        try:
            # 这里简化实现，真实环境中应该加载实际的BLIP模型
            # 由于BLIP需要比较多的依赖，这里提供一个模拟实现
            logging.info("模拟加载BLIP模型")
            self.model = "mock_blip_model"
            
            # 实际代码会类似这样:
            # from transformers import BlipProcessor, BlipForConditionalGeneration
            # self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            # self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
            # 
            # if self.config["use_gpu"] and torch.cuda.is_available():
            #     self.model = self.model.to("cuda")
            
        except ImportError:
            logging.error("未安装BLIP依赖，插件无法正常工作")
            self.model = None
    
    def process(self, parameters):
        """处理图像描述任务"""
        # 获取图像参数
        image_path = None
        
        # 从参数中获取图像路径
        if "image" in parameters:
            image_path = parameters["image"]
        elif "files" in parameters and parameters["files"]:
            # 使用第一个图片文件
            for file_path in parameters["files"]:
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    image_path = file_path
                    break
        
        if not image_path or not os.path.exists(image_path):
            return "未找到有效的图像文件"
        
        try:
            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                return f"无法读取图像: {image_path}"
            
            # 生成图像描述
            description = self._generate_description(image, image_path)
            
            # 添加边框标记进行可视化
            result_image = self._visualize_description(image, description)
            
            # 保存结果图像
            result_filename = os.path.basename(image_path)
            result_path = os.path.join(self.config["result_dir"], f"blip_{result_filename}")
            cv2.imwrite(result_path, result_image)
            
            # 返回结果
            return {
                "original_image": image_path,
                "result_image": result_path,
                "description": description,
                "summary": description
            }
            
        except Exception as e:
            logging.error(f"BLIP处理失败: {e}")
            return f"处理图像时发生错误: {str(e)}"
    
    def _generate_description(self, image, image_path):
        """生成图像描述"""
        # 真实实现应该使用BLIP模型生成描述
        # 这里模拟一些描述
        
        # 根据图像路径生成一个伪随机数，确保同一图像生成相同的描述
        random.seed(os.path.basename(image_path))
        
        # 简单的图像分析：检测是否有人脸、颜色分布等
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 人脸检测
        try:
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            has_faces = len(faces) > 0
        except:
            has_faces = False
        
        # 分析图像颜色
        avg_color = np.mean(image, axis=(0, 1))
        is_bright = np.mean(avg_color) > 127
        
        # 检测图像中的形状
        try:
            # 边缘检测
            edges = cv2.Canny(gray, 100, 200)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            has_objects = len(contours) > 10
        except:
            has_objects = True
        
        # 根据分析结果生成描述
        templates = [
            "这是{time}拍摄的一张{brightness}图片，{people}{objects}。",
            "图像显示{people}在{brightness}的环境中{action}。",
            "照片中{people}{objects}，整体氛围{brightness}。",
            "这是一张{brightness}的照片，{people}{objects}。"
        ]
        
        time_options = ["白天", "夜晚", "黄昏", "清晨"]
        brightness_options = ["明亮", "昏暗", "色彩鲜艳", "色彩柔和"]
        people_options = [
            "有一个人", "有多个人", "有一群人", 
            "没有人", "有一个儿童", "有一家人"
        ]
        objects_options = [
            "有一些建筑物", "有美丽的风景", "有一些植物", 
            "有一些家具", "有一只宠物", "有几辆车"
        ]
        action_options = ["站立", "坐着", "行走", "交谈", "微笑", "工作"]
        
        # 基于图像分析选择描述元素
        time = random.choice(time_options)
        brightness = "明亮" if is_bright else "昏暗"
        people = random.choice(people_options if has_faces else people_options[3:])
        objects = random.choice(objects_options) if has_objects else "没有明显的物体"
        action = random.choice(action_options)
        
        # 生成最终描述
        template = random.choice(templates)
        description = template.format(
            time=time, 
            brightness=brightness, 
            people=people, 
            objects=objects, 
            action=action
        )
        
        return description
    
    def _visualize_description(self, image, description):
        """在图像上添加描述文字"""
        result_image = image.copy()
        
        # 在图像底部添加黑色背景条
        h, w = result_image.shape[:2]
        overlay = result_image[h-70:h, :].copy()
        cv2.rectangle(result_image, (0, h-70), (w, h), (0, 0, 0), -1)
        
        # 添加半透明效果
        alpha = 0.7
        cv2.addWeighted(overlay, alpha, result_image[h-70:h, :], 1-alpha, 0, result_image[h-70:h, :])
        
        # 在黑色背景上添加文字
        # 根据文字长度分行显示
        max_chars = 50  # 每行最大字符数
        description_lines = []
        for i in range(0, len(description), max_chars):
            if i + max_chars < len(description):
                # 查找合适的断句位置
                break_pos = description[i:i+max_chars].rfind("，")
                if break_pos == -1:
                    break_pos = description[i:i+max_chars].rfind("。")
                if break_pos == -1:
                    break_pos = max_chars
                description_lines.append(description[i:i+break_pos+1])
                i = i + break_pos + 1
            else:
                description_lines.append(description[i:])
        
        # 添加文字
        for i, line in enumerate(description_lines):
            cv2.putText(
                result_image, line, (10, h-45+i*20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
            )
        
        return result_image
    
    def get_required_parameters(self):
        """获取插件需要的参数列表"""
        return ["image"]
    
    def get_task_types(self):
        """获取插件支持的任务类型列表"""
        return ["image_description"]
