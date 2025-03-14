from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QFont

class MessageItem(QWidget):
    """消息气泡组件"""
    
    def __init__(self, text, image_path="", is_user=True):
        super().__init__()
        self.text = text
        self.image_path = image_path
        self.is_user = is_user
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
        # 创建消息容器
        message_container = QWidget()
        message_layout = QVBoxLayout(message_container)
        message_container.setStyleSheet(
            "background-color: #a0d8ef;" if not self.is_user else "background-color: #95e1d3;"
            "border-radius: 10px; padding: 10px;"
        )
        
        # 用户名标签
        name_label = QLabel("ChatIR" if not self.is_user else "你")
        name_label.setStyleSheet("font-weight: bold; color: #333;")
        message_layout.addWidget(name_label)
        
        # 消息文本
        if self.text:
            text_label = QLabel(self.text)
            text_label.setWordWrap(True)
            text_label.setTextFormat(Qt.TextFormat.RichText)
            message_layout.addWidget(text_label)
        
        # 消息图片
        if self.image_path:
            image_label = QLabel()
            pixmap = QPixmap(self.image_path)
            scaled_pixmap = pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
            image_label.setMaximumSize(300, 200)
            message_layout.addWidget(image_label)
        
        # 控制消息气泡的对齐方式
        if self.is_user:
            main_layout.addStretch()
            main_layout.addWidget(message_container)
        else:
            main_layout.addWidget(message_container)
            main_layout.addStretch()
        
        # 设置尺寸策略
        message_container.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
