from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QListWidget, QListWidgetItem,
                               QGroupBox, QFormLayout, QLineEdit, QCheckBox,
                               QMessageBox)
from PySide6.QtCore import Qt, QTimer

from ChatRobot import ChatRobot
from core.TasksManager import TasksManager
from core.Task import Task

class PluginManagerWidget(QWidget):
    """插件管理界面"""
    
    def __init__(self):
        super().__init__()
        self.chat_robot = ChatRobot()
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
        
        # 清除现有表单
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)
        
        # 添加描述
        desc_label = QLabel(task.description)
        desc_label.setWordWrap(True)
        self.form_layout.addRow(QLabel("描述:"), desc_label)
        
        # 添加参数设置字段
        for param in task.parameters: 
            # （'可选'的参数才能进行配置）
            if param.get("required", True) is False:
                name = param["name"]
                description = param["description"]
                
                if "path" in name.lower():
                    field = QLineEdit()
                    field.setPlaceholderText(f"默认路径: {description}")
                    self.form_layout.addRow(f"{name}:", field)
                elif "is_" in name.lower():
                    field = QCheckBox()
                    field.setToolTip(description)
                    self.form_layout.addRow(f"{name}:", field)
        
        # 显示设置区域和按钮
        self.settings_form.show()
        self.toggle_btn.show()
        self.save_btn.show()
        
        # 根据任务启用状态更新按钮文本
        if task.enable:
            self.toggle_btn.setText("禁用插件")
        else:
            self.toggle_btn.setText("启用插件")
    
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
        """保存插件设置"""
        # 实际保存到配置文件
        try:
            self.chat_robot.task_manager.save_settings()
            self.save_btn.setText("设置已保存!")
            # 恢复按钮文字
            QTimer.singleShot(2000, lambda: self.save_btn.setText("保存设置"))
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"保存设置时发生错误: {e}")
    
    def import_plugin(self):
        """导入外部插件"""
        # 这里仅为界面演示，实际需要实现插件导入逻辑
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择插件文件", "", "Python文件 (*.py)"
        )
        
        if file_path:
            QMessageBox.information(self, "导入插件", "插件导入功能尚未实现")
