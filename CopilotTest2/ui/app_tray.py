from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QStyle
from PySide6.QtGui import QIcon, QAction
import os
from utils.i18n import _

class AppTray(QSystemTrayIcon):
    """应用程序系统托盘图标"""
    
    def __init__(self, main_window):
        super().__init__(parent=None)
        self.main_window = main_window
        
        # 设置图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "icons", "app_icon.png")
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            # 使用应用程序图标
            self.setIcon(QApplication.style().standardIcon(QApplication.style().SP_ComputerIcon))
        
        # 创建右键菜单
        self._setup_menu()
        
        # 连接信号
        self.activated.connect(self._on_activated)
        
        # 显示托盘图标
        self.show()
    
    def _setup_menu(self):
        """设置托盘右键菜单"""
        menu = QMenu()
        
        # 显示/隐藏主窗口
        self.show_action = QAction(_("tray.show"), self)
        self.show_action.triggered.connect(self._show_hide_window)
        menu.addAction(self.show_action)
        
        # 分隔线
        menu.addSeparator()
        
        # 关于
        about_action = QAction(_("menu.about"), self)
        about_action.triggered.connect(lambda: self.main_window.tabs.setCurrentIndex(3))
        menu.addAction(about_action)
        
        # 退出
        quit_action = QAction(_("menu.exit"), self)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)
        
        self.setContextMenu(menu)
        self._update_show_action()
    
    def _on_activated(self, reason):
        """处理托盘图标点击事件"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_hide_window()
    
    def _show_hide_window(self):
        """显示或隐藏主窗口"""
        if self.main_window.isVisible():
            self.main_window.hide()
        else:
            self.main_window.show()
            self.main_window.activateWindow()
        
        self._update_show_action()
    
    def _update_show_action(self):
        """更新显示/隐藏动作文本"""
        if self.main_window.isVisible():
            self.show_action.setText(_("tray.hide"))
        else:
            self.show_action.setText(_("tray.show"))
    
    def show_message(self, title, message):
        """显示托盘通知"""
        self.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)  # 使用正确的枚举
