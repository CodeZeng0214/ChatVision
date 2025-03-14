from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QMessageBox, QApplication, QStyle
from PySide6.QtCore import Qt, QSize, QEvent
from PySide6.QtGui import QIcon, QAction, QCloseEvent
from ui.chat_widget import ChatWidget
from ui.plugin_manager_widget import PluginManagerWidget
from ui.settings_widget import SettingsWidget
from ui.about_widget import AboutWidget
from ui.app_tray import AppTray
from utils.i18n import _
import logging
import os
from config.app_config import AppConfig
from config.config_manager import ConfigManager

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self, chat_engine, plugin_manager):
        super().__init__()
        
        self.chat_engine = chat_engine
        self.plugin_manager = plugin_manager
        
        self.setWindowTitle(_("app.name") + " - " + _("app.description"))
        self.resize(AppConfig.DEFAULT_WINDOW_WIDTH, AppConfig.DEFAULT_WINDOW_HEIGHT)
        
        # 添加应用图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "icons", "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            # 如果找不到图标文件，尝试创建一个
            try:
                from resources.icons.app_icon import create_app_icon, save_icon_to_file
                
                # 生成并保存图标
                os.makedirs(os.path.dirname(icon_path), exist_ok=True)
                if save_icon_to_file(icon_path):
                    self.setWindowIcon(create_app_icon())
                    logging.info(f"已创建应用图标: {icon_path}")
                else:
                    logging.warning("无法创建应用图标")
            except Exception as e:
                logging.error(f"创建应用图标失败: {str(e)}")
        
        self._setup_menu()
        self._setup_ui()
        
        # 创建系统托盘图标
        self.app_tray = AppTray(self)
        
        # 状态栏
        self.statusBar().showMessage(_("status.ready"))
    
    def _setup_menu(self):
        """设置菜单栏"""
        # 创建菜单栏
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu(_("menu.file"))
        
        # 导出聊天记录
        export_action = QAction(_("menu.export_chat"), self)
        export_action.triggered.connect(self._export_chat)
        file_menu.addAction(export_action)
        
        # 退出应用
        exit_action = QAction(_("menu.exit"), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu(_("menu.edit"))
        
        # 清空聊天
        clear_action = QAction(_("menu.clear_chat"), self)
        clear_action.triggered.connect(self._clear_chat)
        edit_menu.addAction(clear_action)
        
        # 设置菜单
        settings_menu = menubar.addMenu(_("menu.settings"))
        
        # 语言选择
        lang_menu = settings_menu.addMenu(_("menu.language"))
        
        # 添加可用语言
        zh_action = QAction("简体中文", self)
        zh_action.triggered.connect(lambda: self._change_language("zh_CN"))
        lang_menu.addAction(zh_action)
        
        en_action = QAction("English", self)
        en_action.triggered.connect(lambda: self._change_language("en_US"))
        lang_menu.addAction(en_action)
        
        # 插件管理
        plugin_action = QAction(_("menu.manage_plugins"), self)
        plugin_action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        settings_menu.addAction(plugin_action)
        
        # 应用设置
        app_settings_action = QAction(_("menu.app_settings"), self)
        app_settings_action.triggered.connect(lambda: self.tabs.setCurrentIndex(2))
        settings_menu.addAction(app_settings_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu(_("menu.help"))
        
        # 关于
        about_action = QAction(_("menu.about"), self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_ui(self):
        """设置UI布局"""
        # 创建主标签页控件
        self.tabs = QTabWidget()
        
        # 创建聊天页面
        self.chat_widget = ChatWidget(self.chat_engine)
        
        # 创建插件管理页面
        self.plugin_manager_widget = PluginManagerWidget(self.plugin_manager)
        
        # 创建设置页面
        self.settings_widget = SettingsWidget()
        self.settings_widget.settings_changed.connect(self._on_settings_changed)
        
        # 创建关于页面
        self.about_widget = AboutWidget()
        
        # 添加标签页
        self.tabs.addTab(self.chat_widget, _("ui.chat"))
        self.tabs.addTab(self.plugin_manager_widget, _("ui.plugins"))
        self.tabs.addTab(self.settings_widget, _("ui.settings"))
        self.tabs.addTab(self.about_widget, _("ui.about"))
        
        # 设置主窗口的中心部件
        self.setCentralWidget(self.tabs)
        
        # 连接信号
        self.tabs.currentChanged.connect(self._on_tab_changed)
    
    def _on_tab_changed(self, index):
        """标签页切换时的处理"""
        if index == 1:  # 插件管理页
            self.plugin_manager_widget.refresh_plugins()
    
    def _export_chat(self):
        """导出聊天记录"""
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            _("dialog.export_chat"),
            "",
            "Text Files (*.txt);;HTML Files (*.html);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            if file_path.endswith(".html"):
                # 导出为HTML格式
                self._export_chat_html(file_path)
            else:
                # 导出为文本格式
                self._export_chat_text(file_path)
                
            QMessageBox.information(
                self,
                _("dialog.export_success"),
                _("dialog.export_success_message")
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                _("dialog.export_error"),
                _("dialog.export_error_message") + f": {str(e)}"
            )
    
    def _export_chat_text(self, file_path):
        """将聊天记录导出为文本文件"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"=== {_('app.name')} {_('app.version')} ===\n\n")
            
            for msg in self.chat_engine.messages:
                sender = _("chat.me") if msg.sender == "user" else _("chat.assistant")
                f.write(f"[{sender}]:\n{msg.content}\n\n")
                
                if msg.media_files:
                    f.write("附件:\n")
                    for media in msg.media_files:
                        f.write(f"- {os.path.basename(media)}\n")
                    f.write("\n")
    
    def _export_chat_html(self, file_path):
        """将聊天记录导出为HTML文件"""
        from datetime import datetime
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{_('app.name')} - {_('dialog.chat_history')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .message {{ margin-bottom: 20px; }}
        .user {{ text-align: right; }}
        .user .bubble {{ background-color: #95ec69; }}
        .assistant {{ text-align: left; }}
        .assistant .bubble {{ background-color: #ffffff; }}
        .bubble {{ display: inline-block; padding: 10px; border-radius: 10px; max-width: 70%; }}
        .sender {{ font-weight: bold; margin-bottom: 5px; }}
        .media {{ margin-top: 10px; }}
        .media img {{ max-width: 300px; max-height: 200px; }}
        .timestamp {{ font-size: 0.8em; color: #888; margin-top: 5px; }}
    </style>
</head>
<body>
    <h1>{_('app.name')} - {_('dialog.chat_history')}</h1>
    <p>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    <div class="chat">
""")
            
            for msg in self.chat_engine.messages:
                sender_class = "user" if msg.sender == "user" else "assistant"
                sender_name = _("chat.me") if msg.sender == "user" else _("chat.assistant")
                
                f.write(f'<div class="message {sender_class}">\n')
                f.write(f'<div class="sender">{sender_name}</div>\n')
                escaped_content = msg.content.replace("\n", "<br>")
                f.write(f'<div class="bubble">{escaped_content}</div>\n')
                
                if msg.media_files:
                    f.write('<div class="media">\n')
                    for media in msg.media_files:
                        media_path = media.replace("\\", "/")  # 修复反斜杠问题
                        if media.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                            f.write(f'<img src="file:///{media_path}" alt="{os.path.basename(media)}">\n')
                        else:
                            f.write(f'<div>[{os.path.basename(media)}]</div>\n')
                    f.write('</div>\n')
                
                f.write('</div>\n')
            
            f.write("""
    </div>
</body>
</html>
""")
    
    def _clear_chat(self):
        """清空聊天记录"""
        self.chat_widget.clear_chat()
    
    def _show_about(self):
        """显示关于窗口"""
        self.tabs.setCurrentIndex(3)  # 切换到关于标签页
    
    def _change_language(self, locale):
        """切换语言"""
        from utils.i18n import i18n
        i18n.set_locale(locale)
        
        # 更新界面文本
        self._on_settings_changed()
        
        # 显示语言切换成功提示
        self.statusBar().showMessage(_("status.language_changed"), 3000)
    
    def _on_settings_changed(self):
        """设置变更处理"""
        # 更新窗口标题
        self.setWindowTitle(_("app.name") + " - " + _("app.description"))
        
        # 更新标签页文本
        self.tabs.setTabText(0, _("ui.chat"))
        self.tabs.setTabText(1, _("ui.plugins"))
        self.tabs.setTabText(2, _("ui.settings"))
        self.tabs.setTabText(3, _("ui.about"))
        
        # 保存配置
        ConfigManager.save_config()
        
        # 通知其他组件刷新界面
        self.chat_widget.refresh_ui()
        
        # 刷新状态栏
        self.statusBar().showMessage(_("status.settings_saved"), 3000)
    
    def closeEvent(self, event: QCloseEvent):
        """窗口关闭事件处理"""
        # 询问是否最小化到系统托盘
        minimize_to_tray = AppConfig.__dict__.get("MINIMIZE_TO_TRAY", True)
        
        if minimize_to_tray and self.app_tray:
            event.ignore()  # 忽略关闭事件
            self.hide()     # 隐藏窗口
            
            # 显示提示，仅在第一次最小化时显示
            if not hasattr(self, "_tray_notification_shown"):
                self.app_tray.showMessage(
                    _("app.name"),
                    _("tray.minimized_message"),
                    QStyle.SP_MessageBoxInformation,  # 正确的枚举引用方式
                    3000  # 显示3秒
                )
                self._tray_notification_shown = True
        else:
            # 真正退出前确认
            reply = QMessageBox.question(
                self,
                _("dialog.exit_confirm"),
                _("dialog.exit_message"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 清理资源
                if hasattr(self, "app_tray") and self.app_tray:
                    self.app_tray.hide()
                    
                event.accept()  # 接受关闭事件
            else:
                event.ignore()  # 忽略关闭事件
