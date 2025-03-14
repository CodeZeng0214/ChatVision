"""
聊天消息模块，定义消息结构
"""
import os
import time
from datetime import datetime

class Message:
    """聊天消息类"""
    
    def __init__(self, content, sender, media_files=None):
        """
        初始化消息对象
        
        Args:
            content: 消息内容
            sender: 发送者标识，"user" 或 "assistant"
            media_files: 媒体文件列表
        """
        self.content = content
        self.sender = sender  # "user" 或 "assistant"
        self.media_files = media_files or []  # 图像或视频文件列表
        self.processed_results = None  # 处理结果
        self.timestamp = time.time()  # 消息时间戳
        self.status = "normal"  # 消息状态: normal, pending, error
    
    @property
    def formatted_time(self):
        """获取格式化后的时间"""
        dt = datetime.fromtimestamp(self.timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    @property
    def has_media(self):
        """检查消息是否包含媒体文件"""
        return len(self.media_files) > 0
    
    def add_media(self, media_file):
        """添加媒体文件"""
        if os.path.exists(media_file):
            self.media_files.append(media_file)
    
    def set_processed_results(self, results):
        """设置处理结果"""
        self.processed_results = results
    
    def to_dict(self):
        """将消息转换为字典表示"""
        return {
            "content": self.content,
            "sender": self.sender,
            "media_files": self.media_files.copy() if self.media_files else [],
            "timestamp": self.timestamp,
            "formatted_time": self.formatted_time,
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建消息对象"""
        msg = cls(data["content"], data["sender"], data.get("media_files"))
        msg.timestamp = data.get("timestamp", time.time())
        msg.status = data.get("status", "normal")
        return msg
    
    def __str__(self):
        """字符串表示"""
        files_info = f", {len(self.media_files)} 个文件" if self.media_files else ""
        return f"[{self.formatted_time}] {self.sender}: {self.content[:30]}...{files_info}"
