from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QListWidget, QGroupBox, QMessageBox, 
                               QFileDialog)
from PySide6.QtCore import Qt
import json
import os
from typing import Dict

from core.PluginManager import PluginManager
from core.AuxiliaryFunction import PathCheck
from gui.PluginListWidgetItem import PluginListWidgetItem

class PluginManagerWidget(QWidget):
    """插件管理界面"""
    
    def __init__(self, plugin_manager: PluginManager):
        super().__init__()
        self.plugin_manager = plugin_manager
        self.plugin_items: Dict[str, PluginListWidgetItem] = {}  # 插件项字典，键为插件名称，值为PluginListWidgetItem对象
        self.current_plugin_item = None  # 当前选中的插件项
        self.detail_container = None     # 右侧详情容器
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
        
        # 右侧插件详情区域 - 只创建容器，内容由插件项自己管理
        self.detail_container = QWidget()
        # 预先为容器设置一个空的布局，避免后续添加布局时产生冲突
        QVBoxLayout(self.detail_container)
        main_layout.addWidget(self.detail_container, 2)  # 右侧占比较大
    
    def load_plugins(self):
        """初始化并加载所有已注册的插件"""
        self.plugin_list.clear()
        self.plugin_items.clear()
        
        # 获取插件管理器中的插件和所有的插件配置
        all_plugins_config = self.plugin_manager.all_plugins_config

        for plugin_name, plugin_config in all_plugins_config.items():
            # 创建并添加插件列表项
            item = PluginListWidgetItem(plugin_name, plugin_config)
            item.signals.config_changed.connect(self.on_plugin_changed) 
            item.signals.save_needed.connect(self.on_save_needed)
            self.plugin_list.addItem(item)
            self.plugin_items[plugin_name] = item
        
        # 默认选中第一项
        if self.plugin_list.count() > 0:
            self.plugin_list.setCurrentRow(0)
    
    def on_plugin_selected(self, current_item, previous):
        """处理插件列表选择变更"""
        if isinstance(current_item, PluginListWidgetItem):
            self.current_plugin_item = current_item
            # 让当前选中的插件项创建并管理详情视图
            current_item.create_detail_view(self.detail_container)
    
    def on_plugin_changed(self, plugin_name):
        """处理插件配置变更通知"""
        # 更新插件项视图
        if self.current_plugin_item and self.current_plugin_item.plugin_name == plugin_name:
            self.current_plugin_item.update_detail_view()
    
    def on_save_needed(self, needed):
        """处理保存需求变更"""
        self.save_btn.setEnabled(needed)
        
        if needed:
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
            
            # 2. 应用所有插件的未保存修改
            any_changes = False
            for plugin_name, item in self.plugin_items.items():
                if item.has_pending_changes():
                    if item.apply_changes_to_config(config):
                        any_changes = True
                        
                    # 更新插件对象（如果已加载）
                    plugin = self.plugin_manager.plugins.get(plugin_name)
                    if plugin:
                        # 获取修改内容
                        changes = item.get_pending_changes()
                        
                        # 更新启用状态
                        if 'enable' in changes:
                            plugin.enable = changes['enable']
                        
                        # 更新参数
                        if 'parameters' in changes:
                            for param_name, param_value in changes['parameters'].items():
                                for param in plugin.parameters:
                                    if param.get('name') == param_name:
                                        param['default'] = param_value
                                        break
            
            if not any_changes:
                QMessageBox.information(self, "提示", "没有发现需要保存的修改")
                return
            
            # 3. 将更新后的配置写入文件
            self.write_config_file(config)
            
            # 4. 清除所有未保存的修改
            for item in self.plugin_items.values():
                item.clear_pending_changes()
            
            # 5. 更新UI
            self.on_save_needed(False)
            
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
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择插件文件", "", "Python文件 (*.py)"
        )
        
        if file_path:
            # 这里实现导入插件的逻辑
            try:
                # 示例实现 - 需要替换为实际导入逻辑
                plugin_name = os.path.basename(file_path).replace('.py', '')
                dest_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'plugins', os.path.basename(file_path))
                
                # 复制文件
                import shutil
                shutil.copy(file_path, dest_path)
                
                # 触发插件发现和加载
                self.plugin_manager.discover_new_plugin_classes()
                self.plugin_manager.load_plugins_from_config(self.plugin_manager.plugins_config_path)
                
                # 重新加载插件列表
                self.load_plugins()
                
                QMessageBox.information(self, "导入成功", f"插件 {plugin_name} 已导入")
            except Exception as e:
                QMessageBox.warning(self, "导入失败", f"插件导入失败: {e}")
    
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
