from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

class SidebarWidget(QWidget):
    """侧边栏组件，用于显示处理前后的图片/视频"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 标题
        title = QLabel("处理结果")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)
        
        # 原始图片/视频区域
        self.original_label = QLabel("原始图片")
        self.original_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.original_label)
        
        self.original_image = QLabel()
        self.original_image.setAlignment(Qt.AlignCenter)
        self.original_image.setMinimumHeight(200)
        self.original_image.setStyleSheet("border: 1px solid #ccc;")
        layout.addWidget(self.original_image)
        
        # 处理后图片/视频区域
        self.processed_label = QLabel("处理后图片")
        self.processed_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.processed_label)
        
        self.processed_image = QLabel()
        self.processed_image.setAlignment(Qt.AlignCenter)
        self.processed_image.setMinimumHeight(200)
        self.processed_image.setStyleSheet("border: 1px solid #ccc;")
        layout.addWidget(self.processed_image)
        
        layout.addStretch()
    
    def set_original_image(self, image_path):
        """设置原始图片"""
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.original_image.setPixmap(scaled_pixmap)
    
    def set_processed_image(self, image_path):
        """设置处理后图片"""
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.processed_image.setPixmap(scaled_pixmap)
    