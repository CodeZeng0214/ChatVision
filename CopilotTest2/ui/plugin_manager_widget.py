from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QListWidget, QListWidgetItem, QCheckBox,
                              QDialog, QFormLayout, QLineEdit, QGroupBox, 
                              QFileDialog, QTabWidget, QScrollArea)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon

class PluginConfigDialog(QDialog):
    """插件配置对话框"""
    
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.config_widgets = {}
        self.setWindowTitle(f"配置插件 - {plugin.name}")
        self.setMinimumWidth(500)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 插件信息
        info_group = QGroupBox("插件信息")
        info_layout = QFormLayout(info_group)
        info_layout.addRow("名称:", QLabel(self.plugin.name))
        info_layout.addRow("描述:", QLabel(self.plugin.description))
        
        # 添加插件自定义配置UI如果有
        custom_ui = self.plugin.get_config_ui()
        if custom_ui:
            layout.addWidget(info_group)
            layout.addWidget(custom_ui)
        else:
            # 否则显示简单配置表单
            config_group = QGroupBox("配置参数")
            config_layout = QFormLayout(config_group)
            
            # 遍历插件配置
            for key, value in self.plugin.config.items():
                # 创建编辑控件
                if isinstance(value, bool):
                    widget = QCheckBox()
                    widget.setChecked(value)
                elif isinstance(value, (int, float)):
                    widget = QLineEdit(str(value))
                    # 设置验证器
                    if isinstance(value, int):
                        from PySide6.QtGui import QIntValidator
                        widget.setValidator(QIntValidator())
                    else:
                        from PySide6.QtGui import QDoubleValidator
                        widget.setValidator(QDoubleValidator())
                else:
                    widget = QLineEdit(str(value))
                
                # 如果是路径类型的配置，添加浏览按钮
                if "path" in key.lower() or "dir" in key.lower():
                    path_layout = QHBoxLayout()
                    path_layout.addWidget(widget)
                    browse_btn = QPushButton("浏览...")
                    browse_btn.clicked.connect(lambda checked, w=widget, k=key: self._browse_path(w, k))
                    path_layout.addWidget(browse_btn)
                    config_layout.addRow(key, path_layout)
                else:
                    config_layout.addRow(key, widget)
                
                self.config_widgets[key] = widget
            
            layout.addWidget(info_group)
            layout.addWidget(config_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def _browse_path(self, widget, key):
        """浏览文件或目录"""
        if "dir" in key.lower():
            # 目录选择
            path = QFileDialog.getExistingDirectory(self, f"选择{key}")
        else:
            # 文件选择
            path, _ = QFileDialog.getOpenFileName(self, f"选择{key}")
        
        if path:
            widget.setText(path)
    
    def get_config(self):
        """获取用户设置的配置"""
        config = {}
        
        for key, widget in self.config_widgets.items():
            if isinstance(widget, QCheckBox):
                config[key] = widget.isChecked()
            elif isinstance(widget, QLineEdit):
                # 尝试转换为原始类型
                text = widget.text()
                orig_value = self.plugin.config[key]
                
                if isinstance(orig_value, int):
                    try:
                        config[key] = int(text)
                    except ValueError:
                        config[key] = 0
                elif isinstance(orig_value, float):
                    try:
                        config[key] = float(text)
                    except ValueError:
                        config[key] = 0.0
                else:
                    config[key] = text
        
        return config


class PluginInstallDialog(QDialog):
    """插件安装对话框"""
    
    def __init__(self, plugin_manager, parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        self.setWindowTitle("安装新插件")
        self.setMinimumWidth(500)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 插件文件选择
        file_group = QGroupBox("选择插件文件")
        file_layout = QHBoxLayout(file_group)
        
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_plugin)
        
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(browse_btn)
        
        layout.addWidget(file_group)
        
        # 插件信息
        self.info_group = QGroupBox("插件信息")
        self.info_group.setVisible(False)
        info_layout = QFormLayout(self.info_group)
        
        self.info_name = QLabel()
        self.info_desc = QLabel()
        self.info_type = QLabel()
        
        info_layout.addRow("名称:", self.info_name)
        info_layout.addRow("描述:", self.info_desc)
        info_layout.addRow("类型:", self.info_type)
        
        layout.addWidget(self.info_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        
        self.install_btn = QPushButton("安装")
        self.install_btn.clicked.connect(self.accept)
        self.install_btn.setEnabled(False)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.install_btn)
        
        layout.addLayout(button_layout)
    
    def _browse_plugin(self):
        """浏览插件文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择插件文件", 
            "", 
            "Python文件 (*.py)"
        )
        
        if file_path:
            self.file_path.setText(file_path)
            
            # TODO: 解析插件信息
            # 实际实现中需要分析插件文件，提取插件类信息
            # 这里简化处理
            self.info_name.setText(file_path.split("/")[-1].replace(".py", ""))
            self.info_desc.setText("插件描述待提取")
            self.info_type.setText("未知类型")
            
            self.info_group.setVisible(True)
            self.install_btn.setEnabled(True)
    
    def get_plugin_path(self):
        """获取选择的插件路径"""
        return self.file_path.text()


class PluginListItem(QWidget):
    """插件列表项"""
    
    config_clicked = Signal(object)  # 插件对象信号
    toggle_clicked = Signal(object, bool)  # 插件对象、启用状态信号
    
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 启用/禁用复选框
        self.enabled_check = QCheckBox(self.plugin.name)
        self.enabled_check.setChecked(self.plugin.is_enabled())
        self.enabled_check.toggled.connect(self._on_toggle)
        
        # 描述标签
        desc_label = QLabel(self.plugin.description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: gray;")
        
        # 配置按钮
        config_btn = QPushButton("配置")
        config_btn.clicked.connect(self._on_config)
        
        # 垂直布局放置插件名称和描述
        text_layout = QVBoxLayout()
        text_layout.addWidget(self.enabled_check)
        text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        layout.addWidget(config_btn)
    
    def _on_toggle(self, checked):
        """启用/禁用复选框点击"""
        self.toggle_clicked.emit(self.plugin, checked)
    
    def _on_config(self):
        """配置按钮点击"""
        self.config_clicked.emit(self.plugin)
    
    def update_state(self):
        """更新状态"""
        self.enabled_check.setChecked(self.plugin.is_enabled())


class PluginManagerWidget(QWidget):
    """插件管理界面"""
    
    def __init__(self, plugin_manager):
        super().__init__()
        self.plugin_manager = plugin_manager
        self.plugin_items = {}  # 存储插件项: {plugin_name: PluginListItem}
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 标题
        title_layout = QHBoxLayout()
        title_label = QLabel("插件管理")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        
        # 安装按钮
        install_btn = QPushButton("安装插件")
        install_btn.clicked.connect(self._on_install)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(install_btn)
        
        layout.addLayout(title_layout)
        
        # 插件分类标签页
        self.tabs = QTabWidget()
        
        # 创建分类标签页
        self._create_plugin_tabs()
        
        layout.addWidget(self.tabs)
    
    def _create_plugin_tabs(self):
        """创建插件分类标签页"""
        # 清空现有标签页
        self.tabs.clear()
        self.plugin_items = {}
        
        # 创建"所有插件"标签页
        all_tab = QWidget()
        all_layout = QVBoxLayout(all_tab)
        
        all_list = QListWidget()
        all_list.setSpacing(2)
        
        all_layout.addWidget(all_list)
        
        # 创建插件类型分类
        plugin_types = {}
        
        # 加载插件
        for plugin in self.plugin_manager.get_plugins():
            # 创建列表项
            list_item = QListWidgetItem(all_list)
            
            # 创建自定义部件
            item_widget = PluginListItem(plugin)
            item_widget.config_clicked.connect(self._on_config_plugin)
            item_widget.toggle_clicked.connect(self._on_toggle_plugin)
            
            list_item.setSizeHint(item_widget.sizeHint())
            all_list.setItemWidget(list_item, item_widget)
            
            # 保存项
            self.plugin_items[plugin.name] = item_widget
            
            # 按类型分类
            task_types = plugin.get_task_types()
            if task_types:
                for task_type in task_types:
                    if task_type not in plugin_types:
                        plugin_types[task_type] = []
                    plugin_types[task_type].append(plugin)
        
        # 添加"所有插件"标签页
        self.tabs.addTab(all_tab, "所有插件")
        
        # 添加分类标签页
        for task_type, plugins in plugin_types.items():
            type_tab = QWidget()
            type_layout = QVBoxLayout(type_tab)
            
            type_list = QListWidget()
            type_list.setSpacing(2)
            
            for plugin in plugins:
                # 创建列表项
                list_item = QListWidgetItem(type_list)
                
                # 复用已创建的部件
                item_widget = self.plugin_items[plugin.name]
                
                list_item.setSizeHint(item_widget.sizeHint())
                type_list.setItemWidget(list_item, item_widget)
            
            type_layout.addWidget(type_list)
            
            # 添加标签页
            self.tabs.addTab(type_tab, task_type)
    
    def _on_config_plugin(self, plugin):
        """配置插件"""
        dialog = PluginConfigDialog(plugin, self)
        
        if dialog.exec_():
            # 用户确认，保存配置
            config = dialog.get_config()
            success = self.plugin_manager.configure_plugin(plugin.name, config)
            
            if success:
                # TODO: 显示成功提示
                pass
    
    def _on_toggle_plugin(self, plugin, enabled):
        """启用/禁用插件"""
        if enabled:
            success = self.plugin_manager.enable_plugin(plugin.name)
        else:
            success = self.plugin_manager.disable_plugin(plugin.name)
            
        # 更新UI显示
        if not success:
            # 恢复复选框状态
            item_widget = self.plugin_items.get(plugin.name)
            if item_widget:
                item_widget.update_state()
    
    def _on_install(self):
        """安装插件"""
        dialog = PluginInstallDialog(self.plugin_manager, self)
        
        if dialog.exec_():
            # TODO: 实现插件安装逻辑
            plugin_path = dialog.get_plugin_path()
            # 显示安装中...
            # 安装插件
            # 重新加载插件列表
            self.refresh_plugins()
    
    def refresh_plugins(self):
        """刷新插件列表"""
        self._create_plugin_tabs()
