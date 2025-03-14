"""
配置管理模块，用于保存和加载应用配置
"""
import os
import json
import logging
from config.app_config import AppConfig
from config.llm_config import LLMConfig

class ConfigManager:
    """配置管理器"""
    
    @classmethod
    def save_config(cls):
        """保存所有配置到文件"""
        config_dir = os.path.join(AppConfig.BASE_DIR, "config", "saved")
        os.makedirs(config_dir, exist_ok=True)
        
        # 保存应用配置
        app_config_path = os.path.join(config_dir, "app_config.json")
        cls._save_app_config(app_config_path)
        
        # 保存LLM配置
        llm_config_path = os.path.join(config_dir, "llm_config.json")
        cls._save_llm_config(llm_config_path)
        
        logging.info("已保存配置")
        return True
    
    @classmethod
    def load_config(cls):
        """从文件加载所有配置"""
        config_dir = os.path.join(AppConfig.BASE_DIR, "config", "saved")
        if not os.path.exists(config_dir):
            logging.warning("未找到保存的配置")
            return False
        
        # 加载应用配置
        app_config_path = os.path.join(config_dir, "app_config.json")
        cls._load_app_config(app_config_path)
        
        # 加载LLM配置
        llm_config_path = os.path.join(config_dir, "llm_config.json")
        cls._load_llm_config(llm_config_path)
        
        logging.info("已加载配置")
        return True
    
    @classmethod
    def _save_app_config(cls, config_path):
        """保存应用配置到文件"""
        try:
            # 获取需要保存的配置项
            config = {
                "DEFAULT_WINDOW_WIDTH": AppConfig.DEFAULT_WINDOW_WIDTH,
                "DEFAULT_WINDOW_HEIGHT": AppConfig.DEFAULT_WINDOW_HEIGHT,
                "MINIMIZE_TO_TRAY": getattr(AppConfig, "MINIMIZE_TO_TRAY", True)
            }
            
            # 保存到文件
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
                
        except Exception as e:
            logging.error(f"保存应用配置失败: {e}")
    
    @classmethod
    def _save_llm_config(cls, config_path):
        """保存LLM配置到文件"""
        try:
            # 获取当前LLM配置
            config = LLMConfig.get_config()
            
            # 保存到文件
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
                
        except Exception as e:
            logging.error(f"保存LLM配置失败: {e}")
    
    @classmethod
    def _load_app_config(cls, config_path):
        """从文件加载应用配置"""
        if not os.path.exists(config_path):
            return
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 设置应用配置
            if "DEFAULT_WINDOW_WIDTH" in config:
                AppConfig.DEFAULT_WINDOW_WIDTH = config["DEFAULT_WINDOW_WIDTH"]
            if "DEFAULT_WINDOW_HEIGHT" in config:
                AppConfig.DEFAULT_WINDOW_HEIGHT = config["DEFAULT_WINDOW_HEIGHT"]
            if "MINIMIZE_TO_TRAY" in config:
                AppConfig.MINIMIZE_TO_TRAY = config["MINIMIZE_TO_TRAY"]
                
        except Exception as e:
            logging.error(f"加载应用配置失败: {e}")
    
    @classmethod
    def _load_llm_config(cls, config_path):
        """从文件加载LLM配置"""
        if not os.path.exists(config_path):
            return
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新LLM配置
            LLMConfig.update_config(**config)
                
        except Exception as e:
            logging.error(f"加载LLM配置失败: {e}")
