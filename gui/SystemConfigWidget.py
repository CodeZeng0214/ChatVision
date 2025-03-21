from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QLineEdit, QFormLayout, QGroupBox, QPushButton,
                              QSpinBox, QMessageBox)
from PySide6.QtCore import Qt, Signal

from core.SystemConfig import system_config

class SystemConfigWidget(QWidget):
    """系统配置界面组件"""
    
    config_changed = Signal()  # 配置变更信号
    
    def __init__(self):
        super().__init__()
        self.modified = False  # 是否有未保存的修改
        self.setup_ui()
        self.load_config_to_ui()
    
    def setup_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 添加分组：聊天机器人设置
        chat_robot_group = QGroupBox(system_config.get_label("chat_robot"))
        chat_robot_form = QFormLayout(chat_robot_group)
        
        self.init_message_edit = QLineEdit()
        self.init_message_edit.textChanged.connect(lambda: self.mark_modified())
        chat_robot_form.addRow(system_config.get_label("init_message"), self.init_message_edit)
        
        self.max_attempts_spinbox = QSpinBox()
        self.max_attempts_spinbox.setRange(1, 10)
        self.max_attempts_spinbox.valueChanged.connect(lambda: self.mark_modified())
        chat_robot_form.addRow(system_config.get_label("analyze_max_attempts"), self.max_attempts_spinbox)
        
        layout.addWidget(chat_robot_group)
        
        # 添加分组：插件管理器设置
        plugin_manager_group = QGroupBox(system_config.get_label("plugin_manager"))
        plugin_manager_form = QFormLayout(plugin_manager_group)
        
        self.plugins_config_path_edit = QLineEdit()
        self.plugins_config_path_edit.textChanged.connect(lambda: self.mark_modified())
        plugin_manager_form.addRow(system_config.get_label("plugins_config_path"), self.plugins_config_path_edit)
        
        layout.addWidget(plugin_manager_group)
        
        # 添加分组：聊天接口设置
        chat_interface_group = QGroupBox(system_config.get_label("chat_interface"))
        chat_interface_form = QFormLayout(chat_interface_group)
        
        self.api_url_edit = QLineEdit()
        self.api_url_edit.textChanged.connect(lambda: self.mark_modified())
        chat_interface_form.addRow(system_config.get_label("api_url"), self.api_url_edit)
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)  # 密码模式显示
        self.api_key_edit.textChanged.connect(lambda: self.mark_modified())
        chat_interface_form.addRow(system_config.get_label("api_key"), self.api_key_edit)
        
        self.model_name_edit = QLineEdit()
        self.model_name_edit.textChanged.connect(lambda: self.mark_modified())
        chat_interface_form.addRow(system_config.get_label("model_name"), self.model_name_edit)
        
        layout.addWidget(chat_interface_group)
        
        # 按钮区域
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("保存设置")
        self.save_btn.clicked.connect(self.save_config)
        self.save_btn.setEnabled(False)  # 初始状态禁用
        buttons_layout.addWidget(self.save_btn)
        
        self.reset_btn = QPushButton("重置为默认")
        self.reset_btn.clicked.connect(self.reset_to_default)
        buttons_layout.addWidget(self.reset_btn)
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
    
    def load_config_to_ui(self):
        """将配置加载到UI控件"""
        # 聊天机器人设置
        self.init_message_edit.setText(system_config.get_value("chat_robot", "init_message", ""))
        self.max_attempts_spinbox.setValue(system_config.get_value("chat_robot", "analyze_max_attempts", 3))
        
        # 插件管理器设置
        self.plugins_config_path_edit.setText(system_config.get_value("plugin_manager", "plugins_config_path", ""))
        
        # 聊天接口设置
        self.api_url_edit.setText(system_config.get_value("chat_interface", "api_url", ""))
        self.api_key_edit.setText(system_config.get_value("chat_interface", "api_key", ""))
        self.model_name_edit.setText(system_config.get_value("chat_interface", "model_name", ""))
        
        self.modified = False
        self.save_btn.setEnabled(False)
    
    def save_config(self):
        """保存配置"""
        # 聊天机器人设置
        system_config.set_value("chat_robot", "init_message", self.init_message_edit.text())
        system_config.set_value("chat_robot", "analyze_max_attempts", self.max_attempts_spinbox.value())
        
        # 插件管理器设置
        system_config.set_value("plugin_manager", "plugins_config_path", self.plugins_config_path_edit.text())
        
        # 聊天接口设置
        system_config.set_value("chat_interface", "api_url", self.api_url_edit.text())
        system_config.set_value("chat_interface", "api_key", self.api_key_edit.text())
        system_config.set_value("chat_interface", "model_name", self.model_name_edit.text())
        
        # 保存到文件
        if system_config.save_config():
            QMessageBox.information(self, "成功", "配置已保存，部分设置将在应用重启后生效")
            self.modified = False
            self.save_btn.setEnabled(False)
            self.config_changed.emit()
        else:
            QMessageBox.warning(self, "错误", "保存配置失败")
    
    def reset_to_default(self):
        """重置为默认设置"""
        reply = QMessageBox.question(self, "确认", "确定要重置所有设置为默认值吗？", 
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            default_config = system_config.get_default_config()
            system_config.config = default_config
            self.load_config_to_ui()
            self.mark_modified()
    
    def mark_modified(self):
        """标记有未保存的修改"""
        self.modified = True
        self.save_btn.setEnabled(True)
