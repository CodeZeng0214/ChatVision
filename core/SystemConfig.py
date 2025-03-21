import json
import os
from typing import Dict, Any

class SystemConfig:
    """系统配置管理类，用于加载和保存系统配置"""

    # 配置项的中文显示名称映射
    CONFIG_LABELS = {
        "chat_robot": "聊天机器人设置",
        "init_message": "初始化消息",
        "analyze_max_attempts": "意图分析最大尝试次数",
        
        "plugin_manager": "插件管理器设置",
        "plugins_config_path": "插件配置文件路径",
        
        "chat_interface": "聊天接口设置",
        "api_url": "API接口地址",
        "api_key": "API密钥",
        "model_name": "模型名称"
    }
    
    def __init__(self, config_path="core/System_Configs.json"):
        """初始化系统配置管理器"""
        self.config_path = config_path
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """从配置文件加载配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"配置文件 {self.config_path} 不存在，将使用默认设置")
                return self.get_default_config()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return self.get_default_config()
    
    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            # 确保配置文件目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print(f"配置已保存到 {self.config_path}")
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "chat_robot": {
                "init_message": "You are a chatbot capable of image recognition ",
                "analyze_max_attempts": 3
            },
            "plugin_manager": {
                "plugins_config_path": "plugins/PluginConfigs.json"
            },
            "chat_interface": {
                "api_url": "https://api.chatanywhere.tech/v1",
                "api_key": "sk-AencKA6Oy7WnhukWgquDlbis89fhQ5q4Nz8ba4BvYJUjy8LR",
                "model_name": "gpt-4o-mini"
            }
        }
    
    def get_value(self, section, key, default=None):
        """获取配置项的值"""
        try:
            return self.config[section][key]
        except (KeyError, TypeError):
            return default
    
    def set_value(self, section, key, value):
        """设置配置项的值"""
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
    
    def get_label(self, key):
        """获取配置项的中文显示名称"""
        return self.CONFIG_LABELS.get(key, key)

# 创建一个全局实例
system_config = SystemConfig()
