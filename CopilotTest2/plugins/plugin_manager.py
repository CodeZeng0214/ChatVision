import os
import importlib
import importlib.util
import inspect
import sys
import logging
from plugins.base_plugin import BasePlugin

class PluginManager:
    """插件管理器，负责加载和管理插件"""
    
    def __init__(self):
        self.plugins = {}  # 存储已加载的插件: {plugin_name: plugin_instance}
        self.task_plugins = {}  # 任务类型到插件的映射: {task_type: [plugin_instances]}
        self.plugin_paths = [
            os.path.join(os.path.dirname(__file__), "image_recognition"),
            os.path.join(os.path.dirname(__file__), "image_description")
        ]
    
    def load_plugins(self):
        """加载所有插件"""
        # 确保插件目录存在
        for path in self.plugin_paths:
            os.makedirs(path, exist_ok=True)
            
        # 加载内置插件
        self._load_builtin_plugins()
            
        # 从插件目录加载
        for path in self.plugin_paths:
            self._load_plugins_from_directory(path)
            
        logging.info(f"已加载 {len(self.plugins)} 个插件")
        
        # 输出已加载的插件列表
        if self.plugins:
            plugin_names = [p.name for p in self.plugins.values()]
            logging.info(f"已加载的插件: {', '.join(plugin_names)}")
        
        # 输出任务到插件的映射
        for task_type, plugins in self.task_plugins.items():
            plugin_names = [p.name for p in plugins]
            logging.info(f"任务类型 {task_type} 支持的插件: {', '.join(plugin_names)}")
    
    def _load_builtin_plugins(self):
        """加载内置插件"""
        # 这里手动加载内置插件
        builtin_plugins = [
            ("plugins.image_recognition.yolo_plugin", "YoloPlugin"),
            ("plugins.image_description.blip_plugin", "BlipPlugin"),
            ("plugins.image_recognition.pose_plugin", "PosePlugin"),
            ("plugins.image_recognition.batch_plugin", "BatchProcessingPlugin"),
            ("plugins.image_recognition.realtime_plugin", "RealtimeProcessingPlugin")
        ]
        
        for module_path, class_name in builtin_plugins:
            try:
                module = importlib.import_module(module_path)
                plugin_class = getattr(module, class_name)
                plugin_instance = plugin_class()
                self._register_plugin(plugin_instance)
                logging.info(f"已加载内置插件: {plugin_instance.name}")
            except (ImportError, AttributeError) as e:
                logging.warning(f"无法加载内置插件 {module_path}.{class_name}: {e}")
    
    def _load_plugins_from_directory(self, directory):
        """从指定目录加载插件"""
        if not os.path.exists(directory):
            logging.warning(f"插件目录不存在: {directory}")
            return
            
        # 将目录添加到搜索路径
        if directory not in sys.path:
            sys.path.append(directory)
        
        # 搜索Python文件
        for filename in os.listdir(directory):
            if filename.endswith(".py") and not filename.startswith("__"):
                try:
                    module_name = filename[:-3]  # 去掉.py
                    module_path = os.path.join(directory, filename)
                    
                    # 动态导入模块
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    if not spec:
                        logging.error(f"无法加载插件模块: {module_path}")
                        continue
                        
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # 查找模块中的插件类
                    found_plugin = False
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BasePlugin) and 
                            obj != BasePlugin):
                            try:
                                # 实例化并注册插件
                                plugin_instance = obj()
                                self._register_plugin(plugin_instance)
                                logging.info(f"已加载插件: {name} 从 {filename}")
                                found_plugin = True
                            except Exception as e:
                                logging.error(f"实例化插件 {name} 失败: {e}")
                    
                    if not found_plugin:
                        logging.warning(f"在 {filename} 中没有找到有效的插件类")
                except Exception as e:
                    logging.error(f"加载插件 {filename} 失败: {e}")
    
    def _register_plugin(self, plugin):
        """注册插件"""
        if not isinstance(plugin, BasePlugin):
            logging.warning(f"尝试注册非插件对象: {plugin}")
            return
            
        self.plugins[plugin.name] = plugin
        
        # 注册任务类型
        task_types = plugin.get_task_types()
        if task_types:
            for task_type in task_types:
                if task_type not in self.task_plugins:
                    self.task_plugins[task_type] = []
                self.task_plugins[task_type].append(plugin)
    
    def get_plugin_by_name(self, name):
        """根据名称获取插件"""
        return self.plugins.get(name)
    
    def get_plugins(self):
        """获取所有插件"""
        return list(self.plugins.values())
    
    def get_plugin_for_task(self, task_type):
        """获取能处理指定任务类型的插件"""
        plugins = self.task_plugins.get(task_type, [])
        # 返回第一个启用的插件
        for plugin in plugins:
            if plugin.is_enabled():
                return plugin
        return None
    
    def get_plugins_for_task(self, task_type):
        """获取能处理指定任务类型的所有插件"""
        return [p for p in self.task_plugins.get(task_type, []) if p.is_enabled()]
    
    def enable_plugin(self, name):
        """启用插件"""
        plugin = self.get_plugin_by_name(name)
        if plugin:
            plugin.enable()
            return True
        return False
    
    def disable_plugin(self, name):
        """禁用插件"""
        plugin = self.get_plugin_by_name(name)
        if plugin:
            plugin.disable()
            return True
        return False
    
    def configure_plugin(self, name, config):
        """配置插件"""
        plugin = self.get_plugin_by_name(name)
        if plugin:
            plugin.set_config(config)
            return True
        return False
