from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QListWidget, QListWidgetItem,
                               QGroupBox, QFormLayout, QLineEdit, QCheckBox,
                               QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, QTimer
import json
import os

from ChatRobot import ChatRobot
from core.PluginManager import PluginManager
from core.Plugin import Plugin
from core.AuxiliaryFunction import PathCheck

class PluginManagerWidget(QWidget):
    """插件管理界面"""
    
    def __init__(self, chat_robot: ChatRobot):
        super().__init__()
        self.chat_robot = chat_robot
        self.setup_ui()
        self.pending_changes = {}  # 存储所有待保存的修改
        self.current_plugin_name = None  # 当前正在编辑的插件名称
        self.load_plugins()
        self.current_config_fields = {}  # 存储当前正在编辑的配置字段
    
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
        self.plugin_list.currentRowChanged.connect(self.show_plugin_details)
        left_layout.addWidget(self.plugin_list)
        
        import_btn = QPushButton("导入外部插件")
        import_btn.clicked.connect(self.import_plugin)
        left_layout.addWidget(import_btn)
        
        main_layout.addWidget(left_panel)
        
        # 右侧插件详情
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.detail_label = QLabel("选择插件查看详情")
        self.detail_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_layout.addWidget(self.detail_label)
        
        # 插件设置表单
        self.settings_form = QGroupBox("插件设置")
        self.form_layout = QFormLayout(self.settings_form)
        right_layout.addWidget(self.settings_form)
        self.settings_form.hide()
        
        # 启用/禁用按钮
        self.toggle_btn = QPushButton("启用/禁用")
        self.toggle_btn.clicked.connect(self.toggle_plugin)
        right_layout.addWidget(self.toggle_btn)
        self.toggle_btn.hide()
        
        # 保存设置按钮
        self.save_btn = QPushButton("保存设置")
        self.save_btn.clicked.connect(self.save_plugin_settings)
        right_layout.addWidget(self.save_btn)
        self.save_btn.hide()
        
        right_layout.addStretch()
        main_layout.addWidget(right_panel)
    
    def load_plugins(self):
        """加载所有已注册的插件"""
        self.plugin_list.clear()
        
        # 获取配置文件中的所有插件
        all_plugins = self.read_config_file()
        loaded_plugins = self.chat_robot.plugin_manager.plugins
        
        for plugin_name, plugin_config in all_plugins.items():
            item = QListWidgetItem(plugin_name)
            
            # 设置加载状态
            is_loaded = plugin_config.get('is_load', True)
            
            # 设置颜色
            if not is_loaded:
                # 未加载的插件显示为浅灰色
                item.setForeground(Qt.lightGray)
                item.setToolTip("未加载")
            elif plugin_name in loaded_plugins and not loaded_plugins[plugin_name].enable:
                # 已加载但未启用的插件显示为灰色
                item.setForeground(Qt.gray)
                item.setToolTip("已加载但未启用")
            else:
                # 已加载且已启用的插件显示为黑色
                item.setForeground(Qt.black)
                item.setToolTip("已加载且已启用")
                
            self.plugin_list.addItem(item)
    
    def show_plugin_details(self, row):
        """显示选中插件的详情"""
        if row < 0:
            return
            
        new_plugin_name = self.plugin_list.item(row).text()
        
        # 如果切换插件，先保存当前插件的临时修改
        if self.current_plugin_name and self.current_plugin_name != new_plugin_name:
            self.save_current_changes_to_pending()
        
        self.current_plugin_name = new_plugin_name
        
        # 从配置文件读取插件信息
        config = self.read_config_file()
        plugin_config = config.get(self.current_plugin_name, {})
        
        # 检查插件是否已加载
        plugin = self.chat_robot.plugin_manager.plugins.get(self.current_plugin_name)
        is_loaded = plugin_config.get('is_load', True)
        
        # 设置标题
        self.detail_label.setText(f"插件: {self.current_plugin_name}")
        
        # 清除现有表单和配置字段映射
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)
        self.current_config_fields = {}
        
        # 添加描述
        description = plugin_config.get('description', '无描述') if plugin_config else '无描述'
        if plugin:  # 如果插件已加载，使用实例中的描述
            description = plugin.description
        
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        self.form_layout.addRow(QLabel("描述:"), desc_label)
        
        # 添加加载配置和启用配置
        self.load_checkbox = QCheckBox()
        
        # 检查是否有待保存的修改
        if self.current_plugin_name in self.pending_changes and 'is_load' in self.pending_changes[self.current_plugin_name]:
            is_loaded = self.pending_changes[self.current_plugin_name]['is_load']
        
        self.load_checkbox.setChecked(is_loaded)
        self.load_checkbox.toggled.connect(self.on_field_changed)
        self.form_layout.addRow(QLabel("启动时加载:"), self.load_checkbox)
        
        # 启用状态复选框（仅当加载时可编辑）
        self.enable_checkbox = QCheckBox()
        enable_value = plugin_config.get('enable', True) if plugin_config else True
        
        # 检查是否有待保存的修改
        if self.current_plugin_name in self.pending_changes and 'enable' in self.pending_changes[self.current_plugin_name]:
            enable_value = self.pending_changes[self.current_plugin_name]['enable']
        elif plugin:  # 如果插件已加载，使用实际状态
            enable_value = plugin.enable
        
        self.enable_checkbox.setChecked(enable_value)
        self.enable_checkbox.setEnabled(is_loaded)  # 只有已加载的插件才能启用/禁用
        self.enable_checkbox.toggled.connect(self.on_field_changed)
        self.load_checkbox.toggled.connect(self.update_enable_state)
        self.form_layout.addRow(QLabel("启用插件:"), self.enable_checkbox)
        
        # 参数显示和编辑
        if plugin_config and 'parameters' in plugin_config:
            parameters = plugin_config['parameters']
        elif plugin:  # 如果插件已加载，使用实例中的参数
            parameters = plugin.parameters
        else:
            parameters = []
        
        # 添加参数设置
        for param in parameters:
            name = param.get('name', '')
            description = param.get('description', '')
            required = param.get('required', False)
            
            # 跳过必填参数，这些应该由用户在消息中提供
            if required:
                continue
                
            # 获取默认值 - 首先查看待保存修改，然后查看配置
            default_value = None
            if self.current_plugin_name in self.pending_changes and 'parameters' in self.pending_changes[self.current_plugin_name]:
                for pending_param in self.pending_changes[self.current_plugin_name]['parameters']:
                    if pending_param.get('name') == name:
                        default_value = pending_param.get('default', '')
                        break
            
            if default_value is None:
                default_value = param.get('default', '')
            
            # 不同类型参数的不同处理
            if "path" in name.lower() and "weight" in name.lower():
                param_layout = QHBoxLayout()
                field = QLineEdit()
                field.setPlaceholderText(f"默认路径: {description}")
                
                # 设置当前值（如果有）
                if default_value:
                    field.setText(str(default_value))
                    
                # 添加修改事件
                field.textChanged.connect(self.on_field_changed)
                
                # 添加文件浏览按钮（针对权重文件）
                browse_btn = QPushButton("浏览...")
                browse_btn.clicked.connect(lambda checked, f=field: self.browse_weight_file(f))
                
                param_layout.addWidget(field)
                param_layout.addWidget(browse_btn)
                
                container = QWidget()
                container.setLayout(param_layout)
                
                self.form_layout.addRow(QLabel(f"{name} (可选):"), container)
                self.current_config_fields[name] = field
            elif "path" in name.lower():
                param_layout = QHBoxLayout()
                field = QLineEdit()
                field.setPlaceholderText(f"默认路径: {description}")
                
                # 设置当前值（如果有）
                if default_value:
                    field.setText(str(default_value))
                
                # 添加浏览按钮（针对常规路径）
                browse_btn = QPushButton("浏览...")
                browse_btn.clicked.connect(lambda checked, f=field: self.browse_path(f))
                
                param_layout.addWidget(field)
                param_layout.addWidget(browse_btn)
                
                container = QWidget()
                container.setLayout(param_layout)
                
                self.form_layout.addRow(QLabel(f"{name} (可选):"), container)
                self.current_config_fields[name] = field
                # 添加修改事件
                field.textChanged.connect(self.on_field_changed)
            elif "is_" in name.lower():
                field = QCheckBox()
                field.setToolTip(description)
                
                # 设置初始值（如果有）
                if isinstance(default_value, bool):
                    field.setChecked(default_value)
                
                self.form_layout.addRow(QLabel(f"{name} (可选):"), field)
                self.current_config_fields[name] = field
                # 添加修改事件
                field.toggled.connect(self.on_field_changed)
            else:
                field = QLineEdit()
                field.setPlaceholderText(f"{description}")
                
                # 设置初始值（如果有）
                if default_value:
                    field.setText(str(default_value))
                
                self.form_layout.addRow(QLabel(f"{name} (可选):"), field)
                self.current_config_fields[name] = field
                # 添加修改事件
                field.textChanged.connect(self.on_field_changed)
        
        # 显示设置区域和按钮
        self.settings_form.show()
        self.save_btn.show()
        
        # 更新保存按钮状态
        if self.current_plugin_name in self.pending_changes:
            self.save_btn.setText("保存修改")
            self.save_btn.setStyleSheet("background-color: #FFCCCB;")  # 浅红色背景表示有未保存修改
        else:
            self.save_btn.setText("保存设置")
            self.save_btn.setStyleSheet("")
        
        # 更新按钮状态
        self.toggle_btn.setVisible(is_loaded)  # 只有已加载的插件才显示启用/禁用按钮
        if plugin and is_loaded:
            self.toggle_btn.setText("禁用插件" if plugin.enable else "启用插件")
    
    def on_field_changed(self):
        """字段修改时的回调"""
        # 标记有未保存的修改
        if self.current_plugin_name not in self.pending_changes:
            self.pending_changes[self.current_plugin_name] = {}
        
        # 更新保存按钮状态
        self.save_btn.setText("保存修改")
        self.save_btn.setStyleSheet("background-color: #FFCCCB;")  # 浅红色背景表示有未保存修改
        
    def save_current_changes_to_pending(self):
        """将当前表单中的修改保存到待保存字典"""
        if not self.current_plugin_name:
            return
            
        # 初始化待保存字典
        if self.current_plugin_name not in self.pending_changes:
            self.pending_changes[self.current_plugin_name] = {}
        
        # 收集当前表单中的修改
        self.pending_changes[self.current_plugin_name]['is_load'] = self.load_checkbox.isChecked()
        self.pending_changes[self.current_plugin_name]['enable'] = self.enable_checkbox.isChecked()
        
        # 收集参数修改
        params_changes = []
        # 首先从配置文件读取所有参数
        config = self.read_config_file()
        plugin_config = config.get(self.current_plugin_name, {})
        original_params = plugin_config.get('parameters', []) if plugin_config else []
        
        # 复制原始参数
        for param in original_params:
            param_copy = param.copy()
            name = param_copy.get('name', '')
            
            # 如果参数在当前编辑的字段中，更新它的值
            if name in self.current_config_fields:
                field = self.current_config_fields[name]
                if isinstance(field, QLineEdit):
                    param_copy['default'] = field.text()
                elif isinstance(field, QCheckBox):
                    param_copy['default'] = field.isChecked()
            
            params_changes.append(param_copy)
        
        # 保存修改后的参数
        self.pending_changes[self.current_plugin_name]['parameters'] = params_changes
    
    def update_enable_state(self, is_checked):
        """更新启用状态复选框"""
        self.enable_checkbox.setEnabled(is_checked)
        if not is_checked:
            self.enable_checkbox.setChecked(False)
        self.on_field_changed()  # 标记有修改
    
    def browse_path(self, field):
        """打开目录浏览对话框选择路径"""
        path = QFileDialog.getExistingDirectory(self, "选择目录")
        if path:
            field.setText(path)
    
    def browse_weight_file(self, field):
        """打开文件浏览对话框选择权重文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择权重文件", "", "模型权重文件 (*.pt *.pth *.weights);;所有文件 (*)"
        )
        if file_path:
            field.setText(file_path)
    
    def toggle_plugin(self):
        """启用/禁用插件"""
        current_row = self.plugin_list.currentRow()
        if current_row >= 0:
            item = self.plugin_list.item(current_row)
            plugin_name = item.text()
            
            # 检查插件是否已加载
            plugin = self.chat_robot.plugin_manager.plugins.get(plugin_name)
            if not plugin:
                QMessageBox.warning(self, "操作失败", "此插件未加载，无法启用/禁用")
                return
            
            # 切换插件的启用状态
            if self.chat_robot.plugin_manager.toggle_plugin(plugin_name):
                if plugin.enable:
                    item.setForeground(Qt.black)  # 启用(黑色)
                    self.toggle_btn.setText("禁用插件")
                    self.enable_checkbox.setChecked(True)
                else:
                    item.setForeground(Qt.gray)  # 禁用(灰色)
                    self.toggle_btn.setText("启用插件")
                    self.enable_checkbox.setChecked(False)
    
    def save_plugin_settings(self):
        """保存所有插件设置到配置文件"""
        # 保存当前表单中的修改到待保存字典
        self.save_current_changes_to_pending()
        
        try:
            # 1. 读取配置文件
            config = self.read_config_file()
            if not config:
                QMessageBox.warning(self, "读取失败", "无法读取配置文件")
                return
                
            # 2. 更新配置文件中的插件设置
            for plugin_name, changes in self.pending_changes.items():
                if plugin_name not in config:
                    continue
                
                # 更新插件配置
                is_load = changes.get('is_load')
                if is_load is not None:
                    config[plugin_name]["is_load"] = is_load
                    
                    # 如果不加载，则强制设置为不启用
                    if not is_load:
                        config[plugin_name]["enable"] = False
                    else:
                        enable_value = changes.get('enable', True)
                        config[plugin_name]["enable"] = enable_value
                
                # 更新参数设置
                if 'parameters' in changes:
                    # 创建参数名到参数的映射
                    config_params = {param.get('name'): i for i, param in enumerate(config[plugin_name]["parameters"])}
                    
                    # 更新参数值
                    for param in changes['parameters']:
                        name = param.get('name')
                        if name in config_params and not param.get('required', False):
                            config[plugin_name]["parameters"][config_params[name]]['default'] = param.get('default')
            
            # 3. 将配置写入文件
            self.write_config_file(config)
            
            # 4. 更新插件对象（如果已加载）
            for plugin_name, changes in self.pending_changes.items():
                plugin = self.chat_robot.plugin_manager.plugins.get(plugin_name)
                if plugin:
                    if 'enable' in changes:
                        plugin.enable = changes['enable']
                    
                    if 'parameters' in changes:
                        # 更新参数默认值
                        for changed_param in changes['parameters']:
                            name = changed_param.get('name')
                            if name and 'default' in changed_param:
                                for param in plugin.parameters:
                                    if param.get('name') == name and not param.get('required', False):
                                        param['default'] = changed_param['default']
                                        break
            
            # 5. 清除待保存的修改
            self.pending_changes = {}
            
            # 6. 更新界面
            self.save_btn.setText("设置已保存!")
            self.save_btn.setStyleSheet("")
            QTimer.singleShot(2000, lambda: self.save_btn.setText("保存设置"))
            
            # 7. 刷新插件列表，反映新状态
            self.load_plugins()
            
            QMessageBox.information(self, "成功", "插件配置已成功保存!\n设置将在程序重启后生效。")
                
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"保存设置时发生错误: {e}")
    
    def read_config_file(self):
        """从配置文件读取插件配置"""
        config_path = self.chat_robot.plugin_manager.plugins_config_path
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
        config_path = self.chat_robot.plugin_manager.plugins_config_path
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
        if self.pending_changes:
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
