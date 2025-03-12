import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDir
from ui.main_window import MainWindow

def main():
    # Set up proper path handling
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    
    # Create application
    app = QApplication(sys.argv)
    
    # Set up stylesheet if needed
    # with open("ui/style.qss", "r") as f:
    #     app.setStyleSheet(f.read())
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
