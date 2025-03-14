"""
目录结构管理工具
确保应用程序所需的目录结构存在
"""
import os
import logging
from config.app_config import AppConfig

def ensure_directory_structure():
    """确保所有必要的目录结构存在"""
    # 创建必要的目录
    directories = [
        # 配置目录
        os.path.join(AppConfig.BASE_DIR, "config", "saved"),
        
        # 插件目录
        os.path.join(AppConfig.PLUGIN_DIR),
        os.path.join(AppConfig.PLUGIN_DIR, "image_recognition"),
        os.path.join(AppConfig.PLUGIN_DIR, "image_description"),
        
        # 资源目录
        os.path.join(AppConfig.BASE_DIR, "resources", "icons"),
        os.path.join(AppConfig.BASE_DIR, "resources", "locales"),
        
        # 临时目录
        AppConfig.TEMP_DIR,
        
        # 用户数据目录
        os.path.join(AppConfig.BASE_DIR, "user_data"),
        os.path.join(AppConfig.BASE_DIR, "user_data", "chat_history"),
        os.path.join(AppConfig.BASE_DIR, "user_data", "models")
    ]
    
    # 创建目录
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logging.debug(f"确保目录存在: {directory}")
        except Exception as e:
            logging.error(f"创建目录失败 {directory}: {e}")
    
    return True

def get_user_data_dir():
    """获取用户数据目录"""
    user_data_dir = os.path.join(AppConfig.BASE_DIR, "user_data")
    os.makedirs(user_data_dir, exist_ok=True)
    return user_data_dir

def get_temp_file_path(filename):
    """获取临时文件路径"""
    return os.path.join(AppConfig.TEMP_DIR, filename)

def is_first_run():
    """检查是否为首次运行"""
    first_run_flag = os.path.join(AppConfig.BASE_DIR, "user_data", ".initialized")
    if not os.path.exists(first_run_flag):
        # 创建首次运行标志文件
        os.makedirs(os.path.dirname(first_run_flag), exist_ok=True)
        with open(first_run_flag, "w") as f:
            f.write("1")
        return True
    return False
