from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QListWidget, QListWidgetItem,
                               QGroupBox, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, QTimer
import json
import os

from core.PluginManager import PluginManager
from core.AuxiliaryFunction import PathCheck
from gui.PluginListWidgetItem import PluginListWidgetItem
from gui.PluginDetailWidget import PluginDetailWidget

class PluginManagerWidget(QWidget):
    """插件管理界面"""
    
    def __init__(self, plugin_manager: PluginManager):
        super().__init__()
        self.plugin_manager = plugin_manager
        self.plugin_items = {}  # 存储所有插件项的引用
        self.setup_ui()
        self.load_plugins()
    
    def setup_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
        # 左侧插件列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        list_label = QLabel("已安装插件:")
        list_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_layout.addWidget(list_label)
        
        self.plugin_list = QListWidget()
        self.plugin_list.currentItemChanged.connect(self.on_plugin_selected)
        left_layout.addWidget(self.plugin_list)
        
        # 创建底部按钮区域
        bottom_buttons = QHBoxLayout()
        
        # 导入插件按钮
        import_btn = QPushButton("导入外部插件")
        import_btn.clicked.connect(self.import_plugin)
        bottom_buttons.addWidget(import_btn)
        
        # 保存设置按钮
        self.save_btn = QPushButton("保存设置")
        self.save_btn.clicked.connect(self.save_plugin_settings)
        self.save_btn.setEnabled(False)  # 初始禁用
        bottom_buttons.addWidget(self.save_btn)
        
        left_layout.addLayout(bottom_buttons)
        
        main_layout.addWidget(left_panel, 1)  # 左侧占比较小
        
        # 右侧插件详情
        self.detail_widget = PluginDetailWidget()
        self.detail_widget.plugin_changed.connect(self.on_plugin_changed)
        main_layout.addWidget(self.detail_widget, 2)  # 右侧占比较大
    
    def load_plugins(self):
        """初始化并加载所有已注册的插件"""
        self.plugin_list.clear()
        self.plugin_items.clear()
        
        # 获取插件管理器中的插件和所有的插件配置
        all_plugins_config = self.plugin_manager.all_plugins_config

        for plugin_name, plugin_config in all_plugins_config.items():
            
            # 创建并添加插件列表项
            item = PluginListWidgetItem(plugin_name, plugin_config)
            self.plugin_list.addItem(item)
            self.plugin_items[plugin_name] = item
        
        # 默认选中第一项
        if self.plugin_list.count() > 0:
            self.plugin_list.setCurrentRow(0)
    
    def on_plugin_selected(self, current_item, previous):
        """处理插件列表选择时的详情界面变更"""
        if not current_item:
            self.detail_widget.clear()
            return
            
        if isinstance(current_item, PluginListWidgetItem):
            self.detail_widget.display_plugin(current_item)
            
            # 检查是否有未保存的修改来更新保存按钮状态
            self.update_save_button()
    
    def on_plugin_changed(self, plugin_name, changes):
        """处理插件配置变更"""
        if plugin_name in self.plugin_items:
            item = self.plugin_items[plugin_name]
            item.update_config(changes)
            
            # 更新保存按钮状态
            self.update_save_button()
    
    def update_save_button(self):
        """更新保存按钮的状态"""
        has_changes = any(item.has_pending_changes() for item in self.plugin_items.values())
        self.save_btn.setEnabled(has_changes)
        if has_changes:
            self.save_btn.setText("保存修改")
            self.save_btn.setStyleSheet("background-color: #FFCCCB;")  # 浅红色背景表示有未保存修改
        else:
            self.save_btn.setText("保存设置")
            self.save_btn.setStyleSheet("")
    
    def save_plugin_settings(self):
        """保存所有插件设置到配置文件"""
        try:
            # 1. 读取配置文件
            config = self.read_config_file()
            if not config:
                QMessageBox.warning(self, "读取失败", "无法读取配置文件")
                return
                
            # 2. 收集所有插件的待保存修改
            any_changes = False
            
            for plugin_name, item in self.plugin_items.items():
                if item.has_pending_changes():
                    any_changes = True
                    changes = item.get_pending_changes()
                    
                    # 更新配置
                    if plugin_name not in config:
                        continue
                    
                    # 处理基本设置
                    if 'is_load' in changes:
                        config[plugin_name]["is_load"] = changes['is_load']
                        
                    if 'enable' in changes:
                        config[plugin_name]["enable"] = changes['enable']
                    
                    # 处理参数修改
                    if 'parameters' in changes:
                        # 更新参数值
                        for param_name, param_value in changes['parameters'].items():
                            for i, param in enumerate(config[plugin_name]["parameters"]):
                                if param.get('name') == param_name:
                                    config[plugin_name]["parameters"][i]['default'] = param_value
                                    break
            
            if not any_changes:
                QMessageBox.information(self, "提示", "没有发现需要保存的修改")
                return
            
            # 3. 将配置写入文件
            self.write_config_file(config)
            
            # 4. 更新插件对象（如果已加载）
            for plugin_name, item in self.plugin_items.items():
                if item.has_pending_changes():
                    changes = item.get_pending_changes()
                    plugin = self.plugin_manager.plugins.get(plugin_name)
                    
                    if plugin:
                        # 更新插件对象属性
                        if 'enable' in changes:
                            plugin.enable = changes['enable']
                        
                        # 更新参数
                        if 'parameters' in changes:
                            for param_name, param_value in changes['parameters'].items():
                                for param in plugin.parameters:
                                    if param.get('name') == param_name:
                                        param['default'] = param_value
                                        break
                    
                    # 清除待保存的修改
                    item.clear_pending_changes()
            
            # 5. 重置UI状态
            self.update_save_button()
            
            # 6. 显示成功消息
            QMessageBox.information(self, "成功", "插件配置已成功保存!\n部分设置将在程序重启后生效。")
                
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"保存设置时发生错误: {e}")
    
    def read_config_file(self):
        """从配置文件读取插件配置"""
        config_path = self.plugin_manager.plugins_config_path
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"读取配置文件失败: {e}")
            return {}
    
    def write_config_file(self, config):
        """将插件配置写入配置文件"""
        config_path = self.plugin_manager.plugins_config_path
        try:
            # 确保目录存在
            PathCheck(config_path)
            
            # 写入配置文件
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            print(f"已将配置写入文件 {config_path}")
            return True
        except Exception as e:
            print(f"写入配置文件失败: {e}")
            return False
    
    def import_plugin(self):
        """导入外部插件"""
        # 这里仅为界面演示，实际需要实现插件导入逻辑
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择插件文件", "", "Python文件 (*.py)"
        )
        
        if file_path:
            QMessageBox.information(self, "导入插件", "插件导入功能尚未实现")
    
    def closeEvent(self, event):
        """关闭窗口前检查是否有未保存的修改"""
        has_changes = any(item.has_pending_changes() for item in self.plugin_items.values())
        
        if has_changes:
            reply = QMessageBox.question(self, "未保存的修改", 
                                       "有未保存的插件设置修改，是否保存？",
                                       QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            
            if reply == QMessageBox.Yes:
                self.save_plugin_settings()
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
