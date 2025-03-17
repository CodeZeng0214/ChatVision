### Plugin基类定义
from typing import Dict, Any, Callable, List
import json

class Plugin:
    """参数解释：\n
    - plugin_name: str 插件名称\n
    - is_load: bool 是否加载\n
    - enable: bool 是否启用\n
    - module_path: str 模块路径\n
    - class_name: str 类名\n
    - description: str 描述\n
    - parameters: List[Dict[str, Any]] 参数列表\n
    - execute: Callable[[Dict[str, Any]], Any] 执行函数\n
    - result: Any 执行结果\n
    """
    def __init__(self, plugin_name: str, parameters: List[Dict[str, Any]], description: str = ""):

        self.plugin_name = plugin_name
        self.is_load = True
        self.enable = True
        self.module_path = ""
        self.class_name = ""
        self.description = description
        self.parameters = parameters
        self.execute = None
        self.result = None
        
        
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
        data[self.plugin_name] = {
            "is_load": self.is_load,
            "enable": self.enable,
            "module_path": self.module_path,
            "class_name": self.class_name,
            "description": self.description,
            "parameters": self.parameters
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    
    def get_parameter_default(self, param_name):
        """获取参数的默认值"""
        for param in self.parameters:
            if param["name"] == param_name:
                return param.get("default", None)
        return None
    
    def set_parameter_default(self, param_name, value):
        """设置参数的默认值"""
        for param in self.parameters:
            if param["name"] == param_name:
                param["default"] = value
                return True
        return False
