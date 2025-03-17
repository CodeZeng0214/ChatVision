### 插件管理器

import os
import json
import importlib
import inspect
from typing import Dict, Callable, Any, List
from core.Plugin import Plugin
import sys
from core.AuxiliaryFunction import PathCheck

COFIG_PATH = "plugins/PluginConfigs.json" # 插件配置的默认路径

### ========== 插件注册与管理 ========== ###
class PluginManager:
    """
    插件注册管理器：支持动态注册与调用插件。
    """
    def __init__(self, is_discover=False, plugins_config_path=COFIG_PATH):
        """可选参数：\n
        - is_discover: bool 是否需要扫描新的插件类，默认不扫描\n"""
        self.plugins:Dict[str, Plugin] = {}  # 插件字典，键为插件名称，值为Plugin对象
        self.all_plugins_config = {}  # 存储配置文件中所有可用的插件配置（不一定加载）
        self.plugins_config_path = plugins_config_path # 插件配置的路径
        self.is_discover = is_discover  # 是否需要扫描新的插件类，默认不扫描
                
        # 尝试从配置文件中加载插件
        try:
            # 扫描插件目录，判断是否有新插件类
            if self.is_discover:
                self.discover_new_plugin_classes() # 扫描插件目录，判断是否有新插件类    
            self.load_plugins_from_config(self.plugins_config_path)
        except Exception as e:
            print(f"从配置文件加载插件失败: {e}\n将尝试扫描并创建默认配置")
            # 如果加载失败，尝试扫描并创建默认配置
            self.discover_new_plugin_classes()
            self.load_plugins_from_config(self.plugins_config_path)
            
    def read_plugins_config_file(self, plugins_config_path: str) -> Dict[str, Dict[str, Any]]:
        """读取插件配置文件\n
        参数：\n
        - plugins_config_path: str 插件配置文件路径(优先使用传入的路径，否则使用默认路径)\n
        返回：Dict[str, Dict[str, Any]] 插件配置字典
        """
        plugins_config_path = plugins_config_path or self.plugins_config_path 
        try:
            with open(plugins_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"读取插件配置失败，返回空子典: {e}")
            return {}
    
    def discover_new_plugin_classes(self, new_plugins_path: str='plugins') -> int:
        """扫描插件模块目录，发现新的Plugin子类并添加到配置文件（扫描的时候导入了插件自身依赖的模块）\n
        可选参数：\n
        - new_plugins_path: str 新插件目录路径，默认为'plugins'\n
        返回：int 新插件数量"""
        existing_plugins_config = self.read_plugins_config_file(self.plugins_config_path)
        existing_config_classes = [plugin["class_name"] for plugin in existing_plugins_config.values()]
        new_plugin_count = 0
        try:
            # 添加插件目录到Python路径
            plugin_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), new_plugins_path)
            if not os.path.exists(plugin_dir): os.makedirs(plugin_dir)
            if plugin_dir not in sys.path: sys.path.append(plugin_dir)
            
            print(f"开始从插件目录 {new_plugins_path} 中扫描可能的新插件...")
            
            # 遍历插件目录下所有.py文件
            for filename in os.listdir(plugin_dir):
                if filename.endswith(".py") and not filename.startswith("__"):
                    module_name = filename[:-3]  # 去掉.py后缀
                    try:
                        # 导入插件模块
                        module = importlib.import_module(f"plugins.{module_name}")
                        
                        # 查找模块中的Plugin子类并收集信息
                        for class_name, obj in inspect.getmembers(module):
                            # 若插件已存在配置中，则跳过
                            if class_name in existing_config_classes:
                                continue  # 避免重复添加
                            
                            if (inspect.isclass(obj) and 
                                issubclass(obj, Plugin) and 
                                obj != Plugin):  # 排除基类本身
                                try:
                                    # 实例化插件以获取信息
                                    plugin_instance = obj()
                                    
                                    # 写入新的插件配置信息
                                    plugin_instance.write_plugin_to_config(self.plugins_config_path)
                                    new_plugin_count += 1
                                    
                                    print(f"发现新的插件类，已经写入配置文件: {plugin_instance.plugin_name} ({class_name})")
                                except Exception as e:
                                    print(f"收集插件信息失败 {class_name}: {e}")
                    except Exception as e:
                        print(f"加载插件模块 {module_name} 失败: {e}")
            
            print(f"扫描完成，共发现 {new_plugin_count} 个新插件")
            return new_plugin_count
        except Exception as e:
            print(f"遍历插件目录时出错: {e}")
            return 0
    
    def register_plugin(self, plugin: Plugin):
        """注册一个插件实例"""
        self.plugins[plugin.plugin_name] = plugin
    
    def load_plugins_from_config(self, plugins_config_path: str):
        """从配置文件中加载插件"""
        if not os.path.exists(plugins_config_path):
            # 如果配置文件不存在，创建默认配置
            print(f"配置文件 {plugins_config_path} 不存在，将扫描新插件并创建配置")
            self.discover_new_plugin_classes()
            self.load_plugins_from_config(plugins_config_path)  # 递归调用
            return
        
        # 从配置文件加载
        print(f"正在读取配置文件以加载插件: {plugins_config_path}")
        try:
            plugins_config = self.read_plugins_config_file(plugins_config_path)
            
            # 清空当前插件，按配置重新加载
            self.plugins.clear()
            self.all_plugins_config = plugins_config  # 挂载所有配置项
            
            # 根据配置动态导入和实例化插件
            for plugin_name, plugin_config in plugins_config.items():
                # 使用is_load来控制是否加载插件
                if plugin_config.get('is_load', True):  # 默认加载
                    try:
                        # 从配置获取模块路径和类名
                        module_path = plugin_config.get('module_path')
                        class_name = plugin_config.get('class_name')
                        
                        if not module_path or not class_name:
                            print(f"插件配置缺少module_path或class_name: {plugin_name}")
                            continue

                        # 实例化插件类
                        module = importlib.import_module(module_path) # 动态导入插件模块
                        plugin_class = getattr(module, class_name) # 获取插件类
                        plugin_instance:Plugin = plugin_class() # 实例化插件类
                        
                        # 从配置更新挂载的插件属性并注册
                        plugin_instance.update_info_from_config(plugin_config) #更新插件配置
                        self.register_plugin(plugin_instance) # 注册插件
                        
                        print(f"已加载插件: {plugin_name}, 启用状态: {plugin_instance.enable}")
                    except Exception as e:
                        print(f"加载插件失败 {plugin_name}: {e}")
                else:
                    print(f"插件已配置为不加载: {plugin_name}")
            
            print(f"加载完成，共加载了 {len(self.plugins)} 个插件")
        except Exception as e:
            print(f"加载插件配置失败: {e}")
            raise
    
    def write_plugins_to_config(self, plugins_config_path: str = None, plugins_config: Dict[str, Dict[str, Any]] = None):
        """将插件配置写入配置文件，覆盖原有配置"""
        # 确保配置文件目录存在
        os.makedirs(os.path.dirname(plugins_config_path), exist_ok=True)

        # 使用传入的配置或当前配置
        plugins_config = plugins_config or self.all_plugins_config
        plugins_config_path = plugins_config_path or self.plugins_config_path
        # 写入文件（清空了原配置文件）
        try:
            with open(plugins_config_path, 'w', encoding='utf-8') as f:
                json.dump(plugins_config, f, indent=4, ensure_ascii=False)
            print(f"已将 {len(plugins_config)} 个插件配置写入 {plugins_config_path}")
        except (OSError, PermissionError) as e:
            print(f"文件操作失败: {e}")
        except TypeError as e:
            print(f"数据序列化失败: {e}")
    
    def describe_plugins(self) -> str:
        """生成所有插件的描述"""
        descriptions = []
        for plugin_name, plugin in self.plugins.items():
            if plugin.enable:
                descriptions.append(plugin.describe_plugin())
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
        """获取配置中的所有插件配置信息（包括未加载的）"""
        return self.all_plugins_config
