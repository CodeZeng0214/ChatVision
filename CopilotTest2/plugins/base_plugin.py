from abc import ABC, abstractmethod

class BasePlugin(ABC):
    """插件基类"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.description = "基础插件"
        self.enabled = True
        self.config = {}
    
    @abstractmethod
    def process(self, parameters):
        """处理任务的主要方法"""
        pass
    
    @abstractmethod
    def get_required_parameters(self):
        """获取插件需要的参数列表"""
        pass
    
    def get_config_ui(self):
        """获取配置界面"""
        return None
    
    def get_task_types(self):
        """获取插件支持的任务类型列表"""
        return []
    
    def set_config(self, config):
        """设置插件配置"""
        self.config.update(config)
    
    def enable(self):
        """启用插件"""
        self.enabled = True
    
    def disable(self):
        """禁用插件"""
        self.enabled = False
    
    def is_enabled(self):
        """检查插件是否启用"""
        return self.enabled
