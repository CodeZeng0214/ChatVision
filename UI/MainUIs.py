## 采用claude 3.7 生成

import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                              QScrollArea, QFileDialog, QSplitter)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QPixmap

class MessageWidget(QWidget):
    """Custom widget for displaying a single message (text and/or image)"""
    def __init__(self, username, message, image_path=None, is_user=False, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.setup_ui(username, message, image_path)
        
    def setup_ui(self, username, message, image_path):
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
        
        if image_path:
            image_label = QLabel()
            pixmap = QPixmap(image_path)
            # Resize if too large
            if pixmap.width() > 200:
                pixmap = pixmap.scaledToWidth(200, Qt.SmoothTransformation)
            image_label.setPixmap(pixmap)
            message_layout.addWidget(image_label)
        
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

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_image_path = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("WeChat-like Chat")
        self.resize(400, 600)
        
        # Main widget
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Chat display area (upper part)
        self.chat_area = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_area)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(10)
        
        # Make chat area scrollable
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.chat_area)
        
        # Input area (lower part)
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        
        # Text input
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.setFixedHeight(60)
        
        # Buttons row
        button_layout = QHBoxLayout()
        
        # File selection button
        self.file_button = QPushButton("Select Image")
        self.file_button.clicked.connect(self.select_image)
        
        # Selected file name display
        self.file_label = QLabel("No file selected")
        self.file_label.setWordWrap(True)
        
        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        
        button_layout.addWidget(self.file_button)
        button_layout.addWidget(self.file_label)
        button_layout.addStretch()
        button_layout.addWidget(self.send_button)
        
        input_layout.addWidget(self.message_input)
        input_layout.addLayout(button_layout)
        
        # Add a splitter to allow resizing between chat and input areas
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.scroll_area)
        splitter.addWidget(input_widget)
        splitter.setSizes([400, 200])
        
        main_layout.addWidget(splitter)
        self.setCentralWidget(main_widget)
    
    def select_image(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg);;Videos (*.mp4 *.avi *.mov)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.selected_image_path = selected_files[0]
                file_name = self.selected_image_path.split('/')[-1]
                self.file_label.setText(file_name)
    
    def send_message(self):
        message_text = self.message_input.toPlainText().strip()
        if not message_text and not self.selected_image_path:
            return  # Don't send empty messages
        
        # Add user message to chat
        self.add_message("You", message_text, self.selected_image_path, is_user=True)
        
        # Clear input
        self.message_input.clear()
        self.selected_image_path = None
        self.file_label.setText("No file selected")
        
        # Simulate response (in a real app, this would come from network)
        self.add_message("Friend", "666", is_user=False)
    
    def add_message(self, username, message, image_path=None, is_user=False):
        message_widget = MessageWidget(username, message, image_path, is_user)
        self.chat_layout.addWidget(message_widget)
        
        # Auto scroll to the bottom
        QTimer.singleShot(50, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        scroll_bar = self.scroll_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

def main():
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
