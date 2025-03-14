"""
简化版本的本地化支持模块
"""
import os
import json
import logging

class I18nManager:
    """简化的国际化管理器，固定使用中文"""
    
    def __init__(self):
        self.current_locale = "zh_CN"  # 固定使用中文
        self.translations = {}
        self.load_translations()
    
    def load_translations(self):
        """加载翻译文件"""
        try:
            # 获取翻译文件目录
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            locale_dir = os.path.join(base_dir, "resources", "locales")
            
            # 加载中文翻译
            locale_file = os.path.join(locale_dir, f"{self.current_locale}.json")
            
            if os.path.exists(locale_file):
                with open(locale_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
                logging.info(f"已加载语言文件: {locale_file}")
            else:
                # 如果文件不存在，创建一个基本的翻译文件
                self.translations = self._create_default_translations()
                with open(locale_file, 'w', encoding='utf-8') as f:
                    json.dump(self.translations, f, ensure_ascii=False, indent=4)
                logging.info(f"创建了默认语言文件: {locale_file}")
        
        except Exception as e:
            logging.error(f"加载翻译文件失败: {e}")
            self.translations = self._create_default_translations()
    
    def _create_default_translations(self):
        """创建默认翻译"""
        return {
            "app.name": "ChatVision",
            "app.description": "图像识别聊天机器人",
            
            "ui.chat": "聊天",
            "ui.plugins": "插件管理",
            "ui.settings": "设置",
            "ui.about": "关于",
            
            "chat.send": "发送",
            "chat.clear": "清空聊天",
            "chat.select_file": "选择文件",
            "chat.show_sidebar": "显示侧边栏",
            "chat.hide_sidebar": "隐藏侧边栏",
            "chat.processing": "正在处理",
            
            "plugin.name": "插件名称",
            "plugin.description": "描述",
            "plugin.enabled": "已启用",
            "plugin.disabled": "已禁用",
            "plugin.config": "配置",
            "plugin.install": "安装插件",
            
            "task.image_recognition": "图像识别",
            "task.image_description": "图像描述",
            "task.pose_estimation": "姿态估计",
            "task.batch_processing": "批量处理",
            "task.realtime_processing": "实时处理",
            
            "error.model_not_loaded": "模型未加载，无法处理任务",
            "error.file_not_found": "未找到有效的文件",
            "error.processing_failed": "处理失败"
        }
    
    def get_text(self, key, default=None):
        """获取翻译文本"""
        return self.translations.get(key, default if default is not None else key)
    
    def get_all_translations(self):
        """获取所有翻译"""
        return self.translations

# 全局国际化管理器实例
i18n = I18nManager()

def _(key, default=None):
    """翻译函数，方便在代码中使用"""
    return i18n.get_text(key, default)
