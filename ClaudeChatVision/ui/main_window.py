from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, 
                              QTabWidget, QVBoxLayout, QSplitter)
from PySide6.QtCore import Qt, Slot

from ui.chat_window import ChatWindow
from ui.plugin_manager import PluginManagerWindow
from ui.sidebar import Sidebar
from core.task_processor import TaskProcessor
from core.llm_client import LLMClient

class MainWindow(QMainWindow):
    """主应用程序窗口，组织整体UI布局
    
    窗口分为两个主要部分:
    1. 左侧: 带有聊天和插件管理的选项卡界面
    2. 右侧: 用于显示结果和媒体的侧边栏
    
    该类管理核心组件的初始化，并连接UI组件之间的信号/槽通信。
    作为应用程序的主窗口，协调各个功能模块之间的交互。
    """
    def __init__(self):
        """初始化主窗口
        
        创建核心组件，包括LLM客户端和任务处理器，然后设置UI。
        构造函数负责初始化窗口并调用UI设置方法。
        """
        super().__init__()
        self.setWindowTitle("ChatVision")
        self.resize(1200, 800)
        
        # 初始化核心组件
        # LLM客户端处理自然语言处理任务
        self.llm_client = LLMClient()
        # 任务处理器协调UI、视觉插件和LLM之间的通信
        self.task_processor = TaskProcessor(self.llm_client)
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面组件和布局
        
        创建基于分割器的布局，左侧是选项卡，右侧是结果显示。
        同时建立组件之间所有必要的信号连接。
        定义整个应用程序的界面结构和数据流动方式。
        """
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        
        # 创建主UI部分的水平分割器
        main_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧: 包含聊天界面和插件管理器的选项卡小部件
        self.tab_widget = QTabWidget()
        self.chat_window = ChatWindow(self.task_processor)
        self.plugin_manager = PluginManagerWindow(self.task_processor)
        
        self.tab_widget.addTab(self.chat_window, "聊天")
        self.tab_widget.addTab(self.plugin_manager, "插件")
        
        # 右侧: 用于显示处理结果和媒体的侧边栏
        self.sidebar = Sidebar()
        
        # 信号连接 - 建立组件间数据流
        
        # 从聊天窗口到任务处理器: 当用户提交新任务时
        self.chat_window.new_task_request.connect(self.process_task)
        
        # 从任务处理器到侧边栏: 当任务结果准备好显示时
        self.task_processor.result_ready.connect(self.sidebar.display_result)
        
        # 参数处理信号: 当需要用户额外输入时
        self.task_processor.parameter_needed.connect(self.sidebar.show_parameter_input)
        self.sidebar.parameter_submitted.connect(self.task_processor.process_parameters)
        
        # 媒体处理: 当从聊天请求视频播放时
        self.chat_window.video_play_requested.connect(self.handle_media_request)
        
        # 将小部件添加到分割器并设置初始大小
        main_splitter.addWidget(self.tab_widget)
        main_splitter.addWidget(self.sidebar)
        main_splitter.setSizes([700, 500])  # 聊天区域700px, 侧边栏500px
        
        main_layout.addWidget(main_splitter)
        self.setCentralWidget(central_widget)
        
    def process_task(self, task_info):
        """处理来自聊天窗口的新任务
        
        这是一个桥接方法，将任务请求从聊天窗口转发到任务处理器组件。
        
        参数:
            task_info (dict): 有关要处理的任务的信息，包括:
                - message: 用户的文本查询
                - media_path: 任何附加媒体文件的路径
                - media_type: 媒体类型(image, video等)
        """
        self.task_processor.process_task(task_info)
    
    @Slot(str)
    def handle_media_request(self, media_path):
        """处理来自聊天消息的媒体显示请求
        
        当用户点击聊天消息中的媒体时，此方法确保媒体在侧边栏中显示。
        根据媒体类型选择合适的显示方式（图像或视频）。
        
        参数:
            media_path (str): 要显示的媒体文件路径
        """
        import os
        if not os.path.exists(media_path):
            print(f"找不到媒体文件: {media_path}")
            return
            
        if media_path.lower().endswith(('.mp4', '.avi', '.mov', '.wmv', '.mkv')):
            # 对于视频文件，使用侧边栏中的视频播放器
            self.sidebar.media_display.play_video(media_path)
        else:
            # 对于其他文件，假设它是图像并显示它
            self.sidebar.media_display.display_image(media_path)
