import os
import tempfile

class AppConfig:
    """应用程序全局配置"""
    
    # 应用信息
    APP_NAME = "ChatVision"
    APP_VERSION = "0.1.0"
    
    # 文件路径
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    TEMP_DIR = os.path.join(tempfile.gettempdir(), "chatvision")
    PLUGIN_DIR = os.path.join(BASE_DIR, "plugins")
    
    # UI配置
    DEFAULT_WINDOW_WIDTH = 1200
    DEFAULT_WINDOW_HEIGHT = 800
    MINIMIZE_TO_TRAY = True
    
    # 插件相关配置
    PLUGIN_PATHS = [
        os.path.join(PLUGIN_DIR, "image_recognition"),
        os.path.join(PLUGIN_DIR, "image_description")
    ]
    
    # 创建必要的目录
    @classmethod
    def init(cls):
        """初始化应用配置"""
        # 创建临时目录
        os.makedirs(cls.TEMP_DIR, exist_ok=True)
        
        # 创建插件目录
        for path in cls.PLUGIN_PATHS:
            os.makedirs(path, exist_ok=True)
        
        # 尝试加载保存的配置
        try:
            from config.config_manager import ConfigManager
            ConfigManager.load_config()
        except ImportError:
            pass
        
        return True
