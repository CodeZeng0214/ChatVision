from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                              QLabel, QScrollArea, QPushButton,
                              QComboBox, QStackedWidget, QFileDialog,
                              QLineEdit, QFormLayout)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtMultimedia import QMediaPlayer, QCamera, QMediaCaptureSession, QVideoFrame, QVideoSink
import os

class MediaDisplayWidget(QWidget):
    """用于显示图像或视频的小部件
    
    提供了一个统一的界面用于显示不同类型的媒体（图像、视频和摄像头实时预览）。
    通过堆叠小部件实现在不同媒体类型之间的切换。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 堆叠式小部件，用于在不同媒体类型之间切换
        self.stack = QStackedWidget()
        
        # 图像显示区域
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #d0d0d0;")
        self.stack.addWidget(self.image_label)
        
        # 视频显示区域
        self.video_widget = QVideoWidget()
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.stack.addWidget(self.video_widget)
        
        # 摄像头显示区域
        self.camera_widget = QWidget()
        camera_layout = QVBoxLayout(self.camera_widget)
        
        self.camera_view = QVideoWidget()
        self.camera_capture_session = QMediaCaptureSession()
        self.camera_capture_session.setVideoOutput(self.camera_view)
        
        camera_controls = QHBoxLayout()
        self.camera_select = QComboBox()
        self.camera_select.addItem("默认摄像头")  # 在实际应用中，你会列出所有可用摄像头
        self.camera_start_btn = QPushButton("启动摄像头")
        self.camera_start_btn.clicked.connect(self.toggle_camera)
        
        camera_controls.addWidget(QLabel("摄像头:"))
        camera_controls.addWidget(self.camera_select)
        camera_controls.addWidget(self.camera_start_btn)
        
        camera_layout.addWidget(self.camera_view)
        camera_layout.addLayout(camera_controls)
        
        self.stack.addWidget(self.camera_widget)
        
        layout.addWidget(self.stack)
        
        # 初始状态下摄像头是停止的
        self.camera = None
        self.camera_running = False
        
    def display_image(self, image_path):
        """在图像标签中显示图像
        
        接收图像路径，加载并显示图像，如果图像无效则显示错误信息。
        图像会根据窗口大小自动缩放，保持宽高比。
        
        参数:
            image_path (str): 待显示图像的文件路径
        """
        try:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                # 处理无效图像文件
                self.image_label.setText("无效的图像文件")
                return
                
            self.image_label.setPixmap(pixmap.scaled(
                self.image_label.width(), 
                self.image_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
            self.stack.setCurrentIndex(0)  # 切换到图像显示界面
        except Exception as e:
            print(f"显示图像时出错: {str(e)}")
            self.image_label.setText(f"错误: {str(e)}")
    
    def play_video(self, video_path):
        """播放视频小部件中的视频
        
        加载并播放指定路径的视频文件，如果文件不存在则输出错误信息。
        
        参数:
            video_path (str): 待播放视频的文件路径
        """
        try:
            if not video_path or not os.path.exists(video_path):
                print(f"视频文件不存在: {video_path}")
                return
                
            self.media_player.setSource(video_path)
            self.media_player.play()
            self.stack.setCurrentIndex(1)  # 切换到视频显示界面
        except Exception as e:
            print(f"播放视频时出错: {str(e)}")
    
    def toggle_camera(self):
        """切换摄像头开关状态
        
        如果摄像头正在运行则停止，否则启动摄像头。
        更新按钮文本以反映当前状态，并显示摄像头视图。
        """
        if self.camera_running:
            # 停止摄像头
            if self.camera:
                self.camera.stop()
                self.camera = None
            self.camera_running = False
            self.camera_start_btn.setText("启动摄像头")
        else:
            # 启动摄像头
            self.camera = QCamera()
            self.camera_capture_session.setCamera(self.camera)
            self.camera.start()
            self.camera_running = True
            self.camera_start_btn.setText("停止摄像头")
        
        self.stack.setCurrentIndex(2)  # 切换到摄像头显示界面
    
    def resizeEvent(self, event):
        """处理小部件大小变化事件
        
        当窗口大小改变时，确保显示的图像能够适当缩放以匹配新的窗口尺寸。
        保持图像的宽高比，并使用平滑变换提高显示质量。
        
        参数:
            event: 窗口大小变化事件对象
        """
        super().resizeEvent(event)
        # 如果当前显示的是图像，则在小部件大小变化时重新调整图像大小
        if self.stack.currentIndex() == 0:
            pixmap = self.image_label.pixmap()
            if pixmap and not pixmap.isNull():
                self.image_label.setPixmap(pixmap.scaled(
                    self.image_label.width(), 
                    self.image_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                ))

    @Slot(str)
    def play_video_from_chat(self, video_path):
        """从聊天消息中播放视频
        
        接收聊天消息中请求播放的视频路径，调用播放视频方法。
        
        参数:
            video_path (str): 待播放视频的文件路径
        """
        self.play_video(video_path)


class ParameterInputWidget(QWidget):
    """用于从用户收集额外参数的小部件
    
    当任务处理需要附加信息时，显示动态生成的表单，让用户输入所需参数。
    支持文本输入、图像选择器和摄像头选择器等不同类型的输入控件。
    """
    parameter_submitted = Signal(dict)  # 参数提交后发出的信号，携带参数字典
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.param_widgets = {}
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.header_label = QLabel("需要附加信息")
        self.header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.description_label = QLabel("")
        
        # 参数输入的表单布局
        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)
        
        # 提交按钮
        self.submit_button = QPushButton("提交")
        self.submit_button.clicked.connect(self.submit_parameters)
        
        layout.addWidget(self.header_label)
        layout.addWidget(self.description_label)
        layout.addWidget(self.form_widget)
        layout.addWidget(self.submit_button)
        layout.addStretch()
        
        # 初始状态下隐藏小部件
        self.setVisible(False)
        
    def set_parameters(self, param_list, description="请提供以下信息:"):
        """设置需要用户输入的参数
        
        根据提供的参数列表动态创建表单控件，并显示参数输入界面。
        根据参数类型创建不同的输入控件（文本框、图像选择器等）。
        
        参数:
            param_list (list): 参数定义列表，每个参数为一个字典
            description (str): 显示给用户的参数输入说明
        """
        # 清除现有参数
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        self.param_widgets = {}
        self.description_label.setText(description)
        
        # 添加新参数
        for param in param_list:
            param_name = param["name"]
            param_label = param.get("label", param_name)
            param_type = param.get("type", "text")
            
            label = QLabel(param_label)
            
            if param_type == "image_selector":
                widget = QPushButton("选择图像")
                widget.clicked.connect(lambda _, p=param_name: self.select_image(p))
                self.param_widgets[param_name] = {"type": param_type, "widget": widget, "value": None}
            elif param_type == "camera_selector":
                widget = QComboBox()
                widget.addItem("默认摄像头")
                self.param_widgets[param_name] = {"type": param_type, "widget": widget, "value": "默认摄像头"}
            else:  # 默认为文本输入
                widget = QLineEdit()
                if "default" in param:
                    widget.setText(str(param["default"]))
                self.param_widgets[param_name] = {"type": param_type, "widget": widget, "value": param.get("default", "")}
            
            self.form_layout.addRow(label, widget)
        
        self.setVisible(True)
    
    def select_image(self, param_name):
        """打开图像选择对话框
        
        允许用户从文件系统中选择图像文件，更新对应参数的值。
        
        参数:
            param_name (str): 要为其设置图像的参数名称
        """
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                self.param_widgets[param_name]["value"] = file_path
                self.param_widgets[param_name]["widget"].setText(file_path.split('/')[-1])
    
    def submit_parameters(self):
        """提交收集的参数
        
        收集所有参数控件的值，发送参数提交信号，然后隐藏参数输入界面。
        """
        # 收集参数值
        params = {}
        for param_name, param_data in self.param_widgets.items():
            if param_data["type"] == "image_selector":
                params[param_name] = param_data["value"]
            elif param_data["type"] == "camera_selector":
                params[param_name] = param_data["widget"].currentText()
            else:  # 文本输入
                params[param_name] = param_data["widget"].text()
        
        self.parameter_submitted.emit(params)
        self.setVisible(False)


class Sidebar(QWidget):
    """侧边栏小部件，用于显示结果和参数输入
    
    侧边栏包含媒体显示区域、结果文本显示区域和参数输入区域。
    负责展示视觉任务的处理结果，并在需要时收集用户输入的额外参数。
    """
    parameter_submitted = Signal(dict)  # 参数提交信号，将用户提供的参数转发给任务处理器
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 标题标签
        title_label = QLabel("结果 & 预览")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        # 媒体显示区域
        self.media_display = MediaDisplayWidget()
        
        # 结果文本显示
        self.results_label = QLabel("处理结果:")
        self.results_text = QLabel("暂无结果。")
        self.results_text.setWordWrap(True)
        self.results_text.setStyleSheet("background-color: #f9f9f9; padding: 8px; border-radius: 4px;")
        
        # 为结果创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.addWidget(self.results_text)
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        
        # 参数输入小部件
        self.param_input = ParameterInputWidget()
        self.param_input.parameter_submitted.connect(self.on_parameter_submitted)
        
        layout.addWidget(title_label)
        layout.addWidget(self.media_display, 3)  # 拉伸因子 3
        layout.addWidget(self.results_label)
        layout.addWidget(scroll_area, 2)  # 拉伸因子 2
        layout.addWidget(self.param_input, 1)  # 拉伸因子 1
    
    @Slot(dict)
    def display_result(self, result_data):
        """在侧边栏中显示结果
        
        根据结果数据类型（图像、视频或文本）显示相应内容。
        检查文件是否存在，处理可能的错误。
        
        参数:
            result_data (dict): 包含要显示的结果数据
        """
        try:
            # 处理图像结果
            if "image_path" in result_data:
                if os.path.exists(result_data["image_path"]):
                    self.media_display.display_image(result_data["image_path"])
                else:
                    print(f"找不到图像文件: {result_data['image_path']}")
            
            # 处理视频结果
            elif "video_path" in result_data:
                if os.path.exists(result_data["video_path"]):
                    self.media_display.play_video(result_data["video_path"])
                else:
                    print(f"找不到视频文件: {result_data['video_path']}")
            
            # 处理摄像头提要
            elif "camera" in result_data:
                self.media_display.toggle_camera()
            
            # 显示文本结果
            if "text" in result_data:
                self.results_text.setText(result_data["text"])
        except Exception as e:
            print(f"显示结果时出错: {str(e)}")
            self.results_text.setText(f"显示结果时出错: {str(e)}")
    
    @Slot(list, str)
    def show_parameter_input(self, param_list, description=""):
        """当需要附加信息时显示参数输入字段
        
        接收需要用户输入的参数列表和描述，调用参数输入小部件显示表单。
        
        参数:
            param_list (list): 参数定义列表
            description (str): 参数输入说明
        """
        self.param_input.set_parameters(param_list, description)
    
    def on_parameter_submitted(self, params):
        """将参数提交转发给任务处理器
        
        当用户提交参数后，通过信号将参数转发给关联的任务处理器。
        
        参数:
            params (dict): 用户提供的参数值
        """
        self.parameter_submitted.emit(params)

    def connect_video_signals(self, chat_window):
        """连接来自聊天中消息小部件的视频播放信号
        
        此方法需要在聊天窗口初始化后调用。
        目前通过任务处理器处理这个功能。
        
        参数:
            chat_window: 聊天窗口实例
        """
        pass
