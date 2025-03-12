from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                              QTextEdit, QPushButton, QLabel, 
                              QScrollArea, QFileDialog, QSplitter, 
                              QMenu, QToolButton)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction

from ui.message_widget import MessageWidget

class ChatWindow(QWidget):
    new_task_request = Signal(dict)  # Signal for new task requests
    
    def __init__(self, task_processor):
        super().__init__()
        self.task_processor = task_processor
        self.selected_media_path = None
        self.media_type = None  # 'image', 'video', or None
        self.conversation_history = []
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
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
        self.message_input.setFixedHeight(80)
        
        # Buttons row
        button_layout = QHBoxLayout()
        
        # Media button with dropdown menu
        self.media_button = QToolButton()
        self.media_button.setText("Media")
        media_menu = QMenu()
        
        # Image selection action
        image_action = QAction("Select Image", self)
        image_action.triggered.connect(lambda: self.select_media("image"))
        
        # Video selection action
        video_action = QAction("Select Video", self)
        video_action.triggered.connect(lambda: self.select_media("video"))
        
        # Camera selection action
        camera_action = QAction("Use Camera", self)
        camera_action.triggered.connect(self.open_camera)
        
        media_menu.addAction(image_action)
        media_menu.addAction(video_action)
        media_menu.addAction(camera_action)
        
        self.media_button.setMenu(media_menu)
        self.media_button.setPopupMode(QToolButton.InstantPopup)
        
        # Selected file name display
        self.media_label = QLabel("No media selected")
        self.media_label.setWordWrap(True)
        
        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        
        # New chat button
        self.new_chat_button = QPushButton("New Chat")
        self.new_chat_button.clicked.connect(self.start_new_chat)
        
        button_layout.addWidget(self.media_button)
        button_layout.addWidget(self.media_label)
        button_layout.addStretch()
        button_layout.addWidget(self.new_chat_button)
        button_layout.addWidget(self.send_button)
        
        input_layout.addWidget(self.message_input)
        input_layout.addLayout(button_layout)
        
        # Add a splitter to allow resizing between chat and input areas
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.scroll_area)
        splitter.addWidget(input_widget)
        splitter.setSizes([600, 200])
        
        main_layout.addWidget(splitter)
        
    def select_media(self, media_type):
        file_dialog = QFileDialog(self)
        
        if media_type == "image":
            file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp)")
        elif media_type == "video":
            file_dialog.setNameFilter("Videos (*.mp4 *.avi *.mov *.wmv)")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.selected_media_path = selected_files[0]
                self.media_type = media_type
                file_name = self.selected_media_path.split('/')[-1]
                self.media_label.setText(f"{media_type.capitalize()}: {file_name}")
    
    def open_camera(self):
        self.selected_media_path = "camera"
        self.media_type = "camera"
        self.media_label.setText("Using camera")
        # Signal to the sidebar to show camera preview
        self.task_processor.request_camera_preview()
    
    def send_message(self):
        message_text = self.message_input.toPlainText().strip()
        
        # Don't send if both text and media are empty
        if not message_text and not self.selected_media_path:
            return
        
        # Add user message to chat
        self.add_message("You", message_text, self.selected_media_path, self.media_type, is_user=True)
        
        # Prepare task information
        task_info = {
            "message": message_text,
            "media_path": self.selected_media_path,
            "media_type": self.media_type
        }
        
        # Clear input
        self.message_input.clear()
        self.selected_media_path = None
        self.media_type = None
        self.media_label.setText("No media selected")
        
        # Process the task
        self.new_task_request.emit(task_info)
        
        # Add a brief delay before showing AI response
        QTimer.singleShot(1000, lambda: self.handle_ai_response(task_info))
    
    def handle_ai_response(self, task_info):
        """Handle AI response to user query"""
        # This method would normally wait for the task processor to complete
        # but for now we'll just show a placeholder response
        
        # In a real implementation, the task processor would emit a signal with the results
        # that would be connected to this method or similar
        
        # For now, just add a placeholder response
        self.add_message("AI Assistant", "I've processed your request. Check the sidebar for results.", is_user=False)
    
    def add_message(self, username, message, media_path=None, media_type=None, is_user=False):
        message_widget = MessageWidget(username, message, media_path, media_type, is_user)
        self.chat_layout.addWidget(message_widget)
        
        # Save to conversation history
        self.conversation_history.append({
            "username": username,
            "message": message,
            "media_path": media_path,
            "media_type": media_type,
            "is_user": is_user
        })
        
        # Auto scroll to the bottom
        QTimer.singleShot(50, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        scroll_bar = self.scroll_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())
        
    def start_new_chat(self):
        # Clear chat history
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        self.conversation_history = []
        self.message_input.clear()
        self.selected_media_path = None
        self.media_type = None
        self.media_label.setText("No media selected")
