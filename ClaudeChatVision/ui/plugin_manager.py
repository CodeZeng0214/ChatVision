from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                              QLabel, QListWidget, QListWidgetItem,
                              QStackedWidget, QCheckBox, QFormLayout,
                              QLineEdit, QComboBox, QPushButton, QGroupBox,
                              QScrollArea, QSplitter)
from PySide6.QtCore import Qt, Signal

class PluginConfigWidget(QWidget):
    settings_saved = Signal(dict)
    
    def __init__(self, plugin_info, parent=None):
        super().__init__(parent)
        self.plugin_info = plugin_info
        self.setup_ui()
        
    def setup_ui(self):
        layout = QFormLayout(self)
        
        # Create form fields based on the plugin's parameters
        self.param_widgets = {}
        
        for param_name, param_info in self.plugin_info.get("parameters", {}).items():
            param_type = param_info.get("type", "text")
            default_value = param_info.get("default", "")
            label = QLabel(param_info.get("label", param_name))
            
            if param_type == "text":
                widget = QLineEdit(default_value)
            elif param_type == "number":
                widget = QLineEdit(str(default_value))
                widget.setValidator(QIntValidator())
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
        
        # Add save button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        layout.addRow("", save_button)
        
    def save_settings(self):
        # Get all the values from our form widgets
        settings = {}
        for param_name, widget in self.param_widgets.items():
            if isinstance(widget, QLineEdit):
                settings[param_name] = widget.text()
            elif isinstance(widget, QCheckBox):
                settings[param_name] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                settings[param_name] = widget.currentText()
        
        # Emit signal with new settings
        self.settings_saved.emit(settings)
        
        # Feedback to user
        print(f"Saving settings for plugin {self.plugin_info['name']}: {settings}")


class PluginManagerWindow(QWidget):
    plugin_settings_changed = Signal(str, dict)  # plugin_id, settings
    plugin_enabled_changed = Signal(str, bool)   # plugin_id, enabled
    
    def __init__(self, task_processor):
        super().__init__()
        self.task_processor = task_processor
        
        # Sample plugins for demonstration
        self.plugins = [
            {
                "id": "yolo",
                "name": "YOLO Object Detection",
                "enabled": True,
                "description": "Detect objects in images using YOLO",
                "parameters": {
                    "model": {
                        "label": "Model Version",
                        "type": "select", 
                        "options": ["YOLOv5s", "YOLOv5m", "YOLOv5l", "YOLOv5x"],
                        "default": "YOLOv5s"
                    },
                    "confidence": {
                        "label": "Confidence Threshold",
                        "type": "text",
                        "default": "0.5"
                    },
                    "output_dir": {
                        "label": "Output Directory",
                        "type": "text",
                        "default": "d:/Code/ChatVision/output"
                    }
                }
            },
            {
                "id": "pose",
                "name": "Pose Estimation",
                "enabled": True,
                "description": "Estimate human poses in images",
                "parameters": {
                    "model": {
                        "label": "Model Version",
                        "type": "select",
                        "options": ["MoveNet", "BlazePose", "OpenPose"],
                        "default": "MoveNet"
                    },
                    "output_dir": {
                        "label": "Output Directory",
                        "type": "text",
                        "default": "d:/Code/ChatVision/output"
                    }
                }
            },
            {
                "id": "blip",
                "name": "BLIP Image Captioning",
                "enabled": True,
                "description": "Generate captions for images",
                "parameters": {
                    "model_size": {
                        "label": "Model Size",
                        "type": "select",
                        "options": ["Small", "Medium", "Large"],
                        "default": "Medium"
                    },
                    "language": {
                        "label": "Output Language",
                        "type": "select",
                        "options": ["English", "Chinese", "Spanish"],
                        "default": "English"
                    }
                }
            }
        ]
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        # Create splitter for list and details
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Plugin list
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_label = QLabel("Available Plugins")
        list_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        self.plugin_list = QListWidget()
        self.plugin_list.setMinimumWidth(200)
        self.plugin_list.currentRowChanged.connect(self.on_plugin_selected)
        
        list_layout.addWidget(list_label)
        list_layout.addWidget(self.plugin_list)
        
        # Right side: Plugin details and configuration
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        self.plugin_title = QLabel("Select a plugin")
        self.plugin_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.plugin_description = QLabel("")
        
        self.enabled_checkbox = QCheckBox("Enabled")
        self.enabled_checkbox.toggled.connect(self.on_plugin_enabled_changed)
        
        # Create a scroll area for the config
        self.config_scroll = QScrollArea()
        self.config_scroll.setWidgetResizable(True)
        self.stacked_widget = QStackedWidget()
        self.config_scroll.setWidget(self.stacked_widget)
        
        details_layout.addWidget(self.plugin_title)
        details_layout.addWidget(self.plugin_description)
        details_layout.addWidget(self.enabled_checkbox)
        details_layout.addWidget(QLabel("Plugin Configuration:"))
        details_layout.addWidget(self.config_scroll)
        
        # Add widgets to splitter
        splitter.addWidget(list_widget)
        splitter.addWidget(details_widget)
        splitter.setSizes([200, 400])
        
        layout.addWidget(splitter)
        
        # Populate the plugin list
        self.populate_plugins()
        
    def populate_plugins(self):
        self.plugin_list.clear()
        
        for plugin in self.plugins:
            item = QListWidgetItem(plugin["name"])
            item.setData(Qt.UserRole, plugin["id"])
            
            # Show disabled plugins in grey
            if not plugin["enabled"]:
                item.setForeground(Qt.gray)
                
            self.plugin_list.addItem(item)
            
            # Create a configuration widget for this plugin and add it to the stacked widget
            config_widget = PluginConfigWidget(plugin)
            self.stacked_widget.addWidget(config_widget)
    
    def on_plugin_selected(self, row):
        if row < 0:
            return
        
        plugin_id = self.plugin_list.item(row).data(Qt.UserRole)
        plugin = next((p for p in self.plugins if p["id"] == plugin_id), None)
        
        if plugin:
            self.plugin_title.setText(plugin["name"])
            self.plugin_description.setText(plugin["description"])
            self.enabled_checkbox.setChecked(plugin["enabled"])
            self.stacked_widget.setCurrentIndex(row)
            
            # Connect settings saved signal for the currently selected plugin
            config_widget = self.stacked_widget.widget(row)
            if isinstance(config_widget, PluginConfigWidget):
                config_widget.settings_saved.disconnect() if config_widget.receivers(config_widget.settings_saved) > 0 else None
                config_widget.settings_saved.connect(lambda settings: self.on_plugin_settings_saved(plugin_id, settings))
    
    def on_plugin_enabled_changed(self, enabled):
        row = self.plugin_list.currentRow()
        if row >= 0:
            plugin_id = self.plugin_list.item(row).data(Qt.UserRole)
            for plugin in self.plugins:
                if plugin["id"] == plugin_id:
                    plugin["enabled"] = enabled
                    
                    # Update list item appearance
                    self.plugin_list.item(row).setForeground(Qt.black if enabled else Qt.gray)
                    
                    # Notify the task processor
                    self.plugin_enabled_changed.emit(plugin_id, enabled)
                    break
    
    def on_plugin_settings_saved(self, plugin_id, settings):
        # Forward plugin settings to task processor
        self.plugin_settings_changed.emit(plugin_id, settings)
