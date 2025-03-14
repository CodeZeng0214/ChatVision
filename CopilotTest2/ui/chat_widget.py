import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QTextEdit, QListWidget, QListWidgetItem, QLabel, 
                              QSplitter, QFileDialog, QProgressBar, QDialog)
from PySide6.QtCore import Qt, QSize, Signal, Slot
from PySide6.QtGui import QPixmap, QIcon
from ui.sidebar_widget import SidebarWidget
from ui.param_dialog import ParamDialog  # 导入参数对话框类
import tempfile
from utils.i18n import _

class MessageItem(QWidget):
    """消息项组件"""
    
    def __init__(self, message, is_user=True):
        super().__init__()
        self.message = message
        self.is_user = is_user
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        
        # 根据消息发送者调整布局
        if self.is_user:
            layout.addStretch()
            
        # 创建消息内容区域
        msg_widget = QWidget()
        msg_layout = QVBoxLayout(msg_widget)
        
        # 发送者名称
        sender_name = "我" if self.is_user else "ChatVision"
        name_label = QLabel(sender_name)
        name_label.setStyleSheet("font-weight: bold;")
        
        # 根据发送者对齐方式
        if self.is_user:
            name_label.setAlignment(Qt.AlignRight)
            msg_layout.setAlignment(Qt.AlignRight)
        
        msg_layout.addWidget(name_label)
        
        # 消息内容
        content = QLabel(self.message.content)
        content.setWordWrap(True)
        content.setStyleSheet(
            "background-color: #95ec69;" if self.is_user else "background-color: #ffffff;" +
            "border-radius: 10px; padding: 10px;"
        )
        content.setMinimumWidth(100)
        content.setMaximumWidth(400)
        msg_layout.addWidget(content)
        
        # 如果有媒体文件，添加显示
        if self.message.media_files:
            for file_path in self.message.media_files:
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    # 图片文件
                    img_label = QLabel()
                    pixmap = QPixmap(file_path)
                    scaled_pixmap = pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    img_label.setPixmap(scaled_pixmap)
                    img_label.setStyleSheet("background-color: transparent;")
                    msg_layout.addWidget(img_label)
                elif file_path.lower().endswith(('.mp4', '.avi', '.mov', '.wmv')):
                    # 视频文件 - 显示为缩略图
                    video_btn = QPushButton("点击播放视频")
                    video_btn.setStyleSheet("background-color: #d0d0d0;")
                    video_btn.setProperty("video_path", file_path)
                    video_btn.clicked.connect(self.play_video)
                    msg_layout.addWidget(video_btn)
        
        # 如果有处理结果，显示结果
        if hasattr(self.message, 'processed_results') and self.message.processed_results:
            result_label = QLabel("处理结果:")
            result_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
            msg_layout.addWidget(result_label)
            
            # 根据结果类型显示
            if isinstance(self.message.processed_results, str):
                # 字符串结果
                result_content = QLabel(self.message.processed_results)
                result_content.setWordWrap(True)
                result_content.setStyleSheet("background-color: #f0f0f0; border-radius: 5px; padding: 5px;")
                msg_layout.addWidget(result_content)
            elif isinstance(self.message.processed_results, dict) and "result_image" in self.message.processed_results:
                # 图像结果
                img_path = self.message.processed_results["result_image"]
                result_img = QLabel()
                pixmap = QPixmap(img_path)
                scaled_pixmap = pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                result_img.setPixmap(scaled_pixmap)
                msg_layout.addWidget(result_img)
        
        layout.addWidget(msg_widget)
        
        if not self.is_user:
            layout.addStretch()
        
        # 移除布局边距
        layout.setContentsMargins(0, 5, 0, 5)
    
    def play_video(self):
        """播放视频"""
        sender = self.sender()
        video_path = sender.property("video_path")
        # 导入媒体播放相关模块
        try:
            from PySide6.QtMultimedia import QMediaPlayer
            from PySide6.QtMultimediaWidgets import QVideoWidget
            
            # 创建视频播放对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("视频播放")
            dialog.resize(640, 480)
            
            layout = QVBoxLayout(dialog)
            
            # 创建视频播放组件
            video_widget = QVideoWidget()
            player = QMediaPlayer()
            player.setVideoOutput(video_widget)
            player.setSource(video_path)
            
            layout.addWidget(video_widget)
            
            # 播放控制按钮
            controls = QHBoxLayout()
            play_btn = QPushButton("播放")
            pause_btn = QPushButton("暂停")
            stop_btn = QPushButton("停止")
            
            play_btn.clicked.connect(player.play)
            pause_btn.clicked.connect(player.pause)
            stop_btn.clicked.connect(player.stop)
            
            controls.addWidget(play_btn)
            controls.addWidget(pause_btn)
            controls.addWidget(stop_btn)
            
            layout.addLayout(controls)
            
            # 显示对话框并开始播放
            dialog.show()
            player.play()
            
        except ImportError:
            # 如果没有媒体播放模块，显示错误信息
            error_dialog = QDialog(self)
            error_dialog.setWindowTitle("错误")
            error_layout = QVBoxLayout(error_dialog)
            error_label = QLabel("无法播放视频，缺少媒体播放组件。")
            error_layout.addWidget(error_label)
            error_dialog.setLayout(error_layout)
            error_dialog.exec()


class ChatWidget(QWidget):
    """聊天界面组件"""
    
    def __init__(self, chat_engine):
        super().__init__()
        self.chat_engine = chat_engine
        self.media_files = []
        self.sidebar_visible = False
        self.sidebar = None
        
        # 设置回调
        self.chat_engine.on_new_message = self.on_new_message
        self.chat_engine.on_processing = self.on_processing
        self.chat_engine.on_require_params = self.on_require_params
        self.chat_engine.on_show_sidebar = self.on_show_sidebar
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置聊天界面"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建分隔器，用于聊天区域和侧边栏
        self.splitter = QSplitter(Qt.Horizontal)
        
        # 创建左侧聊天区域
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        
        # 聊天记录区域
        self.chat_list = QListWidget()
        self.chat_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.chat_list.setSpacing(8)
        chat_layout.addWidget(self.chat_list)
        
        # 输入和控制区域
        input_container = QWidget()
        input_layout = QVBoxLayout(input_container)
        
        # 进度条 - 默认隐藏
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        input_layout.addWidget(self.progress_bar)
        
        # 文件选择和输入框
        input_controls = QHBoxLayout()
        
        self.file_btn = QPushButton("选择文件")
        self.file_btn.clicked.connect(self.select_files)
        
        input_controls.addWidget(self.file_btn)
        input_layout.addLayout(input_controls)
        
        # 显示已选文件
        self.file_label = QLabel()
        self.file_label.setWordWrap(True)
        input_layout.addWidget(self.file_label)
        
        # 文本输入区
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("输入消息...")
        self.input_text.setMaximumHeight(100)
        input_layout.addWidget(self.input_text)
        
        # 发送和清除按钮
        button_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("清空聊天")
        self.clear_btn.clicked.connect(self.clear_chat)
        
        self.send_btn = QPushButton("发送")
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setDefault(True)
        
        self.sidebar_btn = QPushButton("显示侧边栏")
        self.sidebar_btn.clicked.connect(self.toggle_sidebar)
        
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.sidebar_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.send_btn)
        
        input_layout.addLayout(button_layout)
        
        chat_layout.addWidget(input_container)
        
        # 添加聊天区域到分隔器
        self.splitter.addWidget(chat_container)
        
        # 创建侧边栏（默认不显示）
        self.sidebar = SidebarWidget()
        self.splitter.addWidget(self.sidebar)
        self.sidebar.setVisible(False)
        
        # 设置分隔器尺寸
        self.splitter.setSizes([self.width(), 0])
        
        # 主布局添加分隔器
        main_layout.addWidget(self.splitter)
    
    def select_files(self):
        """选择要发送的文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择文件",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif);;视频文件 (*.mp4 *.avi *.mov *.wmv)"
        )
        
        if files:
            self.media_files = files
            
            # 显示选择的文件名
            file_names = [os.path.basename(f) for f in files]
            self.file_label.setText("已选择: " + ", ".join(file_names))
        else:
            self.media_files = []
            self.file_label.setText("")
    
    def send_message(self):
        """发送消息"""
        content = self.input_text.toPlainText().strip()
        
        if not content and not self.media_files:
            return
        
        # 发送消息
        self.chat_engine.send_message(content, self.media_files)
        
        # 清空输入
        self.input_text.clear()
        self.media_files = []
        self.file_label.setText("")
    
    def on_new_message(self, message):
        """处理新消息"""
        # 创建消息项
        is_user = message.sender == "user"
        item_widget = MessageItem(message, is_user)
        
        # 创建列表项并设置自定义小部件
        list_item = QListWidgetItem(self.chat_list)
        list_item.setSizeHint(item_widget.sizeHint())
        self.chat_list.addItem(list_item)
        self.chat_list.setItemWidget(list_item, item_widget)
        
        # 滚动到底部
        self.chat_list.scrollToBottom()
    
    def on_processing(self, is_processing, message=None):
        """处理状态回调"""
        self.progress_bar.setVisible(is_processing)
        if message and is_processing:
            self.progress_bar.setFormat(message)
    
    def on_require_params(self, task_type, missing_params):
        """需要补充参数回调"""
        dialog = ParamDialog(task_type, missing_params, self)
        
        if dialog.exec():
            # 用户确认，获取参数
            params = dialog.get_parameters()
            
            # 更新消息
            self.chat_engine.update_message_with_params(task_type, params)
    
    def clear_chat(self):
        """清空聊天记录"""
        self.chat_list.clear()
        self.chat_engine.clear_history()
    
    def toggle_sidebar(self):
        """切换侧边栏显示状态"""
        self.sidebar_visible = not self.sidebar_visible
        self.sidebar.setVisible(self.sidebar_visible)
        
        # 更新按钮文本
        self.sidebar_btn.setText("隐藏侧边栏" if self.sidebar_visible else "显示侧边栏")
        
        # 调整分隔器大小
        if self.sidebar_visible:
            self.splitter.setSizes([int(self.width() * 0.6), int(self.width() * 0.4)])
        else:
            self.splitter.setSizes([self.width(), 0])
    
    def refresh_ui(self):
        """刷新UI文本"""
        self.file_btn.setText(_("chat.select_file"))
        self.clear_btn.setText(_("chat.clear"))
        self.send_btn.setText(_("chat.send"))
        
        sidebar_text = _("chat.hide_sidebar") if self.sidebar_visible else _("chat.show_sidebar")
        self.sidebar_btn.setText(sidebar_text)
        
        if self.progress_bar.isVisible():
            self.progress_bar.setFormat(_("chat.processing") + ": %p%")
        
        # 刷新侧边栏
        if self.sidebar:
            self.sidebar.refresh_ui()
    
    def on_show_sidebar(self, display_type, *args):
        """侧边栏显示回调"""
        # 如果侧边栏不可见，显示它
        if not self.sidebar_visible:
            self.toggle_sidebar()
        
        # 根据不同类型显示对应内容
        if display_type == "image_comparison" and len(args) >= 2:
            self.sidebar.show_image_comparison(args[0], args[1])
        elif display_type == "video" and args:
            self.sidebar.show_video(args[0])
        elif display_type == "camera" and len(args) >= 1:
            camera_id = args[0]
            process_type = args[1] if len(args) > 1 else None
            self.sidebar.show_camera(camera_id, process_type)
        elif display_type == "directory" and args:
            # 目录显示可以使用图像比较组件，或实现专门的目录浏览组件
            pass
