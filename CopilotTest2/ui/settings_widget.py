from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QComboBox, QTabWidget, QLineEdit,
                              QFormLayout, QGroupBox, QSpinBox, QCheckBox)
from PySide6.QtCore import Qt, Signal
from config.llm_config import LLMConfig
from config.app_config import AppConfig
from utils.i18n import _, i18n

class SettingsWidget(QWidget):
    """设置界面"""
    
    settings_changed = Signal()  # 设置变更信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        
        # 创建标签页
        self.tabs = QTabWidget()
        
        # 通用设置页
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # 语言设置
        lang_group = QGroupBox(_("settings.language"))
        lang_layout = QFormLayout(lang_group)
        
        self.language_combo = QComboBox()
        self.language_combo.addItem("简体中文", "zh_CN")
        self.language_combo.addItem("English", "en_US")
        lang_layout.addRow(_("settings.language_select"), self.language_combo)
        
        general_layout.addWidget(lang_group)
        
        # 界面设置
        ui_group = QGroupBox(_("settings.ui"))
        ui_layout = QFormLayout(ui_group)
        
        self.default_width = QSpinBox()
        self.default_width.setRange(800, 3840)
        self.default_width.setSingleStep(100)
        ui_layout.addRow(_("settings.window_width"), self.default_width)
        
        self.default_height = QSpinBox()
        self.default_height.setRange(600, 2160)
        self.default_height.setSingleStep(100)
        ui_layout.addRow(_("settings.window_height"), self.default_height)
        
        general_layout.addWidget(ui_group)
        
        # LLM设置页
        llm_tab = QWidget()
        llm_layout = QVBoxLayout(llm_tab)
        
        llm_group = QGroupBox("LLM")
        llm_form = QFormLayout(llm_group)
        
        self.llm_url = QLineEdit()
        llm_form.addRow(_("settings.api_url"), self.llm_url)
        
        self.llm_key = QLineEdit()
        self.llm_key.setEchoMode(QLineEdit.Password)
        llm_form.addRow(_("settings.api_key"), self.llm_key)
        
        self.llm_model = QLineEdit()
        llm_form.addRow(_("settings.model"), self.llm_model)
        
        self.llm_history = QSpinBox()
        self.llm_history.setRange(1, 100)
        llm_form.addRow(_("settings.max_history"), self.llm_history)
        
        llm_layout.addWidget(llm_group)
        
        # 添加标签页
        self.tabs.addTab(general_tab, _("settings.general"))
        self.tabs.addTab(llm_tab, _("settings.llm"))
        
        layout.addWidget(self.tabs)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton(_("settings.cancel"))
        self.cancel_btn.clicked.connect(self._load_settings)
        
        self.save_btn = QPushButton(_("settings.save"))
        self.save_btn.clicked.connect(self._save_settings)
        self.save_btn.setDefault(True)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def _load_settings(self):
        """加载设置"""
        # 加载通用设置
        # 语言
        index = self.language_combo.findData(i18n.current_locale)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
            
        # 窗口尺寸
        self.default_width.setValue(AppConfig.DEFAULT_WINDOW_WIDTH)
        self.default_height.setValue(AppConfig.DEFAULT_WINDOW_HEIGHT)
        
        # 加载LLM设置
        llm_config = LLMConfig.get_config()
        self.llm_url.setText(llm_config["base_url"])
        self.llm_key.setText(llm_config["api_key"])
        self.llm_model.setText(llm_config["model"])
        self.llm_history.setValue(llm_config["max_history"])
    
    def _save_settings(self):
        """保存设置"""
        # 保存通用设置
        # 语言
        new_locale = self.language_combo.currentData()
        if new_locale != i18n.current_locale:
            i18n.set_locale(new_locale)
            
        # 窗口尺寸
        AppConfig.DEFAULT_WINDOW_WIDTH = self.default_width.value()
        AppConfig.DEFAULT_WINDOW_HEIGHT = self.default_height.value()
        
        # 保存LLM设置
        LLMConfig.update_config(
            base_url=self.llm_url.text(),
            api_key=self.llm_key.text(),
            model=self.llm_model.text(),
            max_history=self.llm_history.value()
        )
        
        # 发出设置变更信号
        self.settings_changed.emit()
