import os
import threading
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTextEdit, QListWidget, QListWidgetItem, QLabel, 
                               QFileDialog, QSplitter)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QPixmap, QIcon, QKeyEvent

from ChatRobot import ChatRobot
from gui.SidebarWidget import SidebarWidget
from gui.MessageBubble import MessageItem
from gui.ParameterWidget import ParameterWidget

class ChatWidget(QWidget):
    """聊天界面组件"""

    status_message = Signal(str)  # 状态消息信号
    
    def __init__(self):
        super().__init__()
        self.chat_robot = ChatRobot()
        self.selected_file_path = ""
        self.is_processing = False  # 添加处理状态标志
        
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
        
        # 连接textChanged信号以更新发送按钮状态
        self.input_text.textChanged.connect(lambda: self.update_send_button_state())
        self.input_text.keyPressEvent = self.input_key_press
        
        # 发送按钮
        self.send_btn = QPushButton("发送")
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QPushButton:hover:!disabled {
                background-color: #005fa3;
            }
        """)
        input_layout.addWidget(self.send_btn)
        
        # 初始化发送按钮状态为禁用
        self.send_btn.setEnabled(False)
        
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
        self.sidebar_btn.clicked.connect(self.toggle_sidebar)
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
        self.chat_robot.response_ready.connect(self.replace_current_message_item) # 替换准备好的消息到列表
        self.chat_robot.parameters_needed.connect(self.show_parameter_form) # 是否显示参数表单
        self.chat_robot.plugin_completed.connect(self.show_plugin_result) # 显示插件处理结果
        self.chat_robot.stream_content.connect(self.response_stream_to_widget) # 更新流式内容到聊天窗口
        
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
        
        # 更新发送按钮状态
        self.update_send_button_state()

    def update_send_button_state(self):
        """更新发送按钮状态"""
        has_content = bool(self.input_text.toPlainText().strip() or self.selected_file_path)
        self.send_btn.setEnabled(has_content and not self.is_processing)

    def send_message(self):
        """发送消息"""
        message_text = self.input_text.toPlainText().strip()
        
        # 如果没有内容且没有选择文件，不执行任何操作
        if not message_text and not self.selected_file_path:
            return
        
        # 设置处理状态，禁用发送按钮
        self.is_processing = True
        self.update_send_button_state()
        
        # 添加用户消息到列表
        self.add_message_to_list(message_text, self.selected_file_path, is_user=True)
        
        # 如果有选择文件，将文件路径添加到消息
        if self.selected_file_path:
            message_text = f"{message_text}\n[图片路径: {self.selected_file_path}]"
            # 设置原始图片到侧边栏
            self.sidebar.set_original_image(self.selected_file_path)
        
        # 清空输入框和文件选择
        self.input_text.clear()
        self.selected_file_path = ""
        self.file_label.setText("未选择文件")
        
        # 添加AI思考中的消息
        self.current_response_item = self.add_message_to_list("思考中...", "", is_user=False)
        self.status_message.emit("AI思考中...")

        # 在新线程中处理消息
        threading.Thread(target=self._process_message_in_thread, 
                        args=(message_text,), daemon=True).start()

    def _process_message_in_thread(self, message_text):
        """在新线程中处理消息"""
        try:
            self.current_response_content = "" # 用于存储流式回复的内容
            # 异步发送消息到ChatRobot
            status_message = self.chat_robot.ChatFrame(message_text)
            if status_message:
                self.status_message.emit("消息回复完毕，可以输入问题继续对话")
            # ChatRobot会通过信号触发UI更新
        except Exception as e:
            error_message = f"处理消息时发生错误: {e}"
            # 发送错误信号到信息列表
            self.replace_current_message_item(error_message)
            self.status_message.emit('AI处理消息时发生错误，请查看聊天窗口信息')
        finally:
            # 重置处理状态
            self.is_processing = False
            self.update_send_button_state()


    def add_message_to_list(self, text, image_path="", is_user=False):
        """向消息列表中添加一条消息并返回列表项"""
        message_item = MessageItem(text, image_path, is_user=is_user) # 创建消息气泡(图窗)
        list_item = QListWidgetItem(self.message_list) # 创建列表项
        list_item.setSizeHint(message_item.sizeHint()) # 设置列表项尺寸和消息气泡一致
        self.message_list.addItem(list_item) # 添加列表项
        self.message_list.setItemWidget(list_item, message_item) # 设置列表项的部件为消息气泡
        self.message_list.scrollToBottom() # 滚动到底部
        return list_item

    def replace_current_message_item(self, content, image_path="",is_user=False):
        """替换当前列表信息"""
        new_item = MessageItem(content, image_path, is_user=is_user)
        
        # 更新UI中的消息
        self.current_response_item.setSizeHint(new_item.sizeHint())
        self.message_list.setItemWidget(self.current_response_item, new_item)
        
        self.message_list.scrollToBottom() # 滚动到底部

    @Slot(str)
    def response_stream_to_widget(self, content):
        """更新流式内容到聊天窗口"""
        # 追加内容到当前回复
        self.current_response_content += content
        self.replace_current_message_item(self.current_response_content, is_user=False)

    @Slot(list)
    def show_parameter_form(self, parameters):
        """显示参数输入表单"""
        self.param_widget.setup_parameters(parameters)

    @Slot()
    def show_plugin_result(self):
        """显示插件处理结果"""
        # 显示侧边栏
        if self.chat_robot.current_plugin_params.get("is_show", False):
            self.show_sidebar()
        # 设置插件处理的结果
        if self.chat_robot.current_plugin.results:
            try:
                self.sidebar.set_processed_image(self.chat_robot.current_plugin.results[0])
                self.chat_robot.current_plugin.refresh()
            except Exception as e:
                self.sidebar.set_processed_image(None)

    @Slot(dict)
    def handle_parameters(self, parameters):
        """处理用户填写的参数并继续任务"""
        for param_name, param_value in parameters.items():
            self.chat_robot.current_plugin_params[param_name] = param_value
        self.chat_robot.waiting_for_params = False

    def toggle_sidebar(self):
        """按钮切换侧边栏显示状态"""
        if self.sidebar.isVisible():
            self.close_sidebar()
        else:
            # 显示侧边栏，并设置合适的宽度
            self.show_sidebar()
    
    def show_sidebar(self):
        """"显示侧边栏, 并设置合适的宽度"""
        self.sidebar.show()
        self.sidebar_btn.setText("➡️关闭侧边栏")
        
        # 设置合理的尺寸比例，例如聊天区域:侧边栏 = 2:1
        chat_width = int(self.splitter.width() * 0.65)
        sidebar_width = self.splitter.width() - chat_width
        self.splitter.setSizes([chat_width, sidebar_width])
        
    def close_sidebar(self):
        """隐藏侧边栏"""
        self.sidebar.hide()
        self.splitter.setSizes([self.width(), 0])  # 重置分割器尺寸，聊天区域占满
        self.sidebar_btn.setText("⬅️打开侧边栏")

    # 添加键盘事件处理，支持按Enter发送消息
    def input_key_press(self, event: QKeyEvent):
        """处理输入框的键盘事件"""
        # 按下Enter键发送消息，但按下Shift+Enter换行
        if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
            if self.send_btn.isEnabled():
                self.send_message()
                return
        # 其他情况正常处理
        QTextEdit.keyPressEvent(self.input_text, event)