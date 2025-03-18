from PySide6.QtWidgets import (QListWidgetItem, QLabel, QCheckBox, QLineEdit, 
                              QWidget, QHBoxLayout, QPushButton, QFormLayout,
                              QFileDialog, QVBoxLayout, QGroupBox, QScrollArea)
from PySide6.QtCore import Qt, Signal, QObject
from copy import deepcopy

# 因为QListWidgetItem不继承自QObject，无法发出信号，所以创建一个信号代理
class PluginItemSignals(QObject):
    """插件列表项信号代理\n
    config_changed: 配置变更时发出信号\n
    save_needed: 需要保存时发出信号"""
    config_changed = Signal(str)  # 当配置变更时发出信号
    save_needed = Signal(bool)    # 当需要保存时发出信号

class PluginListWidgetItem(QListWidgetItem):
    """表示插件列表中的一个项目，包含完整的插件配置和修改状态，并管理详情视图\n
    必选参数:\n
        plugin_name (str): 插件名称\n
        plugin_config (dict): 插件配置\n
        detail_view (QWidget): 详情视图容器"""
    
    def __init__(self, plugin_name, plugin_config=None, detail_view:QWidget=None):
        """
        初始化插件列表项
        \n
        参数:\n
            plugin_name (str): 插件名称\n
            plugin_config (dict): 插件配置\n
            detail_view (QWidget): 详情视图容器
        """
        super().__init__(plugin_name)
        self.plugin_name = plugin_name
        self._config = plugin_config or {}
        self.is_load = self._config.get('is_load', True)
        self.enable = self._config.get('enable', True)
        self._pending_changes = {}  # 存储未保存的修改
        self.signals = PluginItemSignals()  # 信号代理
        
        # 详情视图相关属性
        self.detail_view = detail_view        # 详情视图容器
        
        # 初始化详情视图
        self.init_plugin_item()
        
    def init_plugin_item(self):
        """初始化插件列表项"""
        # 创建详情视图
        self.create_detail_view(self.detail_view)
        self.update_appearance()
    
    def create_detail_view(self, container:QWidget):
        """
        在给定的容器中创建详情视图
        
        参数:
            container: 用于放置详情视图的容器控件
        """
        # 清除容器中可能存在的内容
        if container.layout():
            while container.layout().count():
                item = container.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            QWidget().setLayout(container.layout())
        
        # 设置新的布局
        detail_layout = QVBoxLayout(container)
        
        # 插件标题
        self.detail_title = QLabel(f"插件: {self.plugin_name}")
        self.detail_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        detail_layout.addWidget(self.detail_title)
        
        # 创建滚动区域以支持内容过多时滚动
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # 创建设置表单容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # 插件设置表单
        self.settings_form = QGroupBox("插件设置")
        self.form_layout = QFormLayout(self.settings_form)
        content_layout.addWidget(self.settings_form)
        
        # 填充表单内容
        self._populate_form()
        
        # 启用/禁用按钮
        self.toggle_btn = QPushButton("启用/禁用插件")
        self.toggle_btn.setEnabled(self.is_load)
        self.toggle_btn.setText("禁用插件" if self.enable else "启用插件")
        self.toggle_btn.clicked.connect(self._on_toggle_enable_clicked)
        content_layout.addWidget(self.toggle_btn)
        
        content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        detail_layout.addWidget(scroll_area)
        
        # 保存对详情视图的引用
        self.detail_view = container
        
        return container
    
    def _populate_form(self):
        """填充详情表单内容"""
        if not self.form_layout:
            return
            
        # 清空表单
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)
            
        # 获取插件配置
        config = self.get_config()
        
        # 添加描述
        description = config.get('description', '无描述')
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        self.form_layout.addRow(QLabel("描述:"), desc_label)
        
        # 创建加载状态复选框
        load_checkbox = QCheckBox()
        load_checkbox.setChecked(self.is_load)
        load_checkbox.toggled.connect(lambda state: self.update_load_or_enable(is_load=state))
        self.form_layout.addRow(QLabel("启动时加载:"), load_checkbox)
        
        # 创建启用状态复选框
        enable_checkbox = QCheckBox()
        enable_checkbox.setChecked(self.enable)
        enable_checkbox.setEnabled(self.is_load)
        enable_checkbox.toggled.connect(lambda state: self.update_load_or_enable(enable=state))
        load_checkbox.toggled.connect(lambda state: enable_checkbox.setEnabled(state))
        self.form_layout.addRow(QLabel("启用插件:"), enable_checkbox)
        
        # 添加参数配置
        parameters = config.get('parameters', [])
        for param in parameters:
            name = param.get('name', '')
            description = param.get('description', '')
            required = param.get('required', False)
            
            # 跳过必填参数
            if required:
                continue
                
            # 获取参数当前值
            value = self.get_parameter_value(name)
            
            # 根据参数类型创建控件
            if "path" in name.lower() and "weight" in name.lower():
                self.create_path_field(self.form_layout, name, description, value, is_weight=True)
            elif "path" in name.lower():
                self.create_path_field(self.form_layout, name, description, value, is_weight=False)
            elif "is_" in name.lower():
                self.create_checkbox_field(self.form_layout, name, description, value)
            else:
                self.create_text_field(self.form_layout, name, description, value)
    
    # 用于更新插件状态和参数
    def update_appearance(self):
        """根据加载和启用状态更新列表选择外观和提示"""
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
    
    def update_load_or_enable(self, is_load=None, enable=None):
        """
        更新插件启用或者加载的状态
        
        参数:
            is_load (bool, optional): 加载状态
            enable (bool, optional): 启用状态
        """
        modified = False # 是否有修改
        
        # 更新加载状态
        if is_load is not None and self.is_load != is_load:
            self.is_load = is_load
            if not is_load:
                self.enable = False
            modified = True
            
            # 记录未保存的修改
            self._pending_changes['is_load'] = is_load
            if not is_load:
                self._pending_changes['enable'] = False
                
        if enable is not None and self.is_load and self.enable != enable:
            self.enable = enable
            modified = True
            
            # 记录未保存的修改
            self._pending_changes['enable'] = enable
            
        if modified:
            self.update_appearance()
            self.update_enable_button()
            self.signals.config_changed.emit(self.plugin_name)
            self.signals.save_needed.emit(True)
    
    def update_parameters(self, param_name, value):
        """更新参数字典中的值"""
        # 创建未保存的参数修改字典
        if 'parameters' not in self._pending_changes:
            self._pending_changes['parameters'] = {}
            
        # 保存参数修改至未保存的参数修改字典
        self._pending_changes['parameters'][param_name] = value
        
        # 同时更新配置参数的默认值
        if 'parameters' in self._config:
            for param in self._config['parameters']:
                if param.get('name') == param_name:
                    param['default'] = value
                    break
                    
        # 通知有修改
        self.signals.config_changed.emit(self.plugin_name)
        self.signals.save_needed.emit(True)
    
    def update_enable_button(self):
        """更新启用/禁用按钮状态"""
        if not self.detail_view:
            return
            
        # 更新启用/禁用按钮状态
        if self.toggle_btn:
            self.toggle_btn.setEnabled(self.is_load)
            self.toggle_btn.setText("禁用插件" if self.enable else "启用插件")
    
    def _on_toggle_enable_clicked(self):
        """处理启用/禁用按钮点击事件"""
        if self.is_load:
            self.update_load_or_enable(enable=not self.enable)
    
    # 用于获取和处理插件配置
    def get_config(self):
        """获取插件配置\n
        返回值: dict 插件配置的深拷贝"""
        return deepcopy(self._config)
    
    def get_parameter_value(self, param_name):
        """获取参数当前值，优先使用未保存的修改"""
        # 先查找未保存的修改
        if 'parameters' in self._pending_changes and param_name in self._pending_changes['parameters']:
            return self._pending_changes['parameters'][param_name]
            
        # 再查找配置中的默认值    
        if 'parameters' in self._config:
            for param in self._config['parameters']:
                if param.get('name') == param_name:
                    return param.get('default', '')
                    
        return ''
    
    # 用于处理未保存的修改
    def has_pending_changes(self)->bool:
        """检查是否有未保存的修改"""
        return bool(self._pending_changes)
    
    def get_pending_changes(self)->dict:
        """获取未保存的修改"""
        return deepcopy(self._pending_changes)
    
    def clear_pending_changes(self):
        """清除所有未保存的修改"""
        self._pending_changes = {}
        
    def apply_changes_to_config(self)->bool:
        """将未保存的修改应用到配置中\n
        返回值: bool 是否有修改"""
        if not self._pending_changes:
            return False
            
        # 更新配置的is_load和enable属性
        if 'is_load' in self._pending_changes:
            self._config['is_load'] = self._pending_changes['is_load']
            
        if 'enable' in self._pending_changes:
            self._config['enable'] = self._pending_changes['enable']
            
        # 更新参数设置
        if 'parameters' in self._pending_changes:
            for param_name, param_value in self._pending_changes['parameters'].items():
                for i, param in enumerate(self._config['parameters']):
                    if param.get('name') == param_name:
                        self._config['parameters'][i]['default'] = param_value
                        break
        return True
    
    # 参数类型创建控件的创建方法
    def create_text_field(self, form_layout:QFormLayout, name, description, value):
        """创建文本输入字段并添加到表单布局中"""
        field = QLineEdit()
        field.setPlaceholderText(description)
        if value:
            field.setText(str(value))
        field.textChanged.connect(lambda value: self.update_parameters(name, value))
        
        form_layout.addRow(QLabel(f"{name}:"), field)
        return field
    
    def create_checkbox_field(self, form_layout:QFormLayout, name, description, value):
        """创建复选框字段并添加到表单布局中"""
        field = QCheckBox()
        field.setToolTip(description)
        if isinstance(value, bool):
            field.setChecked(value)
        field.toggled.connect(lambda state: self.update_parameters(name, state))
        
        form_layout.addRow(QLabel(f"{name}:"), field)
        return field
    
    def create_path_field(self, form_layout:QFormLayout, name, description, value, is_weight=False):
        """创建路径选择字段并添加到表单布局中"""
        param_layout = QHBoxLayout()
        field = QLineEdit()
        field.setPlaceholderText(description)
        if value:
            field.setText(str(value))
        field.textChanged.connect(lambda value: self.update_parameters(name, value))
        
        # 浏览按钮
        button_text = "浏览..." if not is_weight else "选择权重文件..."
        browse_btn = QPushButton(button_text)
        
        # 使用自己的方法作为回调
        if is_weight:
            browse_btn.clicked.connect(lambda: self.browse_weight_file(field))
        else:
            browse_btn.clicked.connect(lambda: self.browse_path(field))
        
        param_layout.addWidget(field)
        param_layout.addWidget(browse_btn)
        
        container = QWidget()
        container.setLayout(param_layout)
        
        form_layout.addRow(QLabel(f"{name}:"), container)
        return field
    
    def browse_path(self, field):
        """打开目录浏览对话框"""
        path = QFileDialog.getExistingDirectory(None, "选择目录")
        if path:
            field.setText(path)
    
    def browse_weight_file(self, field):
        """打开文件浏览对话框选择权重文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            None, "选择权重文件", "", "模型权重文件 (*.pt *.pth *.weights);;所有文件 (*)"
        )
        if file_path:
            field.setText(file_path)