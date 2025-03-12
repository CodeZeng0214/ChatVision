from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                              QLabel, QPushButton)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QPixmap, QIcon
import os

class MessageWidget(QWidget):
    """用于显示单条聊天消息的自定义小部件
    
    创建气泡形状的消息框，支持显示文本内容和媒体内容（图片或视频）。
    根据是否为用户消息，显示在界面的左侧或右侧，并使用不同的样式。
    用户消息使用绿色背景，AI消息使用白色背景。
    """
    video_play_requested = Signal(str)  # 请求播放视频时发出的信号，参数为视频路径
    
    def __init__(self, username, message, media_path=None, media_type=None, is_user=False, parent=None):
        """初始化消息小部件
        
        参数:
            username (str): 发送消息的用户名
            message (str): 消息文本内容
            media_path (str): 媒体文件的路径，可以是None
            media_type (str): 媒体类型，可以是"image"或"video"
            is_user (bool): 是否为用户发送的消息，影响消息显示位置和样式
            parent (QWidget): 父级小部件
        """
        super().__init__(parent)
        self.is_user = is_user
        self.media_path = media_path
        self.media_type = media_type
        self.setup_ui(username, message, media_path, media_type)
        
    def setup_ui(self, username, message, media_path, media_type):
        """设置消息小部件的UI组件和布局
        
        创建气泡形状的消息，包含用户名、文本内容和可能的媒体内容。
        根据消息发送者确定消息在左侧还是右侧显示，并应用不同的样式。
        根据媒体类型(图像/视频)显示不同的内容组件。
        
        参数:
            username (str): 发送消息的用户名
            message (str): 消息文本内容
            media_path (str): 媒体文件的路径
            media_type (str): 媒体类型
        """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 用户名标签
        username_label = QLabel(username)
        username_label.setStyleSheet("font-weight: bold;")
        
        # 消息内容
        message_widget = QWidget()
        message_layout = QVBoxLayout(message_widget)
        message_layout.setContentsMargins(10, 10, 10, 10)
        
        # 添加文本内容（如果有）
        if message:
            text_label = QLabel(message)
            text_label.setWordWrap(True)  # 允许文本自动换行
            message_layout.addWidget(text_label)
        
        # 添加媒体内容（如果有）
        if media_path:
            if media_type == "image":
                try:
                    if not os.path.exists(media_path):
                        raise FileNotFoundError(f"找不到图像文件: {media_path}")
                        
                    image_label = QLabel()
                    pixmap = QPixmap(media_path)
                    if pixmap.isNull():
                        raise ValueError("无法加载图像")
                        
                    # 如果图像太大则调整大小，限制宽度最大为250像素
                    if pixmap.width() > 250:
                        pixmap = pixmap.scaledToWidth(250, Qt.SmoothTransformation)
                    image_label.setPixmap(pixmap)
                    image_label.setCursor(Qt.PointingHandCursor)  # 鼠标悬停时显示手型光标
                    image_label.mousePressEvent = lambda e: self.enlarge_image()  # 点击图像时放大显示
                    message_layout.addWidget(image_label)
                except Exception as e:
                    error_label = QLabel(f"加载图像时出错: {str(e)}")
                    error_label.setStyleSheet("color: red;")
                    message_layout.addWidget(error_label)
                
            elif media_type == "video":
                # 对于视频，显示带有播放按钮的缩略图
                thumbnail_widget = QWidget()
                thumbnail_layout = QVBoxLayout(thumbnail_widget)
                
                # 添加视频图标或缩略图
                video_label = QLabel("视频")
                video_label.setAlignment(Qt.AlignCenter)
                video_label.setStyleSheet("""
                    background-color: #000; 
                    color: white; 
                    border-radius: 5px; 
                    padding: 30px;
                """)
                video_label.setFixedSize(200, 120)
                thumbnail_layout.addWidget(video_label)
                
                # 显示视频文件名
                if media_path:
                    file_name = os.path.basename(media_path) if os.path.exists(media_path) else media_path
                    file_label = QLabel(file_name)
                    file_label.setAlignment(Qt.AlignCenter)
                    file_label.setWordWrap(True)
                    thumbnail_layout.addWidget(file_label)
                
                # 添加播放按钮
                video_btn = QPushButton("播放视频")
                video_btn.setIcon(QIcon.fromTheme("media-playback-start"))
                video_btn.clicked.connect(self.play_video)
                
                thumbnail_layout.addWidget(video_btn)
                message_layout.addWidget(thumbnail_widget)
        
        # 为消息气泡设置样式
        if self.is_user:
            message_widget.setStyleSheet("background-color: #95EC69; border-radius: 10px;")  # 用户消息使用绿色背景
        else:
            message_widget.setStyleSheet("background-color: #FFFFFF; border-radius: 10px;")  # AI消息使用白色背景
        
        # 根据消息发送者设置布局对齐方式
        h_layout = QHBoxLayout()
        if self.is_user:
            # 用户消息靠右对齐
            h_layout.addStretch()
            main_layout.addWidget(username_label, 0, Qt.AlignRight)
            h_layout.addWidget(message_widget)
        else:
            # AI消息靠左对齐
            main_layout.addWidget(username_label, 0, Qt.AlignLeft)
            h_layout.addWidget(message_widget)
            h_layout.addStretch()
        
        main_layout.addLayout(h_layout)
    
    def play_video(self):
        """在侧边栏中播放视频
        
        当用户点击播放按钮时，发出信号请求在侧边栏播放视频。
        检查视频文件是否存在并处理可能的错误。
        """
        if self.media_path and self.media_type == "video":
            if os.path.exists(self.media_path):
                self.video_play_requested.emit(self.media_path)
            else:
                print(f"找不到视频文件: {self.media_path}")
    
    def enlarge_image(self):
        """在侧边栏中放大显示图像
        
        当用户点击图像时，发出信号请求在侧边栏中显示放大的图像。
        使用与视频相同的信号进行处理。
        检查图像文件是否存在并处理可能的错误。
        """
        if self.media_path and self.media_type == "image":
            if os.path.exists(self.media_path):
                # 使用与视频相同的信号来处理图像显示请求
                self.video_play_requested.emit(self.media_path)
            else:
                print(f"找不到图像文件: {self.media_path}")
