import os
import threading
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTextEdit, QListWidget, QListWidgetItem, QLabel, 
                               QFileDialog, QSplitter)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QPixmap, QIcon

from ChatRobot import ChatRobot
from gui.SidebarWidget import SidebarWidget
from gui.MessageBubble import MessageItem
from gui.ParameterWidget import ParameterWidget

class ChatWidget(QWidget):
    """聊天界面组件"""
    
    def __init__(self):
        super().__init__()
        self.chat_robot = ChatRobot()
        self.selected_file_path = ""
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        # 主布局
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
        # 创建分割器
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # 聊天区域
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        
        # 消息列表
        self.message_list = QListWidget()
        self.message_list.setWordWrap(True)
        self.message_list.setSpacing(10)
        chat_layout.addWidget(self.message_list)
        
        # 输入区域 - 限制高度
        input_container = QWidget()
        input_container.setMaximumHeight(120)  # 限制输入区域最大高度
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(5, 5, 5, 5)  # 减少边距，使界面更紧凑
        
        # 文件选择区域 - 垂直布局
        file_select_container = QWidget()
        file_select_layout = QVBoxLayout(file_select_container)
        
        # 文件选择按钮
        self.file_btn = QPushButton("选择文件")
        self.file_btn.clicked.connect(self.select_file)
        file_select_layout.addWidget(self.file_btn)
        
        # 文件标签
        self.file_label = QLabel("未选择文件")
        self.file_label.setAlignment(Qt.AlignCenter)
        file_select_layout.addWidget(self.file_label)
        
        # 将文件选择区域添加到水平布局中
        input_layout.addWidget(file_select_container)
        
        # 输入框
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("请输入消息...")
        self.input_text.setMaximumHeight(80)  # 限制输入框的高度
        input_layout.addWidget(self.input_text)
        
        # 发送按钮
        self.send_btn = QPushButton("发送")
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        
        chat_layout.addWidget(input_container)
        
        # 参数输入区域
        self.param_widget = ParameterWidget()
        chat_layout.addWidget(self.param_widget)
        self.param_widget.hide()  # 默认隐藏参数区域
        
        self.splitter.addWidget(chat_container)
        
        # 侧边栏
        self.sidebar = SidebarWidget()
        self.splitter.addWidget(self.sidebar)
        self.sidebar.hide()  # 默认隐藏侧边栏
        
        # 添加侧边栏切换按钮
        self.sidebar_btn = QPushButton("⬅️打开侧边栏")
        #self.sidebar_btn.setFixedSize(30, 30)
        self.sidebar_btn.clicked.connect(self.toggleSidebar)
        chat_layout.addWidget(self.sidebar_btn)
        chat_layout.setAlignment(self.sidebar_btn, Qt.AlignRight | Qt.AlignTop)
        
        # 设置消息列表占据大部分空间
        chat_layout.setStretchFactor(self.message_list, 5)
        chat_layout.setStretchFactor(input_container, 1)
        
        # 设置分割器默认比例
        self.splitter.setSizes([self.width(), 0])  # 初始状态下侧边栏宽度为0
    
    def connect_signals(self):
        """连接信号和槽"""
        # 连接ChatRobot的信号
        self.chat_robot.parameters_needed.connect(self.show_parameter_form)
        self.chat_robot.processing_task.connect(self.show_processing_status)
        self.chat_robot.task_completed.connect(self.show_task_result)
        self.chat_robot.stream_content.connect(self.update_stream_content)
        
        # 连接参数表单的信号
        self.param_widget.parameters_ready.connect(self.handle_parameters)
    
    def select_file(self):
        """选择图片或视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", "图像文件 (*.png *.jpg *.jpeg);;视频文件 (*.mp4 *.avi);;所有文件 (*)"
        )
        if file_path:
            self.selected_file_path = file_path
            filename = file_path.split("/")[-1]
            self.file_label.setText(f"已选择: {filename}")
    
    def add_message_to_list(self, text, image_path="", is_user=True):
        """向消息列表中添加一条消息并返回列表项"""
        message_item = MessageItem(text, image_path, is_user=is_user)
        list_item = QListWidgetItem(self.message_list)
        list_item.setSizeHint(message_item.sizeHint())
        self.message_list.addItem(list_item)
        self.message_list.setItemWidget(list_item, message_item)
        self.message_list.scrollToBottom()
        return list_item
    
    def send_message(self):
        """发送消息"""
        message_text = self.input_text.toPlainText().strip()
        if not message_text and not self.selected_file_path:
            return
        
        # 添加用户消息到列表
        self.add_message_to_list(message_text, self.selected_file_path, is_user=True)
        
        # 如果有选择文件，将文件路径添加到消息
        if self.selected_file_path:
            message_text = f"{message_text}\n[图片路径: {self.selected_file_path}]"
            # 设置原始图片到侧边栏
            self.sidebar.set_original_image(self.selected_file_path)
            # 显示侧边栏
            self.showSidebar()
        
        # 清空输入框和文件选择
        self.input_text.clear()
        file_path = self.selected_file_path
        self.selected_file_path = ""
        self.file_label.setText("未选择文件")
        
        # 添加AI思考中的消息
        self.current_response_item = self.add_message_to_list("思考中...", "", is_user=False)
        self.current_response_content = ""
        
        # 在新线程中处理消息
        threading.Thread(target=self._process_message_in_thread, 
                        args=(message_text,), daemon=True).start()
    
    def _process_message_in_thread(self, message_text):
        """在新线程中处理消息"""
        try:
            # 异步发送消息到ChatRobot
            self.chat_robot.ChatFrame(message_text)
            # 注意：不需要在这里更新UI，因为ChatRobot会通过信号触发UI更新
        except Exception as e:
            error_message = f"处理消息时发生错误: {e}"
            # 发送错误信号到信息列表
            self.add_message_to_list(error_message)
            
    
    @Slot(str)
    def update_stream_content(self, content):
        """更新流式内容到聊天窗口"""
        # 追加内容到当前回复
        self.current_response_content += content
        
        # 更新UI中的消息
        ai_item = MessageItem(self.current_response_content, "", is_user=False)
        self.current_response_item.setSizeHint(ai_item.sizeHint())
        self.message_list.setItemWidget(self.current_response_item, ai_item)
        
        # 滚动到底部
        self.message_list.scrollToBottom()
    
    @Slot(list)
    def show_parameter_form(self, parameters):
        """显示参数输入表单"""
        self.param_widget.setup_parameters(parameters)
    
    @Slot(str)
    def show_processing_status(self, status):
        """显示任务处理状态"""
        # 更新最后一条消息为处理状态
        if self.message_list.count() > 0:
            last_item = self.message_list.item(self.message_list.count() - 1)
            last_widget = self.message_list.itemWidget(last_item)
            if isinstance(last_widget, MessageItem) and not last_widget.is_user:
                new_item = MessageItem(status, "", is_user=False)
                self.message_list.setItemWidget(last_item, new_item)
    
    @Slot(str, str)
    def show_task_result(self, task_type, image_path):
        """显示任务处理结果"""
        # 显示侧边栏
        self.showSidebar()
        
        # 设置原始图片
        self.sidebar.set_original_image(image_path)
        
        # 根据任务类型，可能还需要设置处理后的图片
        # 这里需要根据实际情况获取处理后图片路径
        processed_path = image_path.replace(".jpg", "_processed.jpg")
        if os.path.exists(processed_path):
            self.sidebar.set_processed_image(processed_path)
    
    @Slot(dict)
    def handle_parameters(self, parameters):
        """处理用户填写的参数并继续任务"""
        self.chat_robot.set_parameters(parameters)
    
    def toggleSidebar(self):
        """按钮切换侧边栏显示状态"""
        if self.sidebar.isVisible():
            self.closeSidebar()
        else:
            # 显示侧边栏，并设置合适的宽度
            self.showSidebar()
    
    def showSidebar(self):
        """"显示侧边栏, 并设置合适的宽度"""
        self.sidebar.show()
        self.sidebar_btn.setText("➡️关闭侧边栏")
        
        # 设置合理的尺寸比例，例如聊天区域:侧边栏 = 2:1
        chat_width = int(self.splitter.width() * 0.65)
        sidebar_width = self.splitter.width() - chat_width
        self.splitter.setSizes([chat_width, sidebar_width])
        
    def closeSidebar(self):
        """隐藏侧边栏"""
        self.sidebar.hide()
        self.sidebar_btn.setText("⬅️打开侧边栏")
        # 重置分割器尺寸，聊天区域占满
        self.splitter.setSizes([self.width(), 0])