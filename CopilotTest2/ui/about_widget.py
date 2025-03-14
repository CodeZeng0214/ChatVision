from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QScrollArea, QTextBrowser)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QFont
from config.app_config import AppConfig
from utils.i18n import _
import os

class AboutWidget(QWidget):
    """关于界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        
        # 标题和图标
        title_layout = QHBoxLayout()
        
        # 加载图标
        app_icon = QLabel()
        app_icon.setFixedSize(QSize(64, 64))
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                "resources", "icons", "app_icon.png")
        if os.path.exists(icon_path):
            app_icon.setPixmap(QPixmap(icon_path).scaled(
                app_icon.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        
        title_layout.addWidget(app_icon)
        
        title_text = QLabel(f"{AppConfig.APP_NAME} v{AppConfig.APP_VERSION}")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_text.setFont(title_font)
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # 应用描述
        desc_label = QLabel(_("app.description"))
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 关于信息
        about_browser = QTextBrowser()
        about_browser.setOpenExternalLinks(True)
        about_browser.setHtml(self._get_about_html())
        layout.addWidget(about_browser)
        
        # 版权信息
        copyright_label = QLabel("© 2023 ChatVision Team. All rights reserved.")
        copyright_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright_label)
    
    def _get_about_html(self):
        """获取关于信息的HTML"""
        return f"""
        <h3>ChatVision - {_("app.description")}</h3>
        <p>基于大语言模型和计算机视觉技术的聊天机器人，能够识别和分析图像内容。</p>
        
        <h4>主要功能:</h4>
        <ul>
            <li>图像识别：使用YOLO模型检测图像中的物体</li>
            <li>图像描述：使用BLIP模型生成图像内容描述</li>
            <li>姿态估计：检测图像中人体的姿态和关键点</li>
            <li>批量处理：处理指定目录中的多个图像</li>
            <li>实时处理：处理摄像头或视频流</li>
        </ul>
        
        <h4>技术框架:</h4>
        <ul>
            <li>UI: PySide6 (Qt for Python)</li>
            <li>大语言模型: OpenAI API兼容接口</li>
            <li>计算机视觉: OpenCV</li>
            <li>插件系统: 基于Python动态加载</li>
        </ul>
        
        <h4>开发团队:</h4>
        <p>ChatVision是一个开源项目，由开发者社区共同维护。</p>
        
        <h4>致谢:</h4>
        <p>特别感谢OpenAI、OpenCV以及所有为这个项目做出贡献的人员。</p>
        """
