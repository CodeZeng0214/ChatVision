import os
import cv2
import tempfile
import logging
import time
import threading
from plugins.base_plugin import BasePlugin

class RealtimeProcessingPlugin(BasePlugin):
    """实时视频处理插件，处理摄像头或视频流"""
    
    def __init__(self):
        super().__init__()
        self.name = "实时视频处理"
        self.description = "处理摄像头或视频流，可选择不同的处理效果"
        self.config = {
            "result_dir": os.path.join(tempfile.gettempdir(), "chatvision_results"),
            "default_camera": 0,
            "frame_width": 640,
            "frame_height": 480,
            "fps": 30,
            "recording_enabled": True
        }
        
        # 创建结果目录
        os.makedirs(self.config["result_dir"], exist_ok=True)
        
        # 实时处理相关变量
        self.cap = None
        self.is_running = False
        self.processing_thread = None
        self.frame_callback = None
        self.stop_event = threading.Event()
        
        # 预定义处理函数
        self.processing_functions = {
            "none": self._no_processing,
            "gray": self._grayscale,
            "edge": self._edge_detection,
            "face": self._face_detection,
            "blur": self._blur
        }
    
    def process(self, parameters):
        """处理实时任务"""
        # 获取参数
        camera_id = 0  # 默认摄像头ID
        task = "none"  # 默认不处理
        
        if "camera_id" in parameters:
            camera_id = int(parameters["camera_id"])
        if "task" in parameters:
            task = parameters["task"]
        
        # 确认处理函数存在
        if task not in self.processing_functions:
            return f"未知的处理任务: {task}"
        
        # 如果已经在运行，先关闭
        if self.is_running:
            self.stop()
        
        # 创建结果目录
        timestamp = int(time.time())
        result_dir = os.path.join(
            self.config["result_dir"],
            f"realtime_{task}_{timestamp}"
        )
        os.makedirs(result_dir, exist_ok=True)
        
        # 初始化视频录制器
        recording_path = None
        if self.config["recording_enabled"]:
            recording_path = os.path.join(result_dir, "recording.mp4")
            self.recorder = cv2.VideoWriter(
                recording_path,
                cv2.VideoWriter_fourcc(*'MP4V'),
                self.config["fps"],
                (self.config["frame_width"], self.config["frame_height"])
            )
        
        # 启动处理线程
        self.stop_event.clear()
        self.processing_thread = threading.Thread(
            target=self._processing_loop,
            args=(camera_id, task, result_dir)
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        return {
            "status": "started",
            "camera_id": camera_id,
            "task": task,
            "result_dir": result_dir,
            "recording": recording_path if recording_path else None,
            "message": f"已启动摄像头 {camera_id} 的实时处理，任务: {task}"
        }
    
    def _processing_loop(self, camera_id, task_name, result_dir):
        """处理线程主循环"""
        try:
            # 打开摄像头
            self.cap = cv2.VideoCapture(camera_id)
            if not self.cap.isOpened():
                logging.error(f"无法打开摄像头 {camera_id}")
                return
            
            # 设置分辨率
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config["frame_width"])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config["frame_height"])
            
            # 获取处理函数
            process_func = self.processing_functions[task_name]
            
            # 设置运行状态
            self.is_running = True
            
            # 帧计数
            frame_count = 0
            start_time = time.time()
            screenshot_interval = 5  # 每5秒保存一张截图
            last_screenshot = start_time
            
            # 主循环
            while not self.stop_event.is_set():
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                # 应用处理
                processed_frame = process_func(frame)
                
                # 调用回调函数
                if self.frame_callback:
                    self.frame_callback(processed_frame, task_name)
                
                # 录制视频
                if self.config["recording_enabled"] and hasattr(self, 'recorder'):
                    self.recorder.write(processed_frame)
                
                # 定期保存截图
                current_time = time.time()
                if current_time - last_screenshot >= screenshot_interval:
                    screenshot_path = os.path.join(
                        result_dir,
                        f"screenshot_{int(current_time)}.jpg"
                    )
                    cv2.imwrite(screenshot_path, processed_frame)
                    last_screenshot = current_time
                
                # 更新计数
                frame_count += 1
                
                # 控制帧率
                elapsed = time.time() - start_time
                target_elapsed = frame_count / self.config["fps"]
                if elapsed < target_elapsed:
                    time.sleep(target_elapsed - elapsed)
        
        except Exception as e:
            logging.error(f"实时处理错误: {e}")
        
        finally:
            # 清理资源
            self.is_running = False
            if self.cap:
                self.cap.release()
                self.cap = None
            
            if self.config["recording_enabled"] and hasattr(self, 'recorder'):
                self.recorder.release()
                del self.recorder
    
    def stop(self):
        """停止处理"""
        if not self.is_running:
            return
            
        self.stop_event.set()
        if self.processing_thread:
            self.processing_thread.join(timeout=2)
            self.processing_thread = None
        
        self.is_running = False
    
    def set_frame_callback(self, callback):
        """设置帧处理回调"""
        self.frame_callback = callback
    
    def _no_processing(self, frame):
        """无处理"""
        return frame
    
    def _grayscale(self, frame):
        """灰度处理"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    
    def _edge_detection(self, frame):
        """边缘检测"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    
    def _face_detection(self, frame):
        """人脸检测"""
        try:
            # 使用OpenCV内置的人脸检测模型
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            result = frame.copy()
            for (x, y, w, h) in faces:
                cv2.rectangle(result, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            return result
        except Exception as e:
            logging.error(f"人脸检测失败: {e}")
            return frame
    
    def _blur(self, frame):
        """模糊处理"""
        return cv2.GaussianBlur(frame, (15, 15), 0)
    
    def get_required_parameters(self):
        """获取插件需要的参数列表"""
        return ["camera_id", "task"]
    
    def get_task_types(self):
        """获取插件支持的任务类型列表"""
        return ["realtime_processing"]
