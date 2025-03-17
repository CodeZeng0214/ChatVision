### 插件管理器

import os
import json
import importlib
import inspect
from typing import Dict, Callable, Any, List
from core.Plugin import Plugin
import sys
from core.AuxiliaryFunction import PathCheck

### ========== 插件注册与管理 ========== ###
class PluginManager:
    """
    插件注册管理器：支持动态注册与调用插件。
    """
    def __init__(self):
        self.plugins = {}  # 插件字典，键为插件名称，值为Plugin对象
        self.all_available_plugins = {}  # 存储配置文件中所有可用的插件
        self.plugins_config_path = "plugins/PluginConfigs.json"  # 插件配置的默认路径
        
        # 确保配置文件目录存在
        PathCheck(self.plugins_config_path)
        
        # 尝试从配置文件中加载插件
        try:
            self.load_plugins_from_config(self.plugins_config_path)
        except Exception as e:
            print(f"从配置文件加载插件失败: {e}")
            # 如果加载失败，尝试扫描并创建默认配置
            self._discover_plugin_classes()
            self.write_plugins_to_config(self.plugins_config_path)
    
    def _discover_plugin_classes(self):
        """扫描插件模块目录，发现所有Plugin子类并创建配置项"""
        print("开始扫描插件模块...")
        config = {}
        try:
            # 添加插件目录到Python路径
            plugin_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'plugins')
            if not os.path.exists(plugin_dir):
                os.makedirs(plugin_dir)
                
            if plugin_dir not in sys.path:
                sys.path.append(plugin_dir)
            
            # 遍历插件目录下所有.py文件
            for filename in os.listdir(plugin_dir):
                if filename.endswith(".py") and not filename.startswith("__"):
                    module_name = filename[:-3]  # 去掉.py后缀
                    try:
                        # 导入模块
                        module = importlib.import_module(f"plugins.{module_name}")
                        
                        # 查找模块中的Plugin子类并收集信息
                        for class_name, obj in inspect.getmembers(module):
                            if (inspect.isclass(obj) and 
                                issubclass(obj, Plugin) and 
                                obj != Plugin):  # 排除基类本身
                                try:
                                    # 实例化插件以获取信息
                                    plugin_instance = obj()
                                    
                                    # 收集配置信息
                                    config[plugin_instance.plugin_name] = {
                                        'enable': True,
                                        'is_load': True,  # 添加默认为True的is_load配置项
                                        'module_path': f"plugins.{module_name}",
                                        'class_name': class_name,
                                        'description': plugin_instance.description,
                                        'parameters': plugin_instance.parameters
                                    }
                                    
                                    # 注册插件
                                    self.plugins[plugin_instance.plugin_name] = plugin_instance
                                    print(f"发现插件: {plugin_instance.plugin_name} ({class_name})")
                                except Exception as e:
                                    print(f"收集插件信息失败 {class_name}: {e}")
                    except Exception as e:
                        print(f"加载模块 {module_name} 失败: {e}")
            
            print(f"扫描完成，共发现 {len(config)} 个插件")
            return config
        except Exception as e:
            print(f"扫描插件类时出错: {e}")
            return {}
    
    def register_plugin(self, plugin: Plugin):
        """注册一个插件实例"""
        self.plugins[plugin.plugin_name] = plugin
    
    def load_plugins_from_config(self, plugins_config_path: str):
        """从配置文件中加载插件"""
        if not os.path.exists(plugins_config_path):
            # 如果配置文件不存在，创建默认配置
            print(f"配置文件 {plugins_config_path} 不存在，将扫描插件并创建配置")
            config = self._discover_plugin_classes()
            self.write_plugins_to_config(plugins_config_path)
            return
        
        # 从配置文件加载
        print(f"正在从配置文件加载插件: {plugins_config_path}")
        try:
            with open(plugins_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 清空当前插件，按配置重新加载
            self.plugins.clear()
            self.all_available_plugins = config  # 保存所有配置项
            
            # 根据配置动态导入和实例化插件
            for plugin_name, plugin_config in config.items():
                # 使用is_load来控制是否加载插件
                if plugin_config.get('is_load', True):  # 默认加载
                    try:
                        # 从配置获取模块路径和类名
                        module_path = plugin_config.get('module_path')
                        class_name = plugin_config.get('class_name')
                        
                        if not module_path or not class_name:
                            print(f"插件配置缺少module_path或class_name: {plugin_name}")
                            continue
                        
                        # 动态导入模块
                        module = importlib.import_module(module_path)
                        
                        # 获取插件类
                        plugin_class = getattr(module, class_name)
                        
                        # 实例化插件类
                        plugin_instance = plugin_class()
                        
                        # 从配置更新插件属性
                        if 'description' in plugin_config and plugin_config['description']:
                            plugin_instance.description = plugin_config['description']
                            
                        # 更新参数默认值
                        if 'parameters' in plugin_config:
                            # 根据名称匹配参数并更新默认值
                            config_params = {param.get('name'): param for param in plugin_config['parameters'] 
                                            if 'name' in param}
                            
                            for param in plugin_instance.parameters:
                                param_name = param.get('name')
                                if param_name in config_params:
                                    config_param = config_params[param_name]
                                    # 复制默认值
                                    if 'default' in config_param:
                                        param['default'] = config_param['default']
                        
                        # 注册插件并设置enable状态
                        self.register_plugin(plugin_instance)
                        # 使用配置中的enable值更新插件启用状态
                        plugin_instance.enable = plugin_config.get('enable', True)
                        print(f"已加载插件: {plugin_name}, 启用状态: {plugin_instance.enable}")
                    except Exception as e:
                        print(f"加载插件失败 {plugin_name}: {e}")
                else:
                    print(f"插件已配置为不加载: {plugin_name}")
            
            print(f"加载完成，共启用 {len(self.plugins)} 个插件")
        except Exception as e:
            print(f"加载插件配置失败: {e}")
            raise
    
    # 将插件配置写入配置文件
    def write_plugins_to_config(self, plugins_config_path: str = None):
        """将插件配置写入配置文件"""
        if plugins_config_path is None:
            plugins_config_path = self.plugins_config_path
        
        # 确保配置文件目录存在
        os.makedirs(os.path.dirname(plugins_config_path), exist_ok=True)
        
        # 如果没有现有配置文件，创建默认配置
        if not os.path.exists(plugins_config_path):
            # 扫描插件目录以创建初始配置
            config = self._discover_plugin_classes()
        else:
            # 读取现有配置
            try:
                with open(plugins_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception:
                config = {}
                
            # 更新配置中插件的当前状态
            for plugin_name, plugin in self.plugins.items():
                if plugin_name in config:
                    # 更新现有插件的启用状态
                    config[plugin_name]['enable'] = plugin.enable
                    # 如果没有is_load键，添加默认为True
                    if 'is_load' not in config[plugin_name]:
                        config[plugin_name]['is_load'] = True
                else:
                    # 为新插件创建配置项
                    # 从插件实例获取模块和类名信息
                    class_info = plugin.__class__.__module__
                    class_name = plugin.__class__.__name__
                    
                    config[plugin_name] = {
                        'enable': plugin.enable,
                        'is_load': True,  # 新插件默认加载
                        'module_path': class_info,
                        'class_name': class_name,
                        'description': plugin.description,
                        'parameters': plugin.parameters
                    }
        
        # 写入文件
        try:
            with open(plugins_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            print(f"已将 {len(config)} 个插件配置写入 {plugins_config_path}")
        except Exception as e:
            print(f"写入插件配置失败: {e}")
    
    # 为启用的插件生成描述
    def describePlugins(self) -> str:
        descriptions = []
        for plugin_name, plugin in self.plugins.items():
            if plugin.enable:
                descriptions.append(plugin.describePlugin())
        return "The following are the supported plugins and their parameters:\n" + "\n".join(descriptions)
        
    # 获取插件
    def GetPlugin(self, plugin_name):
        """获取插件"""
        plugin = self.plugins.get(plugin_name)
        if plugin and plugin.enable:
            return plugin
        return None
    
    # 启用/禁用插件
    def toggle_plugin(self, plugin_name, enable=None):
        """启用或禁用指定插件"""
        if plugin_name in self.plugins:
            if enable is not None:
                self.plugins[plugin_name].enable = enable
            else:
                self.plugins[plugin_name].enable = not self.plugins[plugin_name].enable
            return True
        return False
    
    # 保存当前设置
    def save_settings(self):
        """保存当前插件设置到配置文件"""
        self.write_plugins_to_config()
    
    # 获取所有可用插件配置（包括未加载的）
    def get_all_available_plugins(self):
        """获取配置中的所有插件（包括未加载的）"""
        return self.all_available_plugins
