from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QListWidget, QGroupBox, QMessageBox, 
                               QFileDialog, QSizePolicy)
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
        self.plugin_detail_views = {}    # 存储每个插件的详情视图
        self.setup_ui()
        self.init_plugins_list_items()
    
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
    
    def init_plugins_list_items(self):
        """初始化并加载所有的插件项"""
        self.plugin_list.clear()
        self.plugin_items.clear()
        self.plugin_detail_views.clear()  # 清空旧的详情视图
        
        # 清除右侧容器中的所有部件，安全删除旧布局
        if self.detail_container.layout():
            # 清除旧布局中的所有部件
            old_layout = self.detail_container.layout()
            while old_layout.count():
                item = old_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            QWidget().setLayout(old_layout)
        
        # 创建新的右侧容器布局
        detail_layout = QVBoxLayout(self.detail_container)
        
        # 获取插件管理器中的插件和所有的插件配置
        all_plugins_config = self.plugin_manager.all_plugins_config

        # 为每个插件预创建详情视图容器
        for plugin_name, plugin_config in all_plugins_config.items():
            
            detail_view = QWidget()
            detail_view.setVisible(False)  # 默认隐藏所有详情视图
            detail_layout.addWidget(detail_view)
            
            # 创建插件列表项
            item = PluginListWidgetItem(plugin_name, plugin_config, detail_view)
            
            # 连接保存需求信号至插件管理界面的处理函数
            item.signals.save_needed.connect(self.on_save_needed)
            
            # 添加插件列表项至列表
            self.plugin_list.addItem(item)
            self.plugin_items[plugin_name] = item
            
            self.plugin_detail_views[plugin_name] = detail_view
        
        # 默认选中第一项
        if self.plugin_list.count() > 0:
            self.plugin_list.setCurrentRow(0)
    
    def on_plugin_selected(self, current_item, previous):
        """处理插件列表选择变更"""
        # 隐藏之前选中的插件的详情视图
        if previous and isinstance(previous, PluginListWidgetItem):
            prev_view:QWidget = self.plugin_detail_views.get(previous.plugin_name)
            if prev_view:
                prev_view.setVisible(False)
        
        # 显示当前选中的插件的详情视图
        if current_item and isinstance(current_item, PluginListWidgetItem):
            self.current_plugin_item = current_item
            curr_view:QWidget = self.plugin_detail_views.get(current_item.plugin_name)
            if curr_view:
                curr_view.setVisible(True)
    
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
        """保存所有插件的修改到列表项属性\n
            及更新插件管理器的插件对象的配置\n
            并将更新后的配置写入文件""" 
        # 1. 应用所有插件的未保存修改
        any_changes = False
        new_plugins_config: Dict[str, Dict[str, Dict[str, any]]] = {} # 用于全部保存修改的配置
        
        for plugin_name, item in self.plugin_items.items():
            new_plugins_config[plugin_name] = item._config # 先保存原始配置信息至新配置信息中
            
            if item.has_pending_changes():
                
                # 应用每个插件项的修改到配置属性中
                if item.apply_changes_to_config():
                    any_changes = True
                else:
                    QMessageBox.warning(self, "更新配置失败", f"无法更新插件 {plugin_name} 的配置信息")
                    return
                new_plugins_config[plugin_name] = item._config
                
                # 更新插件管理器的插件对象
                if not self.plugin_manager.update_plugin_config(plugin_name, item.get_pending_changes()):
                    QMessageBox.warning(self, "应用配置失败", f"无法应用插件 {plugin_name} 的配置")
                    return
        
        if not any_changes:
            QMessageBox.information(self, "提示", "没有发现需要保存的修改")
            return
        
        # 2. 将更新后的配置写入文件
        if self.plugin_manager.write_config_to_file(plugins_config=new_plugins_config) == False: # 只允许通过插件管理器写入配置文件
            QMessageBox.warning(self, "保存失败", "无法写入配置文件")
            return
            
        # 3. 清除所有未保存的修改
        for item in self.plugin_items.values():
            item.clear_pending_changes()
        
        # 4. 更新UI
        self.on_save_needed(False)
        
        # 5. 显示成功消息
        QMessageBox.information(self, "保存成功", "插件配置已成功保存!\n“是否加载”设置将在程序重启后生效。")
        
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
                self.init_plugins_list_items()
                
                QMessageBox.information(self, "导入成功", f"插件 {plugin_name} 已导入")
            except Exception as e:
                QMessageBox.warning(self, "导入失败", f"插件导入失败: {e}")
    
    def closeEvent(self, event):
        """（待完全实现）关闭窗口前检查是否有未保存的修改"""
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
