from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, 
                              QTabWidget, QVBoxLayout, QSplitter)
from PySide6.QtCore import Qt, Slot

from ui.chat_window import ChatWindow
from ui.plugin_manager import PluginManagerWindow
from ui.sidebar import Sidebar
from core.task_processor import TaskProcessor
from core.llm_client import LLMClient

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChatVision")
        self.resize(1200, 800)
        
        # Initialize components
        self.llm_client = LLMClient()
        self.task_processor = TaskProcessor(self.llm_client)
        
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        
        # Create main splitter between chat/tabs and sidebar
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Tab widget for chat and plugin manager
        self.tab_widget = QTabWidget()
        self.chat_window = ChatWindow(self.task_processor)
        self.plugin_manager = PluginManagerWindow(self.task_processor)
        
        self.tab_widget.addTab(self.chat_window, "Chat")
        self.tab_widget.addTab(self.plugin_manager, "Plugins")
        
        # Right side: Sidebar for displaying results
        self.sidebar = Sidebar()
        
        # Connect signals
        self.chat_window.new_task_request.connect(self.process_task)
        self.task_processor.result_ready.connect(self.sidebar.display_result)
        self.task_processor.parameter_needed.connect(self.sidebar.show_parameter_input)
        self.sidebar.parameter_submitted.connect(self.task_processor.process_parameters)
        
        # Add widgets to splitter
        main_splitter.addWidget(self.tab_widget)
        main_splitter.addWidget(self.sidebar)
        main_splitter.setSizes([700, 500])
        
        main_layout.addWidget(main_splitter)
        self.setCentralWidget(central_widget)
        
    def process_task(self, task_info):
        """Process a new task from the chat window"""
        self.task_processor.process_task(task_info)
