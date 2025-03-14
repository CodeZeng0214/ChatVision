import os
import cv2
import numpy as np
import tempfile
import logging
import random
from plugins.base_plugin import BasePlugin

class PosePlugin(BasePlugin):
    """姿态估计插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "姿态估计"
        self.description = "检测图像中的人体姿态"
        self.config = {
            "model_path": "",  # 模型路径
            "confidence_threshold": 0.5,
            "result_dir": os.path.join(tempfile.gettempdir(), "chatvision_results")
        }
        
        # 创建结果目录
        os.makedirs(self.config["result_dir"], exist_ok=True)
        
        # 尝试加载模型
        self._load_model()
    
    def _load_model(self):
        """加载姿态估计模型"""
        try:
            # 这里使用OpenPose模型
            # 实际应用中应该使用完整的OpenPose或其他姿态估计模型
            logging.info("加载姿态估计模型")
            
            # 设置模拟模式为默认状态
            self.net = None
            self.has_model = False
            self.simulation_mode = True
            
            # 尝试加载OpenCV自带的人体姿态估计模型
            try:
                # 检查DNN数据目录是否存在
                dnn_dir = os.path.join(cv2.data.haarcascades, "../dnn")
                proto_file = os.path.join(dnn_dir, "openpose_pose_coco.prototxt")
                weights_file = os.path.join(dnn_dir, "openpose_pose_coco.caffemodel")
                
                # 如果文件不存在，提供下载信息
                if not os.path.exists(weights_file) or not os.path.exists(proto_file):
                    logging.warning("OpenPose模型文件不存在。您可能需要手动下载模型文件。")
                    logging.warning("姿态估计插件将使用模拟模式。")
                else:
                    self.net = cv2.dnn.readNetFromCaffe(proto_file, weights_file)
                    self.has_model = True
                    self.simulation_mode = False
                    logging.info("成功加载姿态估计模型")
            except Exception as e:
                logging.warning(f"加载OpenPose模型失败: {e}")
                    
            # 定义身体部位连接
            self.BODY_PARTS = {
                "Nose": 0, "Neck": 1, "RShoulder": 2, "RElbow": 3, "RWrist": 4,
                "LShoulder": 5, "LElbow": 6, "LWrist": 7, "RHip": 8, "RKnee": 9,
                "RAnkle": 10, "LHip": 11, "LKnee": 12, "LAnkle": 13, "REye": 14,
                "LEye": 15, "REar": 16, "LEar": 17
            }
            
            self.POSE_PAIRS = [
                ["Neck", "RShoulder"], ["Neck", "LShoulder"], ["RShoulder", "RElbow"],
                ["RElbow", "RWrist"], ["LShoulder", "LElbow"], ["LElbow", "LWrist"],
                ["Neck", "RHip"], ["RHip", "RKnee"], ["RKnee", "RAnkle"], ["Neck", "LHip"],
                ["LHip", "LKnee"], ["LKnee", "LAnkle"], ["Neck", "Nose"], ["Nose", "REye"],
                ["REye", "REar"], ["Nose", "LEye"], ["LEye", "LEar"]
            ]
                
        except Exception as e:
            logging.error(f"初始化姿态估计模型失败: {e}")
            self.net = None
            self.has_model = False
            self.simulation_mode = True
    
    def process(self, parameters):
        """处理姿态估计任务"""
        # 获取图像参数
        image_path = None
        
        # 从参数中获取图像路径
        if "image" in parameters:
            image_path = parameters["image"]
        elif "files" in parameters and parameters["files"]:
            # 使用第一个文件
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
                
            # 如果有实际模型，进行姿态估计
            if self.has_model and isinstance(self.net, cv2.dnn.Net) and not self.simulation_mode:
                result_image, pose_data = self._detect_pose_with_model(image)
            else:
                # 否则模拟姿态估计
                result_image, pose_data = self._simulate_pose_detection(image)
            
            # 保存结果图像
            result_filename = os.path.basename(image_path)
            result_path = os.path.join(self.config["result_dir"], f"pose_{result_filename}")
            cv2.imwrite(result_path, result_image)
            
            # 返回结果
            return_result = {
                "original_image": image_path,
                "result_image": result_path,
                "pose_data": pose_data,
                "summary": self._generate_pose_summary(pose_data)
            }
            
            # 如果是模拟模式，添加提示
            if not self.has_model or self.simulation_mode:
                return_result["summary"] += " (模拟姿态估计)"
                
            return return_result
            
        except Exception as e:
            logging.error(f"姿态估计失败: {e}")
            return f"处理图像时发生错误: {str(e)}"
    
    def _detect_pose_with_model(self, image):
        """使用实际模型进行姿态估计"""
        height, width = image.shape[:2]
        
        # 准备输入
        input_blob = cv2.dnn.blobFromImage(
            image, 1.0 / 255, (368, 368), (0, 0, 0), swapRB=False, crop=False
        )
        self.net.setInput(input_blob)
        
        # 前向传播
        output = self.net.forward()
        
        # 解析输出
        H = output.shape[2]
        W = output.shape[3]
        
        # 存储检测到的关键点
        points = []
        pose_data = {}
        
        # 创建结果图像副本
        result_image = image.copy()
        
        # 处理每个关键点
        for i in range(len(self.BODY_PARTS)):
            # 提取当前关键点的热图
            prob_map = output[0, i, :, :]
            
            # 找到最大概率位置
            _, prob, _, point = cv2.minMaxLoc(prob_map)
            
            # 换算回原图坐标
            x = (width * point[0]) / W
            y = (height * point[1]) / H
            
            # 如果概率大于阈值，认为检测到关键点
            if prob > self.config["confidence_threshold"]:
                # 添加到列表
                points.append((int(x), int(y)))
                # 在图像上标记关键点
                cv2.circle(result_image, (int(x), int(y)), 8, (0, 255, 255), thickness=-1, lineType=cv2.FILLED)
                cv2.putText(result_image, f"{i}", (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, lineType=cv2.LINE_AA)
                
                # 记录关键点数据
                for name, idx in self.BODY_PARTS.items():
                    if idx == i:
                        pose_data[name] = {"x": int(x), "y": int(y), "confidence": float(prob)}
                        break
            else:
                points.append(None)
        
        # 绘制骨架连接线
        for pair in self.POSE_PAIRS:
            part_a = self.BODY_PARTS[pair[0]]
            part_b = self.BODY_PARTS[pair[1]]
            
            if points[part_a] and points[part_b]:
                cv2.line(result_image, points[part_a], points[part_b], (0, 255, 0), 3)
        
        return result_image, pose_data
    
    def _simulate_pose_detection(self, image):
        """模拟姿态估计"""
        # 检测人脸作为参考点
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        # 创建结果图像副本
        result_image = image.copy()
        
        # 姿态数据
        pose_data = {}
        
        # 如果检测到人脸，根据人脸位置模拟人体姿态
        if len(faces) > 0:
            for (x, y, w, h) in faces:
                # 绘制人脸框
                cv2.rectangle(result_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # 根据人脸位置估计身体其他部位
                face_center_x = x + w // 2
                face_center_y = y + h // 2
                
                # 模拟头部关键点
                nose = (face_center_x, face_center_y)
                left_eye = (face_center_x - w//4, face_center_y - h//8)
                right_eye = (face_center_x + w//4, face_center_y - h//8)
                left_ear = (face_center_x - w//2, face_center_y)
                right_ear = (face_center_x + w//2, face_center_y)
                
                # 模拟颈部和身体关键点
                neck_y = y + h + h//4
                neck = (face_center_x, neck_y)
                
                # 肩膀
                shoulder_width = w * 2
                left_shoulder = (face_center_x - shoulder_width//2, neck_y + h//2)
                right_shoulder = (face_center_x + shoulder_width//2, neck_y + h//2)
                
                # 手肘
                elbow_y = neck_y + h*2
                left_elbow = (left_shoulder[0] - w//2, elbow_y)
                right_elbow = (right_shoulder[0] + w//2, elbow_y)
                
                # 手腕
                wrist_y = elbow_y + h
                left_wrist = (left_elbow[0], wrist_y)
                right_wrist = (right_elbow[0], wrist_y)
                
                # 臀部
                hip_y = neck_y + h*3
                left_hip = (face_center_x - w, hip_y)
                right_hip = (face_center_x + w, hip_y)
                
                # 膝盖
                knee_y = hip_y + h*3
                left_knee = (left_hip[0], knee_y)
                right_knee = (right_hip[0], knee_y)
                
                # 脚踝
                ankle_y = knee_y + h*3
                left_ankle = (left_knee[0], ankle_y)
                right_ankle = (right_knee[0], ankle_y)
                
                # 存储所有关键点
                keypoints = {
                    "Nose": nose,
                    "LEye": left_eye,
                    "REye": right_eye,
                    "LEar": left_ear,
                    "REar": right_ear,
                    "Neck": neck,
                    "LShoulder": left_shoulder,
                    "RShoulder": right_shoulder,
                    "LElbow": left_elbow,
                    "RElbow": right_elbow,
                    "LWrist": left_wrist,
                    "RWrist": right_wrist,
                    "LHip": left_hip,
                    "RHip": right_hip,
                    "LKnee": left_knee,
                    "RKnee": right_knee,
                    "LAnkle": left_ankle,
                    "RAnkle": right_ankle
                }
                
                # 绘制关键点和连接线
                for name, point in keypoints.items():
                    cv2.circle(result_image, point, 5, (0, 255, 255), thickness=-1)
                    
                    # 记录关键点数据
                    pose_data[name] = {"x": point[0], "y": point[1], "confidence": 0.9}
                
                # 绘制连接线
                connections = [
                    ("Nose", "Neck"), ("Neck", "LShoulder"), ("Neck", "RShoulder"),
                    ("LShoulder", "LElbow"), ("LElbow", "LWrist"),
                    ("RShoulder", "RElbow"), ("RElbow", "RWrist"),
                    ("Neck", "LHip"), ("Neck", "RHip"),
                    ("LHip", "LKnee"), ("LKnee", "LAnkle"),
                    ("RHip", "RKnee"), ("RKnee", "RAnkle"),
                    ("Nose", "LEye"), ("LEye", "LEar"),
                    ("Nose", "REye"), ("REye", "REar")
                ]
                
                for conn in connections:
                    cv2.line(result_image, keypoints[conn[0]], keypoints[conn[1]], (0, 255, 0), 2)
                
                # 只处理第一个检测到的人脸
                break
        else:
            # 如果没有检测到人脸，添加提示文字
            height, width = image.shape[:2]
            cv2.putText(
                result_image, 
                "未检测到人体", 
                (width//4, height//2), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1, 
                (0, 0, 255), 
                2
            )
        
        return result_image, pose_data
    
    def _generate_pose_summary(self, pose_data):
        """生成姿态摘要信息"""
        if not pose_data:
            return "未检测到人体姿态"
        
        # 检测到的关键点数量
        num_keypoints = len(pose_data)
        
        # 简单姿态分析
        if "Nose" in pose_data and "Neck" in pose_data:
            nose = pose_data["Nose"]
            neck = pose_data["Neck"]
            
            # 头部倾斜判断
            head_tilt = "直立"
            if abs(nose["x"] - neck["x"]) > 20:
                head_tilt = "向左倾斜" if nose["x"] < neck["x"] else "向右倾斜"
        else:
            head_tilt = "无法判断"
        
        # 手臂姿态
        arms_state = "无法判断"
        if ("LShoulder" in pose_data and "LElbow" in pose_data and 
            "RShoulder" in pose_data and "RElbow" in pose_data):
            # 根据肘部位置判断
            l_elbow_y = pose_data["LElbow"]["y"]
            r_elbow_y = pose_data["RElbow"]["y"]
            l_shoulder_y = pose_data["LShoulder"]["y"]
            r_shoulder_y = pose_data["RShoulder"]["y"]
            
            if l_elbow_y < l_shoulder_y and r_elbow_y < r_shoulder_y:
                arms_state = "双臂上举"
            elif l_elbow_y > l_shoulder_y and r_elbow_y > r_shoulder_y:
                arms_state = "双臂下垂"
            else:
                arms_state = "一只手臂上举，一只手臂下垂"
        
        # 生成摘要
        summary = f"检测到{num_keypoints}个人体关键点。人物头部{head_tilt}，手臂姿态为{arms_state}。"
        
        return summary
    
    def get_required_parameters(self):
        """获取插件需要的参数列表"""
        return ["image"]
    
    def get_task_types(self):
        """获取插件支持的任务类型列表"""
        return ["pose_estimation"]
