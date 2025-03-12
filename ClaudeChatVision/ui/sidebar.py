from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                              QLabel, QScrollArea, QPushButton,
                              QComboBox, QStackedWidget, QFileDialog,
                              QLineEdit, QFormLayout)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtMultimedia import QMediaPlayer, QCamera, QMediaCaptureSession, QVideoFrame, QVideoSink

class MediaDisplayWidget(QWidget):
    """Widget for displaying images or video"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Stacked widget to switch between different media types
        self.stack = QStackedWidget()
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #d0d0d0;")
        self.stack.addWidget(self.image_label)
        
        # Video display
        self.video_widget = QVideoWidget()
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.stack.addWidget(self.video_widget)
        
        # Camera display
        self.camera_widget = QWidget()
        camera_layout = QVBoxLayout(self.camera_widget)
        
        self.camera_view = QVideoWidget()
        self.camera_capture_session = QMediaCaptureSession()
        self.camera_capture_session.setVideoOutput(self.camera_view)
        
        camera_controls = QHBoxLayout()
        self.camera_select = QComboBox()
        self.camera_select.addItem("Default Camera")  # In a real app, you'd list available cameras
        self.camera_start_btn = QPushButton("Start Camera")
        self.camera_start_btn.clicked.connect(self.toggle_camera)
        
        camera_controls.addWidget(QLabel("Camera:"))
        camera_controls.addWidget(self.camera_select)
        camera_controls.addWidget(self.camera_start_btn)
        
        camera_layout.addWidget(self.camera_view)
        camera_layout.addLayout(camera_controls)
        
        self.stack.addWidget(self.camera_widget)
        
        layout.addWidget(self.stack)
        
        # Camera is initially stopped
        self.camera = None
        self.camera_running = False
        
    def display_image(self, image_path):
        pixmap = QPixmap(image_path)
        self.image_label.setPixmap(pixmap.scaled(
            self.image_label.width(), 
            self.image_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))
        self.stack.setCurrentIndex(0)  # Switch to image display
        
    def play_video(self, video_path):
        self.media_player.setSource(video_path)
        self.media_player.play()
        self.stack.setCurrentIndex(1)  # Switch to video display
    
    def toggle_camera(self):
        if self.camera_running:
            # Stop camera
            if self.camera:
                self.camera.stop()
                self.camera = None
            self.camera_running = False
            self.camera_start_btn.setText("Start Camera")
        else:
            # Start camera
            self.camera = QCamera()
            self.camera_capture_session.setCamera(self.camera)
            self.camera.start()
            self.camera_running = True
            self.camera_start_btn.setText("Stop Camera")
        
        self.stack.setCurrentIndex(2)  # Switch to camera display
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # If showing an image, rescale it when the widget is resized
        if self.stack.currentIndex() == 0:
            pixmap = self.image_label.pixmap()
            if pixmap and not pixmap.isNull():
                self.image_label.setPixmap(pixmap.scaled(
                    self.image_label.width(), 
                    self.image_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                ))

    @Slot(str)
    def play_video_from_chat(self, video_path):
        """Play video when requested from chat message"""
        self.play_video(video_path)


class ParameterInputWidget(QWidget):
    """Widget for collecting additional parameters from user"""
    parameter_submitted = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.param_widgets = {}
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.header_label = QLabel("Additional Information Required")
        self.header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.description_label = QLabel("")
        
        # Form layout for parameter inputs
        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)
        
        # Submit button
        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_parameters)
        
        layout.addWidget(self.header_label)
        layout.addWidget(self.description_label)
        layout.addWidget(self.form_widget)
        layout.addWidget(self.submit_button)
        layout.addStretch()
        
        # Initially hide the widget
        self.setVisible(False)
        
    def set_parameters(self, param_list, description="Please provide the following information:"):
        # Clear existing parameters
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        self.param_widgets = {}
        self.description_label.setText(description)
        
        # Add new parameters
        for param in param_list:
            param_name = param["name"]
            param_label = param.get("label", param_name)
            param_type = param.get("type", "text")
            
            label = QLabel(param_label)
            
            if param_type == "image_selector":
                widget = QPushButton("Select Image")
                widget.clicked.connect(lambda _, p=param_name: self.select_image(p))
                self.param_widgets[param_name] = {"type": param_type, "widget": widget, "value": None}
            elif param_type == "camera_selector":
                widget = QComboBox()
                widget.addItem("Default Camera")
                self.param_widgets[param_name] = {"type": param_type, "widget": widget, "value": "Default Camera"}
            else:  # Default to text input
                widget = QLineEdit()
                if "default" in param:
                    widget.setText(str(param["default"]))
                self.param_widgets[param_name] = {"type": param_type, "widget": widget, "value": param.get("default", "")}
            
            self.form_layout.addRow(label, widget)
        
        self.setVisible(True)
    
    def select_image(self, param_name):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                self.param_widgets[param_name]["value"] = file_path
                self.param_widgets[param_name]["widget"].setText(file_path.split('/')[-1])
    
    def submit_parameters(self):
        # Collect parameter values
        params = {}
        for param_name, param_data in self.param_widgets.items():
            if param_data["type"] == "image_selector":
                params[param_name] = param_data["value"]
            elif param_data["type"] == "camera_selector":
                params[param_name] = param_data["widget"].currentText()
            else:  # Text input
                params[param_name] = param_data["widget"].text()
        
        self.parameter_submitted.emit(params)
        self.setVisible(False)


class Sidebar(QWidget):
    """Sidebar widget for displaying results and parameter inputs"""
    parameter_submitted = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title label
        title_label = QLabel("Results & Preview")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        # Media display
        self.media_display = MediaDisplayWidget()
        
        # Results text display
        self.results_label = QLabel("Processing Results:")
        self.results_text = QLabel("No results yet.")
        self.results_text.setWordWrap(True)
        self.results_text.setStyleSheet("background-color: #f9f9f9; padding: 8px; border-radius: 4px;")
        
        # Create scroll area for results
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.addWidget(self.results_text)
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        
        # Parameter input widget
        self.param_input = ParameterInputWidget()
        self.param_input.parameter_submitted.connect(self.on_parameter_submitted)
        
        layout.addWidget(title_label)
        layout.addWidget(self.media_display, 3)  # Stretch factor 3
        layout.addWidget(self.results_label)
        layout.addWidget(scroll_area, 2)  # Stretch factor 2
        layout.addWidget(self.param_input, 1)  # Stretch factor 1
    
    @Slot(dict)
    def display_result(self, result_data):
        """Display results in the sidebar"""
        # Handle image results
        if "image_path" in result_data:
            self.media_display.display_image(result_data["image_path"])
        
        # Handle video results
        elif "video_path" in result_data:
            self.media_display.play_video(result_data["video_path"])
        
        # Handle camera feed
        elif "camera" in result_data:
            self.media_display.toggle_camera()
        
        # Display text results
        if "text" in result_data:
            self.results_text.setText(result_data["text"])
    
    @Slot(list, str)
    def show_parameter_input(self, param_list, description=""):
        """Show parameter input fields when additional info is needed"""
        self.param_input.set_parameters(param_list, description)
    
    def on_parameter_submitted(self, params):
        """Forward parameter submission to the task processor"""
        self.parameter_submitted.emit(params)

    def connect_video_signals(self, chat_window):
        """Connect video play signals from message widgets in chat"""
        # This would need to be called after chat window is initialized
        # For now, we'll handle this through the task processor
        pass
