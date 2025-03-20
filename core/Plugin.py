### Plugin基类定义
from typing import Dict, Any, Callable, List
import json
import os
import inspect

class Plugin:
    """参数解释：\n
    - plugin_name: str 插件名称\n
    - is_load: bool 是否加载，默认为True\n
    - enable: bool 是否启用，默认为True\n
    - module_path: str 模块路径\n
    - class_name: str 类名\n
    - description: str 描述\n
    - parameters: List[Dict[str, Any]] 参数列表\n
    - execute: Callable[[Dict[str, Any]], Any] 执行函数\n
    - result: Any 执行结果\n
    """
    def __init__(self, plugin_name: str, description: str = "", parameters: List[Dict[str, Any]] = []):

        self.plugin_name = plugin_name
        self.is_load = True
        self.enable = True
        self.module_path = self.get_module_path()
        self.class_name = self.get_class_name()
        self.description = description
        self.parameters = parameters
        self.execute = None
        self.results = None
        
    @classmethod
    def get_class_name(cls)->str:
        """获取类名"""
        return cls.__name__
    
    def get_module_path(self)->str:
        """获取模块路径"""
        # 使用inspect获取调用类所在的模块
        module = inspect.getmodule(self.__class__)
        # 获取模块名
        module_name = module.__name__
        return module_name
     
    def describe_plugin(self):
        """为插件生成描述"""
        parameter_description = []
        for parameter in self.parameters:
            if parameter.get("required", False):
                parameter_description.append(f"{parameter['name']} (necessary): {parameter['description']}")
            else:
                parameter_description.append(f"{parameter['name']} (unnecessary): {parameter['description']}")
        parameter_description = '\n'.join(parameter_description)
        return f"-- {self.plugin_name}: {self.description},\nparameters: \n{parameter_description}"
    
    def update_info_from_config(self, config: Dict[str, Any]):
        """从配置文件中更新插件的信息"""
        self.is_load = config.get("is_load", True)
        self.enable = config.get("enable", True)
        self.module_path = config.get("module_path", "")
        self.class_name = config.get("class_name", "")
        self.description = config.get("description", "")
        self.parameters = config.get("parameters", [])
    
    def write_plugin_to_config(self, config_path: str):
        """将插件信息写入配置文件（添加）"""
        # 1. 读取原数据
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 2. 添加新数据
        data[self.plugin_name] = self.get_plugin_config()
        # 3. 写入文件
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    def get_plugin_config(self)->Dict[str, Any]:
        """获取插件配置
        - 返回值: Dict[str, Any] 插件配置字典
        """
        return {
            "is_load": self.is_load,
            "enable": self.enable,
            "module_path": self.module_path,
            "class_name": self.class_name,
            "description": self.description,
            "parameters": self.parameters
        }

    def refresh(self):
        """刷新插件的执行结果"""
        self.results = None
