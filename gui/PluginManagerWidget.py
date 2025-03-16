from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QListWidget, QListWidgetItem,
                               QGroupBox, QFormLayout, QLineEdit, QCheckBox,
                               QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, QTimer
import json
import os

from ChatRobot import ChatRobot
from core.TasksManager import TasksManager
from core.Task import Task
from core.AuxiliaryFunction import PathCheck

class PluginManagerWidget(QWidget):
    """插件管理界面"""
    
    def __init__(self):
        super().__init__()
        self.chat_robot = ChatRobot()
        self.setup_ui()
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
        
        # 获取所有已注册的任务
        tasks = self.chat_robot.task_manager.tasks
        
        for task_name, task in tasks.items():
            item = QListWidgetItem(task_name)
            # 根据任务启用状态设置颜色
            if not task.enable:
                item.setForeground(Qt.gray)
            self.plugin_list.addItem(item)
    
    def show_plugin_details(self, row):
        """显示选中插件的详情"""
        if row < 0:
            return
        
        task_name = self.plugin_list.item(row).text()
        # 获取任务实例 (现在是Task对象，不是字典)
        task : Task = self.chat_robot.task_manager.tasks.get(task_name)
        
        if not task:
            return
        
        self.detail_label.setText(f"插件: {task_name}")
        self.current_task_name = task_name  # 存储当前正在编辑的任务名称
        
        # 清除现有表单和配置字段映射
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)
        self.current_config_fields = {}
        
        # 添加描述
        desc_label = QLabel(task.description)
        desc_label.setWordWrap(True)
        self.form_layout.addRow(QLabel("描述:"), desc_label)
        
        # 仅添加非必填参数的设置字段（只有optional参数可配置）
        for param in task.parameters:
            name = param["name"]
            description = param["description"]
            required = param.get("required", False)
            
            # 跳过必填参数，这些应该由用户在消息中提供
            if required:
                continue
                
            # 获取默认值
            default_value = param.get("default", "")
            
            # 不同类型参数的不同处理
            if "path" in name.lower() and "weight" in name.lower():
                param_layout = QHBoxLayout()
                field = QLineEdit()
                field.setPlaceholderText(f"默认路径: {description}")
                
                # 设置当前值（如果有）
                if default_value:
                    field.setText(str(default_value))
                
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
            elif "is_" in name.lower():
                field = QCheckBox()
                field.setToolTip(description)
                
                # 设置初始值（如果有）
                if isinstance(default_value, bool):
                    field.setChecked(default_value)
                
                self.form_layout.addRow(QLabel(f"{name} (可选):"), field)
                self.current_config_fields[name] = field
            else:
                field = QLineEdit()
                field.setPlaceholderText(f"{description}")
                
                # 设置初始值（如果有）
                if default_value:
                    field.setText(str(default_value))
                
                self.form_layout.addRow(QLabel(f"{name} (可选):"), field)
                self.current_config_fields[name] = field
        
        # 显示设置区域和按钮
        self.settings_form.show()
        self.toggle_btn.show()
        self.save_btn.show()
        
        # 根据任务启用状态更新按钮文本
        if task.enable:
            self.toggle_btn.setText("禁用插件")
        else:
            self.toggle_btn.setText("启用插件")
    
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
            task_name = item.text()
            
            # 切换任务的启用状态
            if self.chat_robot.task_manager.toggle_task(task_name):
                task = self.chat_robot.task_manager.tasks.get(task_name)
                if task.enable:
                    item.setForeground(Qt.black)  # 启用(黑色)
                    self.toggle_btn.setText("禁用插件")
                else:
                    item.setForeground(Qt.gray)  # 禁用(灰色)
                    self.toggle_btn.setText("启用插件")
    
    def save_plugin_settings(self):
        """保存插件设置到配置文件"""
        current_row = self.plugin_list.currentRow()
        if current_row < 0:
            return
            
        task_name = self.plugin_list.item(current_row).text()
        task = self.chat_robot.task_manager.tasks.get(task_name)
        
        if not task:
            return
            
        try:
            # 1. 读取配置文件
            config = self.read_config_file()
            if not config:
                QMessageBox.warning(self, "读取失败", "无法读取配置文件")
                return
                
            # 2. 收集用户修改的配置
            updated_params = {}
            for name, field in self.current_config_fields.items():
                if isinstance(field, QLineEdit) and field.text():
                    updated_params[name] = field.text()
                elif isinstance(field, QCheckBox):
                    updated_params[name] = field.isChecked()
            
            # 3. 更新任务配置
            if task_name in config:
                # 更新任务参数的默认值
                for param in config[task_name]["parameters"]:
                    if param["name"] in updated_params and not param.get("required", False):
                        param["default"] = updated_params[param["name"]]
                
                # 更新任务启用状态
                config[task_name]["enable"] = task.enable
                
                # 4. 将更新后的配置写入文件
                self.write_config_file(config)
                
                # 5. 更新任务对象
                for param in task.parameters:
                    if param["name"] in updated_params and not param.get("required", False):
                        param["default"] = updated_params[param["name"]]
                
                self.save_btn.setText("设置已保存!")
                # 恢复按钮文字
                QTimer.singleShot(2000, lambda: self.save_btn.setText("保存设置"))
                
                QMessageBox.information(self, "成功", "插件配置已成功保存!")
            else:
                QMessageBox.warning(self, "保存失败", f"配置文件中不存在任务 {task_name}")
                
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"保存设置时发生错误: {e}")
    
    def read_config_file(self):
        """从配置文件读取任务配置"""
        config_path = self.chat_robot.task_manager.tasks_config_path
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"读取配置文件失败: {e}")
            return {}
    
    def write_config_file(self, config):
        """将任务配置写入配置文件"""
        config_path = self.chat_robot.task_manager.tasks_config_path
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
