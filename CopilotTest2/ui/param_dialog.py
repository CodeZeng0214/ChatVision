from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QLineEdit, QFormLayout, QComboBox,
                              QFileDialog, QGroupBox, QMessageBox, QProgressBar)
from PySide6.QtCore import Qt, Signal
import os
from utils.i18n import _

class ParamDialog(QDialog):
    """参数输入对话框 - 增强版"""
    
    # 定义信号
    params_ready = Signal(dict)  # 参数准备好的信号
    
    def __init__(self, task_type, missing_params, parent=None):
        super().__init__(parent)
        self.task_type = task_type
        self.missing_params = missing_params
        self.param_values = {}
        self.param_widgets = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle(_("dialog.param_required") + f" - {self.get_task_display_name()}")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # 说明标签
        description = _("dialog.param_description").format(task=self.get_task_display_name())
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc_label)
        
        # 参数组
        param_group = QGroupBox(_("dialog.parameters"))
        param_layout = QFormLayout(param_group)
        
        # 为每个缺失参数创建输入控件
        for param in self.missing_params:
            self._create_param_widget(param, param_layout)
        
        layout.addWidget(param_group)
        
        # 处理进度条 (初始隐藏)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.cancel_btn = QPushButton(_("dialog.cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        
        self.ok_btn = QPushButton(_("dialog.ok"))
        self.ok_btn.clicked.connect(self._validate_and_accept)
        self.ok_btn.setDefault(True)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
        
        # 调整对话框大小
        self.adjustSize()
    
    def _create_param_widget(self, param, layout):
        """为参数创建输入控件"""
        if param == "image":
            # 图像文件选择
            file_layout = QHBoxLayout()
            file_path = QLineEdit()
            file_path.setReadOnly(True)
            file_path.setPlaceholderText(_("dialog.select_image"))
            
            browse_btn = QPushButton(_("dialog.browse"))
            browse_btn.clicked.connect(lambda: self._select_file(file_path, "image"))
            
            file_layout.addWidget(file_path)
            file_layout.addWidget(browse_btn)
            
            layout.addRow(_("param.image") + ":", file_layout)
            self.param_widgets[param] = file_path
            
        elif param == "video":
            # 视频文件选择
            file_layout = QHBoxLayout()
            file_path = QLineEdit()
            file_path.setReadOnly(True)
            file_path.setPlaceholderText(_("dialog.select_video"))
            
            browse_btn = QPushButton(_("dialog.browse"))
            browse_btn.clicked.connect(lambda: self._select_file(file_path, "video"))
            
            file_layout.addWidget(file_path)
            file_layout.addWidget(browse_btn)
            
            layout.addRow(_("param.video") + ":", file_layout)
            self.param_widgets[param] = file_path
            
        elif param == "directory":
            # 目录选择
            dir_layout = QHBoxLayout()
            dir_path = QLineEdit()
            dir_path.setReadOnly(True)
            dir_path.setPlaceholderText(_("dialog.select_directory"))
            
            browse_btn = QPushButton(_("dialog.browse"))
            browse_btn.clicked.connect(lambda: self._select_directory(dir_path))
            
            dir_layout.addWidget(dir_path)
            dir_layout.addWidget(browse_btn)
            
            layout.addRow(_("param.directory") + ":", dir_layout)
            self.param_widgets[param] = dir_path
            
        elif param == "camera_id":
            # 摄像头选择
            camera_combo = QComboBox()
            camera_combo.addItems([
                "0 - " + _("camera.default"),
                "1 - " + _("camera.external")
            ])
            
            layout.addRow(_("param.camera_id") + ":", camera_combo)
            self.param_widgets[param] = camera_combo
            
        elif param == "task":
            # 处理任务类型
            task_combo = QComboBox()
            task_combo.addItems([
                _("camera.task.none"),
                _("camera.task.edge"),
                _("camera.task.gray"),
                _("camera.task.face"),
                _("camera.task.blur")
            ])
            
            layout.addRow(_("param.task") + ":", task_combo)
            self.param_widgets[param] = task_combo
            
        elif param == "target":
            # 批处理目标插件
            from plugins.plugin_manager import PluginManager
            
            target_combo = QComboBox()
            
            # 获取所有可用插件
            plugin_manager = PluginManager()
            plugin_manager.load_plugins()
            
            for plugin in plugin_manager.get_plugins():
                if plugin.is_enabled() and any(t in ["image_recognition", "image_description"] 
                                              for t in plugin.get_task_types()):
                    target_combo.addItem(plugin.name)
            
            layout.addRow(_("param.target") + ":", target_combo)
            self.param_widgets[param] = target_combo
            
        else:
            # 默认文本输入
            text_input = QLineEdit()
            layout.addRow(f"{param}:", text_input)
            self.param_widgets[param] = text_input
    
    def _select_file(self, line_edit, file_type):
        """选择文件"""
        if file_type == "image":
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                _("dialog.select_image"),
                "",
                _("dialog.image_filter")
            )
        elif file_type == "video":
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                _("dialog.select_video"),
                "",
                _("dialog.video_filter")
            )
        else:
            file_path, _ = QFileDialog.getOpenFileName(self, _("dialog.select_file"))
        
        if file_path:
            line_edit.setText(file_path)
    
    def _select_directory(self, line_edit):
        """选择目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            _("dialog.select_directory")
        )
        
        if dir_path:
            line_edit.setText(dir_path)
    
    def _validate_and_accept(self):
        """验证参数并接受对话框"""
        # 收集参数值
        params = {}
        missing = []
        
        for param, widget in self.param_widgets.items():
            if isinstance(widget, QComboBox):
                if param == "camera_id":
                    # 摄像头ID，使用索引值
                    params[param] = widget.currentIndex()
                elif param == "task":
                    # 处理任务类型，转换为后端可识别的值
                    task_map = {
                        0: "none",
                        1: "edge",
                        2: "gray",
                        3: "face",
                        4: "blur"
                    }
                    params[param] = task_map.get(widget.currentIndex(), "none")
                else:
                    # 其他下拉框，使用文本值
                    params[param] = widget.currentText()
            else:
                # 文本框，获取文本值
                value = widget.text().strip()
                params[param] = value
                
                # 检查必填项是否为空
                if not value:
                    missing.append(param)
        
        # 验证必填项
        if missing:
            missing_names = [_(f"param.{p}") if p in ["image", "video", "directory", "camera_id", "task"] 
                              else p for p in missing]
            QMessageBox.warning(
                self,
                _("dialog.missing_params"),
                _("dialog.fill_all_fields") + f": {', '.join(missing_names)}"
            )
            return
        
        # 处理文件参数
        files = []
        for param in ["image", "video"]:
            if param in params and os.path.exists(params[param]):
                files.append(params[param])
        
        if files:
            params["files"] = files
        
        # 保存参数并接受对话框
        self.param_values = params
        self.accept()
    
    def get_parameters(self):
        """获取参数值"""
        return self.param_values
    
    def get_task_display_name(self):
        """获取任务类型的显示名称"""
        task_names = {
            "image_recognition": _("task.image_recognition"),
            "image_description": _("task.image_description"),
            "pose_estimation": _("task.pose_estimation"),
            "batch_processing": _("task.batch_processing"),
            "realtime_processing": _("task.realtime_processing")
        }
        return task_names.get(self.task_type, self.task_type)
    
    def show_progress(self, value=None, max_value=None):
        """显示进度条"""
        if value is None:
            # 显示不确定进度
            self.progress_bar.setRange(0, 0)
        else:
            # 显示确定进度
            if max_value is not None:
                self.progress_bar.setRange(0, max_value)
            self.progress_bar.setValue(value)
        
        self.progress_bar.setVisible(True)
        self.update()  # 更新界面
    
    def hide_progress(self):
        """隐藏进度条"""
        self.progress_bar.setVisible(False)
        self.update()  # 更新界面
