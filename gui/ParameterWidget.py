from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QComboBox, QPushButton, QCheckBox, 
                               QFileDialog, QFormLayout, QGroupBox)
from PySide6.QtCore import Signal

class ParameterWidget(QWidget):
    """动态参数输入组件"""
    
    parameters_ready = Signal(dict)  # 参数准备好时发出的信号
    
    def __init__(self):
        super().__init__()
        self.parameter_fields = {}  # 存储参数控件的字典
        self.setup_ui()
    
    def setup_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # 标题
        self.title_label = QLabel("请补充任务参数:")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.layout.addWidget(self.title_label)
        
        # 参数表单容器
        self.form_group = QGroupBox()
        self.form_layout = QFormLayout(self.form_group)
        self.layout.addWidget(self.form_group)
        
        # 确认按钮
        self.confirm_btn = QPushButton("确认参数")
        self.confirm_btn.clicked.connect(self.confirm_parameters)
        self.layout.addWidget(self.confirm_btn)
        
        # 初始状态下隐藏
        self.hide()
    
    def setup_parameters(self, parameters):
        """根据参数配置设置界面控件"""
        # 清除现有表单控件
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)
        
        self.parameter_fields.clear()
        
        # 为每个参数创建对应的输入控件
        for param in parameters:
            name = param["name"]
            description = param["description"]
            required = param.get("required", False)
            
            # 标签
            label_text = f"{name} {'(必填)' if required else '(可选)'}"
            label = QLabel(label_text)
            
            # 根据参数名称创建不同的控件
            if "path" in name.lower() or "file" in name.lower():
                # 文件选择
                param_layout = QHBoxLayout()
                field = QLineEdit()
                field.setPlaceholderText(description)
                
                browse_btn = QPushButton("浏览...")
                browse_btn.clicked.connect(lambda _, f=field: self.browse_file(f))
                
                param_layout.addWidget(field)
                param_layout.addWidget(browse_btn)
                
                container = QWidget()
                container.setLayout(param_layout)
                self.form_layout.addRow(label, container)
                self.parameter_fields[name] = field
                
            elif "is_" in name.lower() or name.lower().startswith("show") or "enable" in name.lower():
                # 布尔值选择
                field = QCheckBox()
                if description:
                    field.setToolTip(description)
                self.form_layout.addRow(label, field)
                self.parameter_fields[name] = field
                
            else:
                # 默认文本输入
                field = QLineEdit()
                field.setPlaceholderText(description)
                self.form_layout.addRow(label, field)
                self.parameter_fields[name] = field
        
        # 显示参数表单
        self.show()
    
    def browse_file(self, field):
        """打开文件浏览对话框"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", "所有文件 (*)"
        )
        if file_path:
            field.setText(file_path)
    
    def confirm_parameters(self):
        """确认并收集参数值"""
        parameters = {}
        
        for name, field in self.parameter_fields.items():
            if isinstance(field, QLineEdit):
                value = field.text()
                if value:  # 只添加非空参数
                    parameters[name] = value
            elif isinstance(field, QCheckBox):
                parameters[name] = field.isChecked()
        
        self.parameters_ready.emit(parameters)
        self.hide()  # 隐藏参数面板
