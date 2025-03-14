# 主程序 - GUI版本
import sys
from PySide6.QtWidgets import QApplication
from gui.MainWindow import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()