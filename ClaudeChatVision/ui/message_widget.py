from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                              QLabel, QPushButton)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget

class MessageWidget(QWidget):
    """Custom widget for displaying a single message (text and/or media)"""
    video_play_requested = Signal(str)  # Signal emitted when video play is requested
    
    def __init__(self, username, message, media_path=None, media_type=None, is_user=False, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.media_path = media_path
        self.media_type = media_type
        self.media_player = None
        self.video_widget = None
        self.setup_ui(username, message, media_path, media_type)
        
    def setup_ui(self, username, message, media_path, media_type):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Username label
        username_label = QLabel(username)
        username_label.setStyleSheet("font-weight: bold;")
        
        # Message content
        message_widget = QWidget()
        message_layout = QVBoxLayout(message_widget)
        message_layout.setContentsMargins(10, 10, 10, 10)
        
        if message:
            text_label = QLabel(message)
            text_label.setWordWrap(True)
            message_layout.addWidget(text_label)
        
        if media_path:
            if media_type == "image":
                image_label = QLabel()
                pixmap = QPixmap(media_path)
                # Resize if too large
                if pixmap.width() > 250:
                    pixmap = pixmap.scaledToWidth(250, Qt.SmoothTransformation)
                image_label.setPixmap(pixmap)
                message_layout.addWidget(image_label)
                
            elif media_type == "video":
                # For video, we show a thumbnail with a play button
                thumbnail_widget = QWidget()
                thumbnail_layout = QVBoxLayout(thumbnail_widget)
                
                # Create a thumbnail from the video (simplified - would need media processing in real app)
                # Here we're using a play button icon to represent video
                video_btn = QPushButton("Play Video")
                video_btn.setIcon(QIcon.fromTheme("media-playback-start"))
                video_btn.clicked.connect(self.play_video)
                
                thumbnail_layout.addWidget(video_btn)
                message_layout.addWidget(thumbnail_widget)
        
        # Style the message bubble
        if self.is_user:
            message_widget.setStyleSheet("background-color: #95EC69; border-radius: 10px;")
        else:
            message_widget.setStyleSheet("background-color: #FFFFFF; border-radius: 10px;")
        
        # Layout alignment based on message sender
        h_layout = QHBoxLayout()
        if self.is_user:
            h_layout.addStretch()
            main_layout.addWidget(username_label, 0, Qt.AlignRight)
            h_layout.addWidget(message_widget)
        else:
            main_layout.addWidget(username_label, 0, Qt.AlignLeft)
            h_layout.addWidget(message_widget)
            h_layout.addStretch()
        
        main_layout.addLayout(h_layout)
    
    def play_video(self):
        # Signal to sidebar to play this video
        if self.media_path and self.media_type == "video":
            self.video_play_requested.emit(self.media_path)
