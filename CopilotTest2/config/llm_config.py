"""
语言模型配置模块
"""
import os
import json
import logging

class LLMConfig:
    """语言模型配置管理类"""
    
    # 默认配置
    _default_config = {
        "base_url": "https://api.openai.com/v1",
        "api_key": "",
        "model": "gpt-3.5-turbo",
        "max_tokens": 2000,
        "temperature": 0.7,
        "max_history": 10
    }
    
    # 当前配置
    _config = _default_config.copy()
    
    @classmethod
    def get_config(cls):
        """获取当前配置"""
        return cls._config.copy()
    
    @classmethod
    def update_config(cls, **kwargs):
        """
        更新配置
        
        Args:
            **kwargs: 需要更新的配置项
        """
        cls._config.update(kwargs)
    
    @classmethod
    def reset_config(cls):
        """重置为默认配置"""
        cls._config = cls._default_config.copy()
    
    @classmethod
    def from_json(cls, json_str):
        """从JSON字符串加载配置"""
        try:
            config = json.loads(json_str)
            cls.update_config(**config)
            return True
        except Exception as e:
            logging.error(f"从JSON加载配置失败: {e}")
            return False
    
    @classmethod
    def to_json(cls):
        """将配置转换为JSON字符串"""
        try:
            return json.dumps(cls._config, indent=2)
        except Exception as e:
            logging.error(f"转换配置到JSON失败: {e}")
            return "{}"
