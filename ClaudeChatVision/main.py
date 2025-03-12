import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDir
from ui.main_window import MainWindow

def main():
    """ChatVision应用程序的主入口点
    
    设置Qt应用程序环境，处理路径配置，创建主窗口并启动应用程序事件循环。
    
    应用程序架构:
    - UI层: 管理用户交互(main_window, chat_window, sidebar)
    - 核心层: 处理任务并管理LLM集成(task_processor, llm_client)
    - 数据层: 处理聊天历史和配置的持久化
    
    主函数负责初始化应用程序，确保工作目录正确设置，并启动主事件循环。
    """
    # 设置正确的路径处理
    # 这确保了无论应用程序如何启动，相对路径都能正常工作
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    
    # 创建Qt应用程序实例
    # 这是管理事件循环和应用程序生命周期的核心对象
    app = QApplication(sys.argv)
    
    # 可选：设置应用程序样式
    # 已注释掉，但可用于自定义应用程序外观
    # with open("ui/style.qss", "r") as f:
    #     app.setStyleSheet(f.read())
    
    # 创建并显示主应用程序窗口
    # MainWindow负责所有UI组件初始化和信号连接
    window = MainWindow()
    window.show()
    
    # 启动应用程序事件循环
    # 这会阻塞直到应用程序退出
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
