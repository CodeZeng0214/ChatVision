from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QGroupBox, QFormLayout, QLineEdit, QCheckBox,
                               QPushButton, QFileDialog)
from PySide6.QtCore import Qt, Signal
import json
from gui.PluginListWidgetItem import PluginListWidgetItem

class PluginDetailWidget(QWidget):
    """插件详情显示和编辑组件"""
    
    # 信号定义
    plugin_changed = Signal(str, dict)  # 插件配置被修改时发出的信号(插件名, 修改内容)
    
    def __init__(self):
        super().__init__()
        self.plugin_name = None  # 当前显示的插件名
        self.plugin_config = {}  # 插件配置
        self.current_config_fields = {}  # 当前配置字段的控件引用
        self.setup_ui()
    
    def setup_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 插件标题
        self.title_label = QLabel("选择插件查看详情")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title_label)
        
        # 插件设置表单
        self.settings_form = QGroupBox("插件设置")
        self.form_layout = QFormLayout(self.settings_form)
        layout.addWidget(self.settings_form)
        self.settings_form.hide()
        
        # 启用/禁用按钮
        self.toggle_btn = QPushButton("启用/禁用")
        self.toggle_btn.clicked.connect(self.toggle_plugin)
        layout.addWidget(self.toggle_btn)
        self.toggle_btn.hide()
        
        layout.addStretch()
    
    def display_plugin(self, plugin_item: PluginListWidgetItem):
        """
        显示插件详情
        
        参数:
            plugin_item: PluginListWidgetItem 插件列表项
        """
        if not plugin_item:
            self.clear()
            return
            
        self.plugin_name = plugin_item.plugin_name
        self.plugin_config = plugin_item._config
        is_load = plugin_item.is_load
        enable = plugin_item.enable
        
        # 设置标题
        self.title_label.setText(f"插件名称: {self.plugin_name}")
        
        # 清除现有表单和配置字段映射
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)
        self.current_config_fields = {}
        
        # 添加描述
        description = self.plugin_config.get('description', '无描述')
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        self.form_layout.addRow(QLabel("描述:"), desc_label)
        
        # 添加加载配置
        self.load_checkbox = QCheckBox()
        self.load_checkbox.setChecked(is_load)
        self.load_checkbox.toggled.connect(lambda state: self.update_plugin_config('is_load', state))
        self.form_layout.addRow(QLabel("启动时加载:"), self.load_checkbox)
        
        # 启用状态复选框（仅当加载时可编辑）
        self.enable_checkbox = QCheckBox()
        self.enable_checkbox.setChecked(enable)
        self.enable_checkbox.setEnabled(is_load)  # 只有已加载的插件才能启用/禁用
        self.enable_checkbox.toggled.connect(lambda state: self.update_plugin_config('enable', state))
        self.load_checkbox.toggled.connect(self.update_enable_state)
        self.form_layout.addRow(QLabel("启用插件:"), self.enable_checkbox)
        
        # 参数显示和编辑
        parameters = self.plugin_config.get('parameters', [])
        
        # 添加参数设置
        for param in parameters:
            name = param.get('name', '')
            description = param.get('description', '')
            required = param.get('required', False)
            
            # 跳过必填参数，这些应该由用户在消息中提供
            if required:
                continue
                
            # 获取默认值
            default_value = param.get('default', '')
            
            # 不同类型参数的不同处理
            if "path" in name.lower() and "weight" in name.lower():
                self.add_path_field(name, description, default_value, is_weight=True)
            elif "path" in name.lower():
                self.add_path_field(name, description, default_value, is_weight=False)
            elif "is_" in name.lower():
                self.add_checkbox_field(name, description, default_value)
            else:
                self.add_text_field(name, description, default_value)
        
        # 显示设置区域和按钮
        self.settings_form.show()
        self.toggle_btn.setVisible(is_load)  # 只有已加载的插件才显示启用/禁用按钮
        if is_load:
            self.toggle_btn.setText("禁用插件" if enable else "启用插件")
    
    def clear(self):
        """清空详情页"""
        self.plugin_name = None
        self.plugin_config = {}
        self.title_label.setText("选择插件查看详情")
        
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)
        
        self.current_config_fields = {}
        self.settings_form.hide()
        self.toggle_btn.hide()
    
    def add_text_field(self, name, description, default_value):
        """添加文本输入字段"""
        field = QLineEdit()
        field.setPlaceholderText(description)
        if default_value:
            field.setText(str(default_value))
        field.textChanged.connect(lambda text: self.update_parameter(name, text))
        self.form_layout.addRow(QLabel(f"{name} :"), field)
        self.current_config_fields[name] = field
    
    def add_checkbox_field(self, name, description, default_value):
        """添加复选框字段"""
        field = QCheckBox()
        field.setToolTip(description)
        if isinstance(default_value, bool):
            field.setChecked(default_value)
        field.toggled.connect(lambda state: self.update_parameter(name, state))
        self.form_layout.addRow(QLabel(f"{name}:"), field)
        self.current_config_fields[name] = field
    
    def add_path_field(self, name, description, default_value, is_weight=False):
        """添加路径选择字段"""
        param_layout = QHBoxLayout()
        field = QLineEdit()
        field.setPlaceholderText(f"默认路径: {description}")
        if default_value:
            field.setText(str(default_value))
        field.textChanged.connect(lambda text: self.update_parameter(name, text))
        
        button_text = "浏览..." if not is_weight else "选择权重文件..."
        browse_btn = QPushButton(button_text)
        if is_weight:
            browse_btn.clicked.connect(lambda: self.browse_weight_file(field))
        else:
            browse_btn.clicked.connect(lambda: self.browse_path(field))
        
        param_layout.addWidget(field)
        param_layout.addWidget(browse_btn)
        
        container = QWidget()
        container.setLayout(param_layout)
        
        self.form_layout.addRow(QLabel(f"{name}:"), container)
        self.current_config_fields[name] = field
    
    def update_parameter(self, param_name, value):
        """更新参数值并发出信号"""
        changes = {'parameters': {param_name: value}}
        self.plugin_changed.emit(self.plugin_name, changes)
    
    def update_plugin_config(self, key, value):
        """更新插件配置并发出信号"""
        changes = {key: value}
        self.plugin_changed.emit(self.plugin_name, changes)
    
    def update_enable_state(self, is_checked):
        """更新启用状态复选框"""
        self.enable_checkbox.setEnabled(is_checked)
        if not is_checked:
            self.enable_checkbox.setChecked(False)
            self.update_plugin_config('enable', False)
    
    def toggle_plugin(self):
        """切换插件启用状态"""
        new_state = not self.enable_checkbox.isChecked()
        self.enable_checkbox.setChecked(new_state)
        self.update_plugin_config('enable', new_state)
        self.toggle_btn.setText("禁用插件" if new_state else "启用插件")
    
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
