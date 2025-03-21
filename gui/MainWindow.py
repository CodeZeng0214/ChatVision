from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtGui import QIcon

from gui.ChatWidget import ChatWidget
from gui.PluginManagerWidget import PluginManagerWidget
from gui.SystemConfigWidget import SystemConfigWidget
from core.SystemConfig import system_config

class MainWindow(QMainWindow):
    """主窗口，包含聊天界面和插件管理界面"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChatVision")
        self.resize(900, 700)
        
        # 中央选项卡布局
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # 创建聊天界面
        self.chat_widget = ChatWidget()
        self.tabs.addTab(self.chat_widget, "聊天")
        
        # 创建插件管理界面
        self.plugin_manager = PluginManagerWidget(self.chat_widget.chat_robot.plugin_manager)
        self.tabs.addTab(self.plugin_manager, "插件管理")
        
        # 创建系统配置界面
        self.system_config_widget = SystemConfigWidget()
        self.system_config_widget.config_changed.connect(self.on_config_changed)
        self.tabs.addTab(self.system_config_widget, "系统设置")
        
        self.connect_signals() # 连接信号槽
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        
    def connect_signals(self):
        """连接信号槽"""
        # 聊天界面的状态消息连接到状态栏
        self.chat_widget.status_message.connect(self.on_status_message)
    
    @Slot(str)
    def on_status_message(self, message):
        """状态消息槽函数"""
        self.statusBar().showMessage(message)
        
    @Slot()
    def on_config_changed(self):
        """配置变更槽函数"""
        self.statusBar().showMessage("系统配置已更新，部分设置将在重启后生效")
