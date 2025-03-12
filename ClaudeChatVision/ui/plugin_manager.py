from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                              QLabel, QListWidget, QListWidgetItem,
                              QStackedWidget, QCheckBox, QFormLayout,
                              QLineEdit, QComboBox, QPushButton, QGroupBox,
                              QScrollArea, QSplitter)
from PySide6.QtCore import Qt, Signal

class PluginConfigWidget(QWidget):
    """插件配置小部件
    
    为单个插件提供配置界面，根据插件参数定义动态创建表单控件。
    允许用户修改插件设置并保存更改。
    不同参数类型会使用不同的输入控件，如文本框、复选框和下拉选择框等。
    """
    settings_saved = Signal(dict)  # 当设置被保存时发出的信号，携带设置字典
    
    def __init__(self, plugin_info, parent=None):
        """初始化插件配置小部件
        
        参数:
            plugin_info (dict): 包含插件信息和参数定义的字典
            parent (QWidget): 父级小部件
        """
        super().__init__(parent)
        self.plugin_info = plugin_info
        self.setup_ui()
        
    def setup_ui(self):
        """设置配置界面UI
        
        根据插件参数定义动态创建表单控件，并添加保存按钮。
        支持文本、数字、复选框和下拉选择等多种参数类型。
        每个参数会创建对应的标签和输入控件。
        """
        layout = QFormLayout(self)
        
        # 根据插件的参数创建表单字段
        self.param_widgets = {}
        
        for param_name, param_info in self.plugin_info.get("parameters", {}).items():
            param_type = param_info.get("type", "text")
            default_value = param_info.get("default", "")
            label = QLabel(param_info.get("label", param_name))
            
            if param_type == "text":
                widget = QLineEdit(default_value)
            elif param_type == "number":
                widget = QLineEdit(str(default_value))
                widget.setValidator(QIntValidator())  # 仅允许输入整数
            elif param_type == "checkbox":
                widget = QCheckBox()
                widget.setChecked(bool(default_value))
            elif param_type == "select":
                widget = QComboBox()
                widget.addItems(param_info.get("options", []))
                if default_value and default_value in param_info.get("options", []):
                    widget.setCurrentText(default_value)
            else:
                widget = QLineEdit(str(default_value))
            
            self.param_widgets[param_name] = widget
            layout.addRow(label, widget)
        
        # 添加保存按钮
        save_button = QPushButton("保存设置")
        save_button.clicked.connect(self.save_settings)
        layout.addRow("", save_button)
        
    def save_settings(self):
        """保存设置并发出信号
        
        从表单控件中收集所有值，构建设置字典并发出信号通知更改。
        根据控件类型正确获取值（文本、复选框状态、下拉选择）。
        还会提供反馈信息表明设置已被保存。
        """
        # 从表单控件中获取所有值
        settings = {}
        for param_name, widget in self.param_widgets.items():
            if isinstance(widget, QLineEdit):
                settings[param_name] = widget.text()
            elif isinstance(widget, QCheckBox):
                settings[param_name] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                settings[param_name] = widget.currentText()
        
        # 发出包含新设置的信号
        self.settings_saved.emit(settings)
        
        # 向用户提供反馈
        print(f"保存插件{self.plugin_info['name']}的设置: {settings}")


class PluginManagerWindow(QWidget):
    """插件管理器窗口
    
    提供可用视觉处理插件的管理界面，允许用户启用/禁用插件和配置插件参数。
    使用分割视图显示插件列表和当前选中插件的详细设置。
    左侧显示所有可用插件的列表，右侧显示当前选中插件的详细设置。
    """
    plugin_settings_changed = Signal(str, dict)  # 插件设置更改信号，参数为plugin_id和settings
    plugin_enabled_changed = Signal(str, bool)   # 插件启用状态更改信号，参数为plugin_id和enabled状态
    
    def __init__(self, task_processor):
        """初始化插件管理器窗口
        
        参数:
            task_processor: 任务处理器实例，用于获取和更新插件配置
        """
        super().__init__()
        self.task_processor = task_processor
        
        # 示例插件数据，用于演示
        # 在实际应用中，这些数据应该从任务处理器或插件系统获取
        self.plugins = [
            {
                "id": "yolo",
                "name": "YOLO物体检测",
                "enabled": True,
                "description": "使用YOLO在图像中检测物体",
                "parameters": {
                    "model": {
                        "label": "模型版本",
                        "type": "select", 
                        "options": ["YOLOv5s", "YOLOv5m", "YOLOv5l", "YOLOv5x"],
                        "default": "YOLOv5s"
                    },
                    "confidence": {
                        "label": "置信度阈值",
                        "type": "text",
                        "default": "0.5"
                    },
                    "output_dir": {
                        "label": "输出目录",
                        "type": "text",
                        "default": "d:/Code/ChatVision/output"
                    }
                }
            },
            {
                "id": "pose",
                "name": "姿态估计",
                "enabled": True,
                "description": "估计图像中的人体姿态",
                "parameters": {
                    "model": {
                        "label": "模型版本",
                        "type": "select",
                        "options": ["MoveNet", "BlazePose", "OpenPose"],
                        "default": "MoveNet"
                    },
                    "output_dir": {
                        "label": "输出目录",
                        "type": "text",
                        "default": "d:/Code/ChatVision/output"
                    }
                }
            },
            {
                "id": "blip",
                "name": "BLIP图像描述",
                "enabled": True,
                "description": "为图像生成描述文本",
                "parameters": {
                    "model_size": {
                        "label": "模型大小",
                        "type": "select",
                        "options": ["小型", "中型", "大型"],
                        "default": "中型"
                    },
                    "language": {
                        "label": "输出语言",
                        "type": "select",
                        "options": ["英文", "中文", "西班牙文"],
                        "default": "中文"
                    }
                }
            }
        ]
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置插件管理器UI
        
        创建水平分割的界面：左侧显示插件列表，右侧显示选中插件的详细信息和配置选项。
        使用QSplitter允许用户调整左右两侧的宽度比例。
        """
        layout = QHBoxLayout(self)
        
        # 创建列表和详情分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：插件列表
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_label = QLabel("可用插件")
        list_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        self.plugin_list = QListWidget()
        self.plugin_list.setMinimumWidth(200)
        self.plugin_list.currentRowChanged.connect(self.on_plugin_selected)
        
        list_layout.addWidget(list_label)
        list_layout.addWidget(self.plugin_list)
        
        # 右侧：插件详情和配置
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        self.plugin_title = QLabel("选择一个插件")
        self.plugin_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.plugin_description = QLabel("")
        
        self.enabled_checkbox = QCheckBox("启用")
        self.enabled_checkbox.toggled.connect(self.on_plugin_enabled_changed)
        
        # 为配置创建滚动区域
        self.config_scroll = QScrollArea()
        self.config_scroll.setWidgetResizable(True)
        self.stacked_widget = QStackedWidget()
        self.config_scroll.setWidget(self.stacked_widget)
        
        details_layout.addWidget(self.plugin_title)
        details_layout.addWidget(self.plugin_description)
        details_layout.addWidget(self.enabled_checkbox)
        details_layout.addWidget(QLabel("插件配置:"))
        details_layout.addWidget(self.config_scroll)
        
        # 将小部件添加到分割器
        splitter.addWidget(list_widget)
        splitter.addWidget(details_widget)
        splitter.setSizes([200, 400])  # 设置初始分割比例
        
        layout.addWidget(splitter)
        
        # 填充插件列表
        self.populate_plugins()
        
    def populate_plugins(self):
        """填充插件列表
        
        清空并重新填充插件列表，为每个插件创建配置小部件。
        禁用的插件在列表中显示为灰色。
        为每个插件创建一个配置小部件并添加到堆叠小部件中。
        """
        self.plugin_list.clear()
        
        for plugin in self.plugins:
            item = QListWidgetItem(plugin["name"])
            item.setData(Qt.UserRole, plugin["id"])
            
            # 禁用的插件显示为灰色
            if not plugin["enabled"]:
                item.setForeground(Qt.gray)
                
            self.plugin_list.addItem(item)
            
            # 为此插件创建配置小部件并添加到堆叠小部件中
            config_widget = PluginConfigWidget(plugin)
            self.stacked_widget.addWidget(config_widget)
    
    def on_plugin_selected(self, row):
        """处理选择插件的事件
        
        当用户从列表中选择插件时，更新右侧面板显示该插件的详细信息。
        连接选中插件的设置保存信号。
        
        参数:
            row (int): 选中的插件行索引
        """
        if row < 0:
            return
        
        plugin_id = self.plugin_list.item(row).data(Qt.UserRole)
        plugin = next((p for p in self.plugins if p["id"] == plugin_id), None)
        
        if plugin:
            self.plugin_title.setText(plugin["name"])
            self.plugin_description.setText(plugin["description"])
            self.enabled_checkbox.setChecked(plugin["enabled"])
            self.stacked_widget.setCurrentIndex(row)
            
            # 为当前选中的插件连接设置保存信号
            config_widget = self.stacked_widget.widget(row)
            if isinstance(config_widget, PluginConfigWidget):
                # 如果已经连接信号，先断开以避免多次连接
                if config_widget.receivers(config_widget.settings_saved) > 0:
                    config_widget.settings_saved.disconnect()
                config_widget.settings_saved.connect(
                    lambda settings: self.on_plugin_settings_saved(plugin_id, settings)
                )
    
    def on_plugin_enabled_changed(self, enabled):
        """处理插件启用状态更改
        
        当用户切换插件的启用/禁用状态时，更新插件数据和UI显示。
        发出信号通知任务处理器插件状态的变更。
        
        参数:
            enabled (bool): 新的启用状态
        """
        row = self.plugin_list.currentRow()
        if row >= 0:
            plugin_id = self.plugin_list.item(row).data(Qt.UserRole)
            for plugin in self.plugins:
                if plugin["id"] == plugin_id:
                    plugin["enabled"] = enabled
                    
                    # 更新列表项的外观
                    self.plugin_list.item(row).setForeground(Qt.black if enabled else Qt.gray)
                    
                    # 通知任务处理器
                    self.plugin_enabled_changed.emit(plugin_id, enabled)
                    break
    
    def on_plugin_settings_saved(self, plugin_id, settings):
        """处理插件设置保存
        
        当用户保存插件设置时，将这些设置转发给任务处理器。
        
        参数:
            plugin_id (str): 插件ID
            settings (dict): 新的设置值
        """
        # 将插件设置转发到任务处理器
        self.plugin_settings_changed.emit(plugin_id, settings)
