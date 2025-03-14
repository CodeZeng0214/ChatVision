import os
import cv2
import numpy as np  # 修复导入语句
import tempfile
import logging
from plugins.base_plugin import BasePlugin

class YoloPlugin(BasePlugin):
    """YOLO目标检测插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "YOLO目标检测"
        self.description = "使用YOLO模型检测图像中的物体"
        self.config = {
            "model_path": "",  # 模型路径，默认使用OpenCV DNN的YOLO
            "confidence_threshold": 0.5,
            "nms_threshold": 0.4,
            "result_dir": os.path.join(tempfile.gettempdir(), "chatvision_results")
        }
        
        # 创建结果目录
        os.makedirs(self.config["result_dir"], exist_ok=True)
        
        # 加载COCO类别
        self.classes = self._load_coco_classes()
        
        # 尝试加载模型
        self._load_model()
    
    def _load_coco_classes(self):
        """加载COCO类别名称"""
        classes = []
        try:
            # 常用的COCO类别名称
            classes = [
                "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", 
                "truck", "boat", "traffic light", "fire hydrant", "stop sign", 
                "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", 
                "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", 
                "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", 
                "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", 
                "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork", 
                "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", 
                "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", 
                "couch", "potted plant", "bed", "dining table", "toilet", "tv", 
                "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave", 
                "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", 
                "scissors", "teddy bear", "hair drier", "toothbrush"
            ]
        except Exception as e:
            logging.error(f"加载COCO类别失败: {e}")
        
        return classes
    
    def _load_model(self):
        """加载YOLO模型"""
        try:
            # 如果指定了模型路径，使用指定路径
            if self.config["model_path"] and os.path.exists(self.config["model_path"]):
                weights_path = self.config["model_path"]
                config_path = os.path.join(os.path.dirname(weights_path), "yolov3.cfg")
            else:
                # 否则尝试使用OpenCV内置模型
                try:
                    # 检查DNN数据目录是否存在
                    dnn_dir = os.path.join(cv2.data.haarcascades, "../dnn")
                    weights_path = os.path.join(dnn_dir, "yolov3.weights")
                    config_path = os.path.join(dnn_dir, "yolov3.cfg")
                    
                    # 如果文件不存在，提供下载信息
                    if not os.path.exists(weights_path) or not os.path.exists(config_path):
                        logging.warning("YOLO模型文件不存在。请从以下地址下载模型文件:")
                        logging.warning("1. 下载 yolov3.weights: https://pjreddie.com/media/files/yolov3.weights")
                        logging.warning("2. 下载 yolov3.cfg: https://github.com/pjreddie/darknet/blob/master/cfg/yolov3.cfg")
                        logging.warning(f"3. 将文件保存到 {os.path.dirname(weights_path)}")
                        
                        # 使用模拟模式
                        logging.info("YOLO插件将使用模拟检测模式")
                        self.net = None
                        self.simulation_mode = True
                        return
                except AttributeError:
                    logging.warning("无法访问OpenCV DNN数据目录，将使用模拟模式")
                    self.net = None
                    self.simulation_mode = True
                    return
            
            # 尝试加载模型
            if os.path.exists(weights_path) and os.path.exists(config_path):
                logging.info(f"加载YOLO模型: {weights_path}")
                self.net = cv2.dnn.readNetFromDarknet(config_path, weights_path)
                
                # 设置计算后端
                self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
                
                # 获取输出层名称
                layer_names = self.net.getLayerNames()
                try:
                    # OpenCV 4.x+
                    self.output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]
                except IndexError:
                    # 可能是较旧版本的OpenCV
                    self.output_layers = [layer_names[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]
                
                self.simulation_mode = False
                logging.info("YOLO模型加载成功")
            else:
                logging.warning(f"YOLO模型文件不存在: {weights_path}")
                self.net = None
                self.simulation_mode = True
            
        except Exception as e:
            logging.error(f"加载YOLO模型失败: {e}")
            self.net = None
            self.simulation_mode = True
    
    def process(self, parameters):
        """处理图像识别任务"""
        # 检查模型是否加载成功
        if self.net is None and not hasattr(self, 'simulation_mode'):
            return "模型未加载，无法进行识别"
        
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
                
            # 如果是模拟模式，使用模拟检测
            if hasattr(self, 'simulation_mode') and self.simulation_mode:
                return self._simulate_detection(image, image_path)
            
            # 图像预处理
            height, width, _ = image.shape
            
            # 创建输入blob
            blob = cv2.dnn.blobFromImage(image, 1/255.0, (416, 416), swapRB=True, crop=False)
            self.net.setInput(blob)
            
            # 前向推理
            outputs = self.net.forward(self.output_layers)
            
            # 处理结果
            class_ids = []
            confidences = []
            boxes = []
            
            for output in outputs:
                for detection in output:
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]
                    
                    if confidence > self.config["confidence_threshold"]:
                        center_x = int(detection[0] * width)
                        center_y = int(detection[1] * height)
                        w = int(detection[2] * width)
                        h = int(detection[3] * height)
                        
                        # 计算左上角坐标
                        x = int(center_x - w / 2)
                        y = int(center_y - h / 2)
                        
                        boxes.append([x, y, w, h])
                        confidences.append(float(confidence))
                        class_ids.append(class_id)
            
            # 非极大值抑制，去除重叠框
            indices = cv2.dnn.NMSBoxes(boxes, confidences, self.config["confidence_threshold"], 
                                       self.config["nms_threshold"])
            
            # 在图像上绘制结果
            result_image = image.copy()
            detection_results = []
            
            if len(indices) > 0:
                for i in indices:
                    if isinstance(i, (list, tuple)):  # OpenCV 3.x返回二维数组
                        i = i[0]
                        
                    box = boxes[i]
                    x, y, w, h = box
                    label = self.classes[class_ids[i]] if class_ids[i] < len(self.classes) else f"未知类别{class_ids[i]}"
                    confidence = confidences[i]
                    
                    # 保存识别结果
                    detection_results.append({
                        "label": label,
                        "confidence": confidence,
                        "box": [x, y, w, h]
                    })
                    
                    # 绘制框
                    cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
                    # 绘制标签
                    text = f"{label}: {confidence:.2f}"
                    cv2.putText(result_image, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 
                                0.5, (0, 255, 0), 2)
            
            # 保存结果图像
            result_filename = os.path.basename(image_path)
            result_path = os.path.join(self.config["result_dir"], f"yolo_{result_filename}")
            cv2.imwrite(result_path, result_image)
            
            # 返回结果
            return {
                "original_image": image_path,
                "result_image": result_path,
                "detections": detection_results,
                "total_objects": len(indices),
                "summary": self._generate_summary(detection_results)
            }
            
        except Exception as e:
            logging.error(f"YOLO处理失败: {e}")
            return f"处理图像时发生错误: {str(e)}"
    
    def _simulate_detection(self, image, image_path):
        """模拟对象检测，当模型不可用时使用"""
        logging.info("使用模拟检测模式")
        
        # 创建结果图像副本
        result_image = image.copy()
        height, width, _ = image.shape
        
        # 模拟一些常见物体的检测结果
        detection_results = []
        
        # 使用简单的图像分析来确定可能的对象
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 使用边缘检测查找可能的物体
        edges = cv2.Canny(gray, 100, 200)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 只保留面积较大的轮廓
        significant_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # 忽略小物体
                significant_contours.append(contour)
        
        # 为每个重要轮廓创建模拟检测框
        common_objects = ["object", "item", "box", "shape"]
        
        # 限制最多检测5个物体
        max_detections = min(5, len(significant_contours))
        
        for i in range(max_detections):
            if i < len(significant_contours):
                contour = significant_contours[i]
                x, y, w, h = cv2.boundingRect(contour)
                
                # 确保框在图像内
                x = max(0, x)
                y = max(0, y)
                w = min(width - x, w)
                h = min(height - y, h)
                
                # 模拟标签和置信度
                import random
                label = common_objects[i % len(common_objects)]
                confidence = random.uniform(0.7, 0.95)
                
                # 添加到检测结果
                detection_results.append({
                    "label": label,
                    "confidence": confidence,
                    "box": [x, y, w, h]
                })
                
                # 绘制框和标签
                cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                text = f"{label}: {confidence:.2f}"
                cv2.putText(result_image, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 
                            0.5, (0, 255, 0), 2)
        
        # 保存结果图像
        result_filename = os.path.basename(image_path)
        result_path = os.path.join(self.config["result_dir"], f"yolo_{result_filename}")
        cv2.imwrite(result_path, result_image)
        
        # 返回结果
        return {
            "original_image": image_path,
            "result_image": result_path,
            "detections": detection_results,
            "total_objects": len(detection_results),
            "summary": self._generate_summary(detection_results) + " (模拟检测模式)"
        }
    
    def _generate_summary(self, detections):
        """生成检测结果摘要"""
        if not detections:
            return "未检测到任何物体"
            
        # 统计各类别物体数量
        label_counts = {}
        for det in detections:
            label = det["label"]
            if label in label_counts:
                label_counts[label] += 1
            else:
                label_counts[label] = 1
                
        # 生成摘要文本
        summary_parts = []
        for label, count in label_counts.items():
            summary_parts.append(f"{count}个{label}")
            
        return f"共检测到{len(detections)}个物体: " + ", ".join(summary_parts)
    
    def get_required_parameters(self):
        """获取插件需要的参数列表"""
        return ["image"]
    
    def get_task_types(self):
        """获取插件支持的任务类型列表"""
        return ["image_recognition"]
