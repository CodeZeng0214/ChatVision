from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                              QTextEdit, QPushButton, QLabel, 
                              QScrollArea, QFileDialog, QSplitter, 
                              QMenu, QToolButton, QListWidget, QDialog)
from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QAction, QIcon

from ui.message_widget import MessageWidget
import os
import json
import datetime

class ChatHistoryDialog(QDialog):
    """对话历史选择对话框
    
    用于显示保存的对话历史记录，并允许用户选择一个历史对话加载到当前聊天窗口中。
    使用QListWidget展示可选的历史记录，双击或点击加载按钮可选择对话。
    
    信号:
        chat_selected: 当用户选择一个历史对话时发出，携带所选对话的消息列表
    """
    chat_selected = Signal(list)  # 当选择历史对话时发出的信号
    
    def __init__(self, history_entries, parent=None):
        """初始化对话历史选择对话框
        
        参数:
            history_entries: 包含历史对话条目的列表
            parent: 父窗口widget
        """
        super().__init__(parent)
        self.history_entries = history_entries
        self.setup_ui()
        
    def setup_ui(self):
        """设置对话框UI组件
        
        创建历史对话列表和按钮，设置布局和事件处理
        """
        self.setWindowTitle("聊天历史")
        self.setMinimumSize(400, 500)
        
        layout = QVBoxLayout(self)
        
        # 历史列表
        self.history_list = QListWidget()
        
        # 填充历史对话条目
        for i, entry in enumerate(self.history_entries):
            timestamp = entry.get("timestamp", "未知日期")
            message_count = len(entry.get("messages", []))
            self.history_list.addItem(f"{timestamp} ({message_count} 条消息)")
        
        # 双击选择功能
        self.history_list.itemDoubleClicked.connect(self.select_history)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        load_button = QPushButton("加载")
        load_button.clicked.connect(self.select_history)
        
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(load_button)
        button_layout.addWidget(cancel_button)
        
        layout.addWidget(QLabel("选择要加载的聊天历史:"))
        layout.addWidget(self.history_list)
        layout.addLayout(button_layout)
    
    def select_history(self):
        """处理用户选择历史对话的逻辑
        
        当用户双击列表项或点击加载按钮时触发
        发出包含选中对话消息的信号并关闭对话框
        """
        selected_row = self.history_list.currentRow()
        if selected_row >= 0 and selected_row < len(self.history_entries):
            selected_history = self.history_entries[selected_row]
            self.chat_selected.emit(selected_history.get("messages", []))
            self.accept()

class ChatWindow(QWidget):
    """聊天窗口主组件
    
    提供用户聊天界面，包括消息显示区域、输入框和媒体选择功能。
    管理对话历史，处理用户输入，并通过信号与其他组件通信。
    
    信号:
        new_task_request: 当用户发送包含文本和/或媒体的消息时发出
        video_play_requested: 当需要播放视频时发出
    """
    new_task_request = Signal(dict)  # 新任务请求信号
    video_play_requested = Signal(str)  # 视频播放请求信号
    
    def __init__(self, task_processor):
        """初始化聊天窗口
        
        参数:
            task_processor: 任务处理器实例，用于处理用户请求和预览媒体
        """
        super().__init__()
        self.task_processor = task_processor
        self.selected_media_path = None  # 当前选中的媒体文件路径
        self.media_type = None  # 媒体类型: 'image', 'video', 或 None
        self.conversation_history = []  # 当前对话历史
        self.chat_histories = []  # 所有保存的对话历史
        self.load_chat_histories()  # 从磁盘加载历史对话
        self.setup_ui()  # 设置UI组件
    
    def setup_ui(self):
        """设置聊天窗口UI布局和组件
        
        创建聊天显示区域、输入区域和控制按钮，设置布局和事件处理
        """
        main_layout = QVBoxLayout(self)
        
        # 聊天显示区域(上半部分)
        self.chat_area = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_area)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(10)
        
        # 使聊天区域可滚动
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.chat_area)
        
        # 输入区域(下半部分)
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        
        # 文本输入框
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("输入消息...")
        self.message_input.setFixedHeight(80)
        
        # 按钮行
        button_layout = QHBoxLayout()
        
        # 媒体按钮及下拉菜单
        self.media_button = QToolButton()
        self.media_button.setText("媒体")
        self.media_button.setIcon(QIcon.fromTheme("document-open"))
        self.media_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.media_button.setPopupMode(QToolButton.InstantPopup)
        
        media_menu = QMenu()
        
        # 图像选择动作
        image_action = QAction("选择图片", self)
        image_action.setIcon(QIcon.fromTheme("image-x-generic"))
        image_action.triggered.connect(lambda: self.select_media("image"))
        
        # 视频选择动作
        video_action = QAction("选择视频", self)
        video_action.setIcon(QIcon.fromTheme("video-x-generic"))
        video_action.triggered.connect(lambda: self.select_media("video"))
        
        # 相机选择动作
        camera_action = QAction("使用摄像头", self)
        camera_action.setIcon(QIcon.fromTheme("camera-photo"))
        camera_action.triggered.connect(self.open_camera)
        
        media_menu.addAction(image_action)
        media_menu.addAction(video_action)
        media_menu.addAction(camera_action)
        
        self.media_button.setMenu(media_menu)
        # 添加直接点击处理器确保菜单显示
        self.media_button.clicked.connect(self.media_button.showMenu)
        
        # 选中文件名称显示
        self.media_label = QLabel("未选择媒体")
        self.media_label.setWordWrap(True)
        
        # 清除媒体按钮
        self.clear_media_button = QPushButton("×")
        self.clear_media_button.setFixedSize(24, 24)
        self.clear_media_button.setToolTip("清除选中的媒体")
        self.clear_media_button.clicked.connect(self.clear_media)
        self.clear_media_button.setVisible(False)
        
        # 历史按钮
        self.history_button = QPushButton("聊天历史")
        self.history_button.setIcon(QIcon.fromTheme("document-open-recent"))
        self.history_button.clicked.connect(self.show_chat_history)
        
        # 新对话按钮
        self.new_chat_button = QPushButton("新对话")
        self.new_chat_button.setIcon(QIcon.fromTheme("document-new"))
        self.new_chat_button.clicked.connect(self.start_new_chat)
        
        # 发送按钮
        self.send_button = QPushButton("发送")
        self.send_button.setIcon(QIcon.fromTheme("mail-send"))
        self.send_button.clicked.connect(self.send_message)
        
        # 媒体选择行
        media_layout = QHBoxLayout()
        media_layout.addWidget(self.media_button)
        media_layout.addWidget(self.media_label)
        media_layout.addWidget(self.clear_media_button)
        media_layout.addStretch()
        
        # 按钮行
        button_layout.addWidget(self.history_button)
        button_layout.addStretch()
        button_layout.addWidget(self.new_chat_button)
        button_layout.addWidget(self.send_button)
        
        input_layout.addWidget(self.message_input)
        input_layout.addLayout(media_layout)
        input_layout.addLayout(button_layout)
        
        # 添加可调整大小的分割器
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.scroll_area)
        splitter.addWidget(input_widget)
        splitter.setSizes([600, 200])
        
        main_layout.addWidget(splitter)
    
    def select_media(self, media_type):
        """处理媒体选择
        
        打开文件对话框让用户选择图像或视频文件，并在侧边栏预览所选媒体
        
        参数:
            media_type: 媒体类型，'image'或'video'
        """
        file_dialog = QFileDialog(self)
        
        if media_type == "image":
            file_dialog.setNameFilter("图像 (*.png *.jpg *.jpeg *.bmp *.gif)")
            file_dialog.setWindowTitle("选择图片")
        elif media_type == "video":
            file_dialog.setNameFilter("视频 (*.mp4 *.avi *.mov *.wmv *.mkv)")
            file_dialog.setWindowTitle("选择视频")
        
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.selected_media_path = selected_files[0]
                self.media_type = media_type
                file_name = os.path.basename(self.selected_media_path)
                self.media_label.setText(f"{media_type.capitalize()}: {file_name}")
                self.clear_media_button.setVisible(True)
                
                # 在侧边栏预览媒体
                if media_type == "video":
                    self.video_play_requested.emit(self.selected_media_path)
                elif media_type == "image":
                    self.task_processor.preview_image(self.selected_media_path)
    
    def clear_media(self):
        """清除当前选中的媒体
        
        重置媒体选择状态，清除显示标签并隐藏清除按钮
        """
        self.selected_media_path = None
        self.media_type = None
        self.media_label.setText("未选择媒体")
        self.clear_media_button.setVisible(False)
    
    def open_camera(self):
        """使用相机功能
        
        将媒体类型设为摄像头，并请求在侧边栏显示摄像头预览
        """
        self.selected_media_path = "camera"
        self.media_type = "camera"
        self.media_label.setText("使用摄像头")
        # 向侧边栏发送显示相机预览的信号
        self.task_processor.request_camera_preview()
    
    def send_message(self):
        """处理发送消息的逻辑
        
        获取用户输入的文本和选择的媒体，添加到对话中
        并发送任务请求信号，触发AI响应
        """
        message_text = self.message_input.toPlainText().strip()
        
        # 文本和媒体都为空时不发送
        if not message_text and not self.selected_media_path:
            return
        
        # 添加用户消息到聊天区域
        self.add_message("您", message_text, self.selected_media_path, self.media_type, is_user=True)
        
        # 准备任务信息
        task_info = {
            "message": message_text,
            "media_path": self.selected_media_path,
            "media_type": self.media_type
        }
        
        # 清除输入
        self.message_input.clear()
        self.clear_media()
        
        # 处理任务
        self.new_task_request.emit(task_info)
        
        # 添加短暂延迟后显示AI响应
        QTimer.singleShot(1000, lambda: self.handle_ai_response(task_info))
    
    def handle_ai_response(self, task_info):
        """处理AI对用户查询的响应
        
        在聊天区域添加AI助手的响应消息
        
        参数:
            task_info: 包含用户消息和媒体信息的字典
        
        注意: 在实际实现中，应该连接到任务处理器的信号
        """
        # 添加占位响应，实际应用中应等待任务处理器的结果
        self.add_message("AI 助手", "我已处理您的请求。请查看侧边栏获取结果。", is_user=False)
    
    def add_message(self, username, message, media_path=None, media_type=None, is_user=False):
        """添加消息到聊天区域
        
        创建新的消息小部件并添加到聊天布局中，同时保存到会话历史记录
        
        参数:
            username: 发送消息的用户名
            message: 消息文本
            media_path: 可选的媒体文件路径
            media_type: 媒体类型，'image'或'video'
            is_user: 是否为用户发送的消息
        """
        message_widget = MessageWidget(username, message, media_path, media_type, is_user)
        self.chat_layout.addWidget(message_widget)
        
        # 连接视频播放请求信号
        message_widget.video_play_requested.connect(self.video_play_requested)
        
        # 保存到对话历史
        message_data = {
            "username": username,
            "message": message,
            "media_path": media_path,
            "media_type": media_type,
            "is_user": is_user,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.conversation_history.append(message_data)
        
        # 自动滚动到底部
        QTimer.singleShot(50, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        """滚动聊天区域到底部，显示最新消息
        
        确保新添加的消息可见，提供更好的用户体验
        """
        scroll_bar = self.scroll_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())
        
    def start_new_chat(self):
        """开始新对话，保存当前对话并清除聊天区域
        
        将当前会话保存到历史记录，然后清空聊天界面准备新对话
        """
        if self.conversation_history:
            self.save_current_chat()
        
        # 清除聊天显示
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # 重置对话历史
        self.conversation_history = []
        self.message_input.clear()
        self.clear_media()
    
    def save_current_chat(self):
        """保存当前对话到历史记录
        
        创建包含时间戳和所有消息的历史记录条目并保存到磁盘
        """
        if not self.conversation_history:
            return
            
        # 创建对话历史条目
        chat_entry = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "messages": self.conversation_history
        }
        
        # 添加到历史记录
        self.chat_histories.append(chat_entry)
        
        # 保存到磁盘
        self.save_chat_histories()
    
    def load_chat_histories(self):
        """从磁盘加载对话历史记录
        
        尝试读取历史记录JSON文件，如果文件不存在则初始化空列表
        """
        history_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "chat_history.json")
        os.makedirs(os.path.dirname(history_path), exist_ok=True)
        
        try:
            if os.path.exists(history_path):
                with open(history_path, 'r', encoding='utf-8') as f:
                    self.chat_histories = json.load(f)
        except Exception as e:
            print(f"加载聊天历史时出错: {str(e)}")
            self.chat_histories = []
    
    def save_chat_histories(self):
        """保存对话历史记录到磁盘
        
        将历史记录列表序列化为JSON并写入文件
        """
        history_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "chat_history.json")
        os.makedirs(os.path.dirname(history_path), exist_ok=True)
        
        try:
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(self.chat_histories, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存聊天历史时出错: {str(e)}")
    
    def show_chat_history(self):
        """显示对话历史选择对话框
        
        如果有历史记录，显示对话框让用户选择要加载的历史会话
        """
        if not self.chat_histories:
            return
            
        # 先保存当前对话
        if self.conversation_history:
            self.save_current_chat()
        
        # 显示历史对话框
        dialog = ChatHistoryDialog(self.chat_histories, self)
        dialog.chat_selected.connect(self.load_chat)
        dialog.exec()
    
    def load_chat(self, messages):
        """加载选中的对话历史
        
        清空当前对话并加载所选历史会话的所有消息
        
        参数:
            messages: 包含消息的列表
        """
        # 清除当前对话
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # 重置对话历史
        self.conversation_history = []
        
        # 添加消息
        for msg in messages:
            username = msg.get("username", "未知用户")
            message = msg.get("message", "")
            media_path = msg.get("media_path")
            media_type = msg.get("media_type")
            is_user = msg.get("is_user", False)
            
            self.add_message(username, message, media_path, media_type, is_user)
