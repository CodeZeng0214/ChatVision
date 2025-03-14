from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QComboBox, QTabWidget, QScrollArea)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QPixmap, QImage, QIcon
import cv2
import numpy as np
import os
from utils.i18n import _

class VideoPlayer(QWidget):
    """视频播放组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_path = None
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.is_playing = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 视频显示区域
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: #000000;")
        layout.addWidget(self.video_label)
        
        # 控制按钮
        controls = QHBoxLayout()
        
        self.play_btn = QPushButton(_("sidebar.play"))
        self.play_btn.clicked.connect(self.toggle_play)
        
        self.stop_btn = QPushButton(_("sidebar.stop"))
        self.stop_btn.clicked.connect(self.stop)
        
        controls.addWidget(self.play_btn)
        controls.addWidget(self.stop_btn)
        controls.addStretch()
        
        layout.addLayout(controls)
    
    def set_video(self, video_path):
        """设置视频源"""
        self.stop()
        self.video_path = video_path
        if os.path.exists(video_path):
            self.cap = cv2.VideoCapture(video_path)
            success, frame = self.cap.read()
            if success:
                self.display_frame(frame)
    
    def toggle_play(self):
        """切换播放状态"""
        if self.is_playing:
            self.timer.stop()
            self.play_btn.setText(_("sidebar.play"))
        else:
            if self.cap is None and self.video_path:
                self.cap = cv2.VideoCapture(self.video_path)
            
            if self.cap and self.cap.isOpened():
                self.timer.start(33)  # ~30 FPS
                self.play_btn.setText(_("sidebar.pause"))
        
        self.is_playing = not self.is_playing
    
    def stop(self):
        """停止播放"""
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None
        self.is_playing = False
        self.play_btn.setText(_("sidebar.play"))
        self.video_label.clear()
    
    def update_frame(self):
        """更新视频帧"""
        if self.cap and self.cap.isOpened():
            success, frame = self.cap.read()
            if success:
                self.display_frame(frame)
            else:
                # 视频结束
                self.timer.stop()
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 重置到开始
                self.is_playing = False
                self.play_btn.setText(_("sidebar.play"))
    
    def display_frame(self, frame):
        """显示视频帧"""
        # 转换为RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 调整尺寸以适应标签
        h, w, ch = rgb_frame.shape
        label_size = self.video_label.size()
        scale_w = label_size.width() / w
        scale_h = label_size.height() / h
        scale = min(scale_w, scale_h)
        
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        resized_frame = cv2.resize(rgb_frame, (new_w, new_h))
        
        # 转为QImage并显示
        bytes_per_line = ch * new_w
        image = QImage(resized_frame.data, new_w, new_h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)
        self.video_label.setPixmap(pixmap)


class CameraFeed(QWidget):
    """摄像头实时流组件"""
    
    # 定义信号
    frame_processed = Signal(object, str)  # 帧处理信号，传递处理后的帧和处理类型
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.camera_id = 0
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.is_active = False
        self.processing_function = None
        self.processing_type = "none"
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 摄像头选择
        camera_layout = QHBoxLayout()
        camera_layout.addWidget(QLabel(_("sidebar.camera")))
        
        self.camera_combo = QComboBox()
        self.camera_combo.addItems(["0 - " + _("sidebar.default_camera"), "1 - " + _("sidebar.external_camera")])
        self.camera_combo.currentIndexChanged.connect(self.change_camera)
        camera_layout.addWidget(self.camera_combo)
        
        layout.addLayout(camera_layout)
        
        # 摄像头显示区域
        self.feed_label = QLabel()
        self.feed_label.setAlignment(Qt.AlignCenter)
        self.feed_label.setStyleSheet("background-color: #000000;")
        self.feed_label.setMinimumSize(400, 300)
        layout.addWidget(self.feed_label)
        
        # 控制按钮
        controls = QHBoxLayout()
        
        self.start_btn = QPushButton(_("sidebar.play"))
        self.start_btn.clicked.connect(self.toggle_feed)
        
        self.process_combo = QComboBox()
        self.process_combo.addItems([
            _("sidebar.no_processing"), 
            _("sidebar.edge_detection"), 
            _("sidebar.grayscale"), 
            _("sidebar.face_detection")
        ])
        self.process_combo.currentIndexChanged.connect(self.set_processing)
        
        controls.addWidget(self.start_btn)
        controls.addWidget(QLabel(_("sidebar.processing") + ":"))
        controls.addWidget(self.process_combo)
        controls.addStretch()
        
        layout.addLayout(controls)
    
    def change_camera(self, index):
        """切换摄像头"""
        was_active = self.is_active
        self.stop_feed()
        self.camera_id = index
        if was_active:
            self.start_feed()
    
    def set_processing(self, index):
        """设置处理函数"""
        if index == 0:  # 无处理
            self.processing_function = None
            self.processing_type = "none"
        elif index == 1:  # 边缘检测
            self.processing_function = self._edge_detection
            self.processing_type = "edge_detection"
        elif index == 2:  # 灰度
            self.processing_function = self._grayscale
            self.processing_type = "grayscale"
        elif index == 3:  # 人脸检测
            self.processing_function = self._face_detection
            self.processing_type = "face_detection"
            # 加载人脸检测级联分类器
            try:
                self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            except Exception as e:
                print(f"加载人脸检测器失败: {e}")
                self.processing_function = None
                self.processing_type = "none"
                self.process_combo.setCurrentIndex(0)
    
    def toggle_feed(self):
        """切换摄像头状态"""
        if self.is_active:
            self.stop_feed()
        else:
            self.start_feed()
    
    def start_feed(self):
        """启动摄像头"""
        self.cap = cv2.VideoCapture(self.camera_id)
        if self.cap.isOpened():
            self.timer.start(33)  # ~30 FPS
            self.is_active = True
            self.start_btn.setText(_("sidebar.stop"))
    
    def stop_feed(self):
        """停止摄像头"""
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None
        self.is_active = False
        self.start_btn.setText(_("sidebar.play"))
        self.feed_label.clear()
    
    def update_frame(self):
        """更新摄像头帧"""
        if self.cap and self.cap.isOpened():
            success, frame = self.cap.read()
            if success:
                # 应用处理函数
                if self.processing_function:
                    processed_frame = self.processing_function(frame)
                    self.display_frame(processed_frame)
                    # 发出信号
                    self.frame_processed.emit(processed_frame, self.processing_type)
                else:
                    self.display_frame(frame)
                    # 发出信号
                    self.frame_processed.emit(frame, "none")
    
    def display_frame(self, frame):
        """显示摄像头帧"""
        # 转换为RGB
        if len(frame.shape) == 2:  # 灰度图像
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
        else:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 调整尺寸以适应标签
        h, w = rgb_frame.shape[:2]
        label_size = self.feed_label.size()
        scale_w = label_size.width() / w
        scale_h = label_size.height() / h
        scale = min(scale_w, scale_h)
        
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        resized_frame = cv2.resize(rgb_frame, (new_w, new_h))
        
        # 转为QImage并显示
        if len(resized_frame.shape) == 2:  # 灰度图像
            image = QImage(resized_frame.data, new_w, new_h, new_w, QImage.Format_Grayscale8)
        else:
            ch = resized_frame.shape[2]
            bytes_per_line = ch * new_w
            image = QImage(resized_frame.data, new_w, new_h, bytes_per_line, QImage.Format_RGB888)
            
        pixmap = QPixmap.fromImage(image)
        self.feed_label.setPixmap(pixmap)
    
    def _edge_detection(self, frame):
        """边缘检测处理"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)
        
        # 转回三通道以便显示
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    
    def _grayscale(self, frame):
        """灰度处理"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    
    def _face_detection(self, frame):
        """人脸检测"""
        if not hasattr(self, 'face_cascade'):
            return frame
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(30, 30)
        )
        
        # 绘制人脸框
        result_frame = frame.copy()
        for (x, y, w, h) in faces:
            cv2.rectangle(result_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
        return result_frame


class ImageComparison(QWidget):
    """图像对比组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_image = None
        self.processed_image = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 图像标题
        titles_layout = QHBoxLayout()
        titles_layout.addWidget(QLabel(_("sidebar.original_image")))
        titles_layout.addWidget(QLabel(_("sidebar.processed_image")))
        layout.addLayout(titles_layout)
        
        # 图像显示区域
        images_layout = QHBoxLayout()
        
        self.original_label = QLabel()
        self.original_label.setAlignment(Qt.AlignCenter)
        self.original_label.setStyleSheet("background-color: #f0f0f0;")
        self.original_label.setMinimumSize(300, 200)
        
        self.processed_label = QLabel()
        self.processed_label.setAlignment(Qt.AlignCenter)
        self.processed_label.setStyleSheet("background-color: #f0f0f0;")
        self.processed_label.setMinimumSize(300, 200)
        
        images_layout.addWidget(self.original_label)
        images_layout.addWidget(self.processed_label)
        
        layout.addLayout(images_layout)
    
    def set_images(self, original_path, processed_path):
        """设置对比图像"""
        if original_path and os.path.exists(original_path):
            original_pixmap = QPixmap(original_path)
            self.original_label.setPixmap(original_pixmap.scaled(
                self.original_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
            self.original_image = original_path
        
        if processed_path and os.path.exists(processed_path):
            processed_pixmap = QPixmap(processed_path)
            self.processed_label.setPixmap(processed_pixmap.scaled(
                self.processed_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
            self.processed_image = processed_path
    
    def set_cv_images(self, original_image, processed_image):
        """设置OpenCV图像对象"""
        # 显示原始图像
        if original_image is not None:
            if len(original_image.shape) == 2:  # 灰度图像
                rgb_image = cv2.cvtColor(original_image, cv2.COLOR_GRAY2RGB)
            else:
                rgb_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
            
            h, w = rgb_image.shape[:2]
            qimg = QImage(rgb_image.data, w, h, w * 3, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            self.original_label.setPixmap(pixmap.scaled(
                self.original_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        
        # 显示处理后图像
        if processed_image is not None:
            if len(processed_image.shape) == 2:  # 灰度图像
                rgb_image = cv2.cvtColor(processed_image, cv2.COLOR_GRAY2RGB)
            else:
                rgb_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)
            
            h, w = rgb_image.shape[:2]
            qimg = QImage(rgb_image.data, w, h, w * 3, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            self.processed_label.setPixmap(pixmap.scaled(
                self.processed_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
    
    def clear(self):
        """清除图像"""
        self.original_label.clear()
        self.processed_label.clear()
        self.original_image = None
        self.processed_image = None


class SidebarWidget(QWidget):
    """侧边栏组件，用于显示图像、视频和摄像头处理结果"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建标签页
        self.tabs = QTabWidget()
        
        # 图像对比页
        self.image_comparison = ImageComparison()
        self.tabs.addTab(self.image_comparison, _("sidebar.image_comparison"))
        
        # 视频播放页
        self.video_player = VideoPlayer()
        self.tabs.addTab(self.video_player, _("sidebar.video_player"))
        
        # 摄像头页
        self.camera_feed = CameraFeed()
        self.camera_feed.frame_processed.connect(self.on_frame_processed)
        self.tabs.addTab(self.camera_feed, _("sidebar.camera_feed"))
        
        layout.addWidget(self.tabs)
        
        # 信息显示区域
        self.info_label = QLabel(_("sidebar.ready"))
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("background-color: #e0e0e0; padding: 5px;")
        layout.addWidget(self.info_label)
    
    def on_frame_processed(self, frame, process_type):
        """处理摄像头帧处理信号"""
        # 更新信息标签
        if process_type != "none":
            self.info_label.setText(_("sidebar.processing") + f": {process_type}")
            
            # 保存原始帧以展示对比
            if not hasattr(self, 'last_original_frame'):
                self.last_original_frame = frame.copy()
            
            # 更新图像对比标签页
            self.image_comparison.set_cv_images(self.last_original_frame, frame)
    
    def show_image_comparison(self, original_path, processed_path=None):
        """显示图像对比"""
        self.tabs.setCurrentIndex(0)  # 切换到图像对比标签页
        self.image_comparison.set_images(original_path, processed_path)
        self.info_label.setText(_("sidebar.image_comparison") + f": {os.path.basename(original_path)}")
    
    def show_video(self, video_path):
        """显示视频"""
        self.tabs.setCurrentIndex(1)  # 切换到视频播放标签页
        self.video_player.set_video(video_path)
        self.info_label.setText(_("sidebar.video_player") + f": {os.path.basename(video_path)}")
    
    def show_camera(self, camera_id=0, process_type=None):
        """显示摄像头"""
        self.tabs.setCurrentIndex(2)  # 切换到摄像头标签页
        
        # 设置摄像头
        self.camera_feed.camera_combo.setCurrentIndex(camera_id)
        
        # 设置处理类型
        if process_type is not None:
            process_index = 0  # 默认无处理
            if process_type == "edge_detection":
                process_index = 1
            elif process_type == "grayscale":
                process_index = 2
            elif process_type == "face_detection":
                process_index = 3
            
            self.camera_feed.process_combo.setCurrentIndex(process_index)
        
        # 启动摄像头
        if not self.camera_feed.is_active:
            self.camera_feed.start_feed()
        
        self.info_label.setText(_("sidebar.camera_feed") + f" ID: {camera_id}")
    
    def refresh_ui(self):
        """刷新UI文本"""
        self.tabs.setTabText(0, _("sidebar.image_comparison"))
        self.tabs.setTabText(1, _("sidebar.video_player"))
        self.tabs.setTabText(2, _("sidebar.camera_feed"))
        
        if self.info_label.text() == "准备就绪":
            self.info_label.setText(_("sidebar.ready"))
            
        # 更新视频播放器按钮
        self.video_player.play_btn.setText(
            _("sidebar.pause") if self.video_player.is_playing else _("sidebar.play")
        )
        self.video_player.stop_btn.setText(_("sidebar.stop"))
        
        # 更新摄像头按钮
        self.camera_feed.start_btn.setText(
            _("sidebar.stop") if self.camera_feed.is_active else _("sidebar.play")
        )
    
    def clear(self):
        """清除所有内容"""
        self.image_comparison.clear()
        self.video_player.stop()
        self.camera_feed.stop_feed()
        self.info_label.setText(_("sidebar.ready"))
