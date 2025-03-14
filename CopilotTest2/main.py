import sys
import os
import logging
import tempfile
import argparse

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))
sys.path.append(current_dir)

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.chat_engine import ChatEngine
from plugins.plugin_manager import PluginManager
from config.app_config import AppConfig
from utils.error_handler import ErrorHandler
from utils.dir_structure import ensure_directory_structure

def main(debug=False, log_level=logging.INFO, no_gui=False):
    """
    主入口函数
    
    Args:
        debug: 是否启用调试模式
        log_level: 日志级别
        no_gui: 是否为无GUI模式
    """
    # 启用全局异常处理
    ErrorHandler.setup_exception_handling()
    
    # 确保目录结构存在
    ensure_directory_structure()
    
    # 确保临时目录存在
    temp_dir = os.path.join(tempfile.gettempdir(), "chatvision")
    os.makedirs(temp_dir, exist_ok=True)
    AppConfig.TEMP_DIR = temp_dir
    
    # 配置日志
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(temp_dir, "chatvision.log"))
        ]
    )
    
    # 设置调试模式
    AppConfig.DEBUG_MODE = debug
    if debug:
        logging.info("调试模式已启用")
    
    logging.info(f"启动 {AppConfig.APP_NAME} v{AppConfig.APP_VERSION}")
    
    # 初始化应用配置
    AppConfig.init()
    
    # 如果是无GUI模式，处理命令行任务然后退出
    if no_gui:
        return process_cli_tasks()
    
    # 初始化 Qt 应用
    app = QApplication(sys.argv)
    app.setApplicationName(AppConfig.APP_NAME)
    
    try:
        # 初始化插件管理器
        logging.info("加载插件...")
        plugin_manager = PluginManager()
        plugin_manager.plugin_paths = AppConfig.PLUGIN_PATHS
        plugin_manager.load_plugins()
        
        # 初始化聊天引擎
        logging.info("初始化聊天引擎...")
        chat_engine = ChatEngine(plugin_manager)
        
        # 创建并显示主窗口
        logging.info("创建主窗口...")
        window = MainWindow(chat_engine, plugin_manager)
        window.resize(AppConfig.DEFAULT_WINDOW_WIDTH, AppConfig.DEFAULT_WINDOW_HEIGHT)
        window.show()
        
        # 设置应用样式表
        try:
            with open(os.path.join(current_dir, "resources", "style.qss"), "r") as f:
                app.setStyleSheet(f.read())
        except Exception as e:
            logging.warning(f"未能加载样式表文件: {str(e)}")
        
        logging.info("应用程序启动成功")
        return app.exec()
        
    except Exception as e:
        ErrorHandler.report_error(e, "应用启动失败", send_report=True)
        sys.exit(1)

def process_cli_tasks():
    """处理命令行任务"""
    logging.info("运行在CLI模式下，处理任务后退出")
    
    # TODO: 实现CLI模式下的任务处理
    # 这部分代码可以在后续开发中添加，用于处理批量任务等
    
    return 0

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="ChatVision - 图像识别聊天机器人")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--log", default="info", choices=["debug", "info", "warning", "error"], 
                        help="日志级别")
    parser.add_argument("--no-gui", action="store_true", help="无GUI模式")
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = {
        "debug": logging.DEBUG,
        "info": logging.INFO, 
        "warning": logging.WARNING,
        "error": logging.ERROR
    }.get(args.log, logging.INFO)
    
    # 启动应用
    sys.exit(main(debug=args.debug, log_level=log_level, no_gui=args.no_gui))
