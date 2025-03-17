from PySide6.QtWidgets import QListWidgetItem
from PySide6.QtCore import Qt
from copy import deepcopy

class PluginListWidgetItem(QListWidgetItem):
    """表示插件列表中的一个项目"""
    
    def __init__(self, plugin_name, plugin_config=None):
        """
        初始化插件列表项
        
        参数:
            plugin_name (str): 插件名称
            config (dict): 插件配置
        """
        super().__init__(plugin_name)
        self.plugin_name = plugin_name
        self.is_load = plugin_config.get('is_load', True)
        self.enable = plugin_config.get('enable', True)
        self._config = plugin_config or {}
        self._pending_changes = {}  # 存储未保存的修改
        self.update_appearance()
    
    def update_appearance(self):
        """根据加载和启用状态更新外观"""
        if not self.is_load:
            # 未加载的插件显示为浅灰色
            self.setForeground(Qt.lightGray)
            self.setToolTip("未加载")
        elif not self.enable:
            # 已加载但未启用的插件显示为灰色
            self.setForeground(Qt.gray)
            self.setToolTip("已加载但未启用")
        else:
            # 已加载且已启用的插件显示为黑色
            self.setForeground(Qt.black)
            self.setToolTip("已加载且已启用")
    
    def set_loaded(self, is_loaded):
        """设置加载状态"""
        self.is_load = is_loaded
        # 如果未加载，则必定未启用
        if not is_loaded:
            self.enable = False
        self.update_appearance()
        self._pending_changes['is_load'] = is_loaded
        if not is_loaded:
            self._pending_changes['enable'] = False
    
    def set_enabled(self, is_enabled):
        """设置启用状态（只有已加载的插件才能被启用）"""
        if self.is_load:
            self.enable = is_enabled
            self._pending_changes['enable'] = is_enabled
        else:
            self.enable = False
            self._pending_changes['enable'] = False
        self.update_appearance()
    
    def get_plugin_name(self):
        """获取插件名称"""
        return self.plugin_name
    
    def get_config(self):
        """获取插件配置（包含待保存的修改）"""
        # 返回一份配置的深拷贝，避免外部修改直接影响内部状态
        result = deepcopy(self._config)
        return result
    
    def update_config(self, changes):
        """
        更新插件配置
        
        参数:
            changes (dict): 包含配置修改的字典
        """
        # 更新待保存的修改
        for key, value in changes.items():
            if key == 'is_load':
                self.set_loaded(value)
            elif key == 'enable':
                self.set_enabled(value)
            elif key == 'parameters':
                if 'parameters' not in self._pending_changes:
                    self._pending_changes['parameters'] = {}
                
                # 更新参数配置
                for param_name, param_value in value.items():
                    self._pending_changes['parameters'][param_name] = param_value
                    
                    # 同时更新配置参数的默认值（用于UI显示）
                    if 'parameters' in self._config:
                        for param in self._config['parameters']:
                            if param.get('name') == param_name:
                                param['default'] = param_value
                                break
            else:
                self._pending_changes[key] = value
    
    def has_pending_changes(self):
        """检查是否有未保存的修改"""
        return bool(self._pending_changes)
    
    def get_pending_changes(self):
        """获取未保存的修改"""
        return deepcopy(self._pending_changes)
    
    def clear_pending_changes(self):
        """清除未保存的修改"""
        self._pending_changes = {}
    
    def apply_changes(self, config):
        """
        应用新的配置
        
        参数:
            config (dict): 新的插件配置
        """
        self._config = deepcopy(config)
        self.is_load = config.get('is_load', True)
        self.enable = config.get('enable', True)
        self.update_appearance()
        self.clear_pending_changes()