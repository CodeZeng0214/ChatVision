## 采用 GPT4o 生成

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QLabel, QHBoxLayout, QFileDialog, QScrollArea, QTextBrowser
from PySide6.QtGui import QPixmap, QTextCursor
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChatVision")
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Chat display area
        self.chat_display = QTextBrowser()
        self.chat_display.setReadOnly(True)
        main_layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        self.input_text = QTextEdit()
        self.input_text.setFixedHeight(50)
        input_layout.addWidget(self.input_text)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        self.file_button = QPushButton("Select Image/Video")
        self.file_button.clicked.connect(self.select_file)
        input_layout.addWidget(self.file_button)
        
        main_layout.addLayout(input_layout)
        
        # Central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Variable to store selected file path
        self.selected_file_path = None
    
    def send_message(self):
        # Get the text from the input field
        message = self.input_text.toPlainText()
        
        # Check if there is a message or a selected file to send
        if message or self.selected_file_path:
            combined_message = message
            if self.selected_file_path:
                if combined_message:
                    combined_message += "<br>"
                combined_message += self.format_file_message(self.selected_file_path)
                self.selected_file_path = None  # Clear the selected file path after sending
            self.display_message("User", combined_message)
            self.input_text.clear()
    
    def select_file(self):
        # Open file dialog to select an image or video file
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilters(["Images (*.png *.xpm *.jpg)", "Videos (*.mp4 *.avi)"])
        if file_dialog.exec():
            # Store the selected file path
            self.selected_file_path = file_dialog.selectedFiles()[0]
            # Display the selected file path to the user
            self.input_text.setPlainText(f"Selected file: {self.selected_file_path}")
    
    def format_file_message(self, file_path):
        # Format the content if it is a file
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            return f'<img src="{file_path}" width="200">'
        else:
            return f'<a href="{file_path}">Video File</a>'
    
    def display_message(self, sender, content, is_file=False):
        # Create HTML for the message
        message_html = f"""
        <div style="margin: 10px;">
            <b>{sender}:</b><br>
            {content}
        </div>
        """
        # Append the message to the chat display
        self.chat_display.append(message_html)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
