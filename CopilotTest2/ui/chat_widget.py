import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QTextEdit, QListWidget, QListWidgetItem, QLabel, 
                              QSplitter, QFileDialog, QProgressBar, QDialog, QTextBrowser,
                              QScrollArea, QScroller, QSizePolicy)
from PySide6.QtCore import Qt, QSize, Signal, Slot, QEvent, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QIcon, QResizeEvent, QTextCursor, QPainter, QPen, QColor, QBrush, QPainterPath
from ui.sidebar_widget import SidebarWidget
from ui.param_dialog import ParamDialog  # 导入参数对话框类
import tempfile
from utils.i18n import _
from core.message import Message

class BubbleWidget(QWidget):
    """消息气泡小部件"""
    
    def __init__(self, content, is_user=True, parent=None):
        super().__init__(parent)
        self.content = content
        self.is_user = is_user
        self.setContentsMargins(10, 5, 10, 5)
        
        # 设置自定义气泡背景
        self.user_color = QColor(149, 236, 105)  # 用户消息气泡颜色 #95ec69
        self.assistant_color = QColor(255, 255, 255)  # 助手消息气泡颜色 #ffffff
        
        # 修复：正确设置尺寸策略
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
    
    def paintEvent(self, event):
        """自定义绘制气泡背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 选择颜色
        color = self.user_color if self.is_user else self.assistant_color
        
        # 创建圆角矩形路径
        path = QPainterPath()
        rect = self.rect().adjusted(2, 2, -2, -2)  # 留出一点边距
        path.addRoundedRect(rect, 10, 10)
        
        # 设置画笔和画刷
        painter.setPen(QPen(color.darker(110), 1))
        painter.setBrush(QBrush(color))
        
        # 绘制气泡
        painter.drawPath(path)
        
        super().paintEvent(event)

class MessageItem(QWidget):
    """消息项组件"""
    
    def __init__(self, message, is_user=True, parent=None):
        super().__init__(parent)
        self.message = message
        self.is_user = is_user
        self.parent_list = parent  # 保存父级列表，用于计算宽度
        
        # 设置最小高度
        self.setMinimumHeight(50)
        
        # 监听父控件大小变化
        if parent:
            parent.installEventFilter(self)
        
        self._setup_ui()
        
        # 计算消息尺寸
        self.adjustSize()
    
    def eventFilter(self, obj, event):
        """事件过滤器，处理父控件尺寸变化"""
        if obj == self.parent_list and event.type() == QEvent.Resize:
            # 调整消息宽度适应父控件宽度
            self._adjust_message_width()
            return False
        return super().eventFilter(obj, event)
    
    def _adjust_message_width(self):
        """调整消息宽度适应父控件宽度"""
        if self.parent_list:
            # 设置消息最大宽度为父控件的65% (微信风格)
            max_width = int(self.parent_list.width() * 0.65)
            if hasattr(self, 'bubble_container'):
                self.bubble_container.setMaximumWidth(max_width)
            self.updateGeometry()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(10)
        
        # 在用户消息添加头像占位符
        if not self.is_user:
            avatar_label = QLabel()
            avatar_label.setFixedSize(40, 40)
            avatar_label.setStyleSheet("background-color: #c0c0c0; border-radius: 20px;")
            layout.addWidget(avatar_label)
        else:
            layout.addStretch()
        
        # 创建消息内容容器
        msg_container = QWidget()
        msg_layout = QVBoxLayout(msg_container)
        msg_layout.setContentsMargins(0, 0, 0, 0)
        msg_layout.setSpacing(5)
        
        # 发送者名称
        sender_name = "我" if self.is_user else "ChatVision"
        name_label = QLabel(sender_name)
        name_label.setStyleSheet("font-weight: bold; color: #666666;")
        
        # 根据发送者对齐方式
        if self.is_user:
            name_label.setAlignment(Qt.AlignRight)
            msg_layout.setAlignment(Qt.AlignRight)
        
        msg_layout.addWidget(name_label)
        
        # 创建气泡容器
        self.bubble_container = QWidget()
        bubble_layout = QVBoxLayout(self.bubble_container)
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        bubble_layout.setSpacing(5)
        
        # 消息内容 - 使用QTextBrowser代替QLabel以支持更好的文本格式化和自动换行
        self.content = QTextBrowser()
        self.content.setHtml(self.message.content.replace("\n", "<br>"))
        self.content.setOpenExternalLinks(True)
        self.content.setReadOnly(True)
        self.content.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.content.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 设置合适的最小尺寸和自适应高度
        self.content.setMinimumWidth(100)
        self.content.setMinimumHeight(30)
        
        # 计算适合内容的高度
        doc_height = self.content.document().size().height()
        self.content.setMaximumHeight(min(300, int(doc_height + 20)))
        
        # 气泡样式设置
        bubble_widget = BubbleWidget(self.content, self.is_user)
        bubble_layout_inner = QVBoxLayout(bubble_widget)
        bubble_layout_inner.addWidget(self.content)
        bubble_layout_inner.setContentsMargins(10, 10, 10, 10)
        
        bubble_layout.addWidget(bubble_widget)
        
        # 如果有媒体文件，添加显示
        if self.message.media_files:
            for file_path in self.message.media_files:
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    # 图片文件
                    img_container = QWidget()
                    img_container_layout = QVBoxLayout(img_container)
                    img_container_layout.setContentsMargins(0, 0, 0, 0)
                    
                    img_label = QLabel()
                    pixmap = QPixmap(file_path)
                    
                    # 根据父控件调整图片尺寸
                    if self.parent_list:
                        max_img_width = int(self.parent_list.width() * 0.4)
                        scaled_pixmap = pixmap.scaled(
                            max_img_width, 300, 
                            Qt.KeepAspectRatio, 
                            Qt.SmoothTransformation
                        )
                    else:
                        scaled_pixmap = pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        
                    img_label.setPixmap(scaled_pixmap)
                    img_label.setStyleSheet("background-color: transparent; border-radius: 5px;")
                    
                    # 添加到气泡中的图片容器
                    img_container_layout.addWidget(img_label)
                    bubble_layout.addWidget(img_container)
                    
                elif file_path.lower().endswith(('.mp4', '.avi', '.mov', '.wmv')):
                    # 视频文件 - 显示为缩略图
                    video_btn = QPushButton("点击播放视频")
                    video_btn.setStyleSheet("background-color: #d0d0d0; border-radius: 5px; padding: 8px;")
                    video_btn.setProperty("video_path", file_path)
                    video_btn.clicked.connect(self.play_video)
                    bubble_layout.addWidget(video_btn)
        
        # 如果有处理结果，显示结果
        if hasattr(self.message, 'processed_results') and self.message.processed_results:
            result_label = QLabel("处理结果:")
            result_label.setStyleSheet("font-weight: bold; color: #666666;")
            bubble_layout.addWidget(result_label)
            
            # 根据结果类型显示
            if isinstance(self.message.processed_results, str):
                # 字符串结果
                result_widget = BubbleWidget(None, self.is_user)
                result_layout = QVBoxLayout(result_widget)
                
                result_content = QLabel(self.message.processed_results)
                result_content.setWordWrap(True)
                result_content.setStyleSheet("padding: 5px;")
                
                result_layout.addWidget(result_content)
                result_layout.setContentsMargins(10, 10, 10, 10)
                
                bubble_layout.addWidget(result_widget)
                
            elif isinstance(self.message.processed_results, dict) and "result_image" in self.message.processed_results:
                # 图像结果
                img_path = self.message.processed_results["result_image"]
                
                img_container = QWidget()
                img_container_layout = QVBoxLayout(img_container)
                img_container_layout.setContentsMargins(0, 0, 0, 0)
                
                result_img = QLabel()
                pixmap = QPixmap(img_path)
                
                # 根据父控件调整图片尺寸
                if self.parent_list:
                    max_img_width = int(self.parent_list.width() * 0.4)
                    scaled_pixmap = pixmap.scaled(
                        max_img_width, 300, 
                        Qt.KeepAspectRatio, 
                        Qt.SmoothTransformation
                    )
                else:
                    scaled_pixmap = pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    
                result_img.setPixmap(scaled_pixmap)
                
                img_container_layout.addWidget(result_img)
                bubble_layout.addWidget(img_container)
        
        msg_layout.addWidget(self.bubble_container)
        layout.addWidget(msg_container)
        
        # 在助手消息添加头像占位符或用户消息添加右侧空间
        if self.is_user:
            avatar_label = QLabel()
            avatar_label.setFixedSize(40, 40)
            avatar_label.setStyleSheet("background-color: #c0c0c0; border-radius: 20px;")
            layout.addWidget(avatar_label)
        else:
            layout.addStretch()
        
        # 初始调整宽度
        QTimer.singleShot(0, self._adjust_message_width)
    
    def update_content(self, content):
        """更新消息内容"""
        self.message.content = content
        self.content.setHtml(content.replace("\n", "<br>"))
        
        # 更新消息尺寸
        doc_height = self.content.document().size().height()
        self.content.setMaximumHeight(min(300, int(doc_height + 20)))
        
        # 滚动到底部
        cursor = self.content.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.content.setTextCursor(cursor)
        
        # 调整整体尺寸
        self.adjustSize()
    
    def add_content_chunk(self, chunk):
        """添加消息内容块（用于流式输出）"""
        current = self.message.content
        self.update_content(current + chunk)
    
    def play_video(self):
        """播放视频"""
        sender = self.sender()
        video_path = sender.property("video_path")
        # 导入媒体播放相关模块
        try:
            from PySide6.QtMultimedia import QMediaPlayer
            from PySide6.QtMultimediaWidgets import QVideoWidget
            
            # 创建视频播放对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("视频播放")
            dialog.resize(640, 480)
            
            layout = QVBoxLayout(dialog)
            
            # 创建视频播放组件
            video_widget = QVideoWidget()
            player = QMediaPlayer()
            player.setVideoOutput(video_widget)
            player.setSource(video_path)
            
            layout.addWidget(video_widget)
            
            # 播放控制按钮
            controls = QHBoxLayout()
            play_btn = QPushButton("播放")
            pause_btn = QPushButton("暂停")
            stop_btn = QPushButton("停止")
            
            play_btn.clicked.connect(player.play)
            pause_btn.clicked.connect(player.pause)
            stop_btn.clicked.connect(player.stop)
            
            controls.addWidget(play_btn)
            controls.addWidget(pause_btn)
            controls.addWidget(stop_btn)
            
            layout.addLayout(controls)
            
            # 显示对话框并开始播放
            dialog.show()
            player.play()
            
        except ImportError:
            # 如果没有媒体播放模块，显示错误信息
            error_dialog = QDialog(self)
            error_dialog.setWindowTitle("错误")
            error_layout = QVBoxLayout(error_dialog)
            error_label = QLabel("无法播放视频，缺少媒体播放组件。")
            error_layout.addWidget(error_label)
            error_dialog.setLayout(error_layout)
            error_dialog.exec()


class ChatWidget(QWidget):
    """聊天界面组件"""
    
    def __init__(self, chat_engine):
        super().__init__()
        self.chat_engine = chat_engine
        self.media_files = []
        self.sidebar_visible = False
        self.sidebar = None
        self.message_widgets = {}  # 存储消息ID到消息控件的映射
        self.auto_scroll = True    # 默认启用自动滚动
        
        # 设置回调
        self.chat_engine.on_new_message = self.on_new_message
        self.chat_engine.on_processing = self.on_processing
        self.chat_engine.on_require_params = self.on_require_params
        self.chat_engine.on_show_sidebar = self.on_show_sidebar
        
        # 连接流式响应信号
        self.chat_engine.message_response_chunk.connect(self.on_message_chunk)
        
        self._setup_ui()
        
        # 添加欢迎消息
        self._show_welcome_message()
    
    def _setup_ui(self):
        """设置聊天界面"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建分隔器，用于聊天区域和侧边栏
        self.splitter = QSplitter(Qt.Horizontal)
        
        # 创建左侧聊天区域
        chat_container = QWidget()
        chat_container.setStyleSheet("background-color: #f5f5f5;")  # 微信风格的背景色
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        
        # 聊天记录区域 - 使用QListWidget，但确保滚动行为像微信那样
        self.chat_list = QListWidget()
        self.chat_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)  # 平滑滚动
        self.chat_list.setFrameShape(QListWidget.NoFrame)  # 无边框
        self.chat_list.setStyleSheet("""
            QListWidget {
                background-color: #f5f5f5;
                border: none;
                outline: none;
            }
            QListWidget::item {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f5f5f5;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # 启用平滑滚动（触摸屏风格）
        scroller = QScroller.scroller(self.chat_list.viewport())
        scroller.grabGesture(self.chat_list.viewport(), QScroller.LeftMouseButtonGesture)
        
        # 监听滚动以检测用户是否手动滚动
        self.chat_list.verticalScrollBar().valueChanged.connect(self._on_scroll_value_changed)
        self.chat_list.verticalScrollBar().rangeChanged.connect(self._on_scroll_range_changed)
        
        chat_layout.addWidget(self.chat_list)
        
        # 输入和控制区域
        input_container = QWidget()
        input_container.setStyleSheet("background-color: white;")
        input_layout = QVBoxLayout(input_container)
        
        # 进度条 - 默认隐藏
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        self.progress_bar.setStyleSheet("QProgressBar {border: none; background-color: #f0f0f0; height: 4px;}")
        input_layout.addWidget(self.progress_bar)
        
        # 文件选择和输入框布局
        input_controls = QHBoxLayout()
        input_controls.setContentsMargins(10, 5, 10, 5)
        
        self.file_btn = QPushButton("选择文件")
        self.file_btn.setCursor(Qt.PointingHandCursor)
        self.file_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.file_btn.clicked.connect(self.select_files)
        
        input_controls.addWidget(self.file_btn)
        input_controls.addStretch()
        input_layout.addLayout(input_controls)
        
        # 显示已选文件
        self.file_label = QLabel()
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet("color: #666666; margin: 0px 10px;")
        input_layout.addWidget(self.file_label)
        
        # 文本输入区
        input_box_layout = QHBoxLayout()
        input_box_layout.setContentsMargins(10, 0, 10, 0)
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("输入消息...")
        self.input_text.setMinimumHeight(60)
        self.input_text.setMaximumHeight(100)
        self.input_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
        """)
        
        input_box_layout.addWidget(self.input_text, 1)  # 占比1
        
        # 发送按钮放在输入框右侧
        self.send_btn = QPushButton("发送")
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setMinimumWidth(60)
        self.send_btn.setMaximumWidth(80)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #07C160;
                color: white;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #06AD56;
            }
        """)
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setDefault(True)
        
        input_box_layout.addWidget(self.send_btn)
        
        input_layout.addLayout(input_box_layout)
        
        # 底部控制按钮
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(10, 5, 10, 10)
        
        self.clear_btn = QPushButton("清空聊天")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666666;
                border: none;
            }
            QPushButton:hover {
                color: #1aad19;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_chat)
        
        self.sidebar_btn = QPushButton("显示侧边栏")
        self.sidebar_btn.setCursor(Qt.PointingHandCursor)
        self.sidebar_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666666;
                border: none;
            }
            QPushButton:hover {
                color: #1aad19;
            }
        """)
        self.sidebar_btn.clicked.connect(self.toggle_sidebar)
        
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.sidebar_btn)
        button_layout.addStretch()
        input_layout.addLayout(button_layout)
        
        # 设置输入区域固定高度
        input_container.setMinimumHeight(170)
        input_container.setMaximumHeight(190)
        chat_layout.addWidget(input_container)
        
        # 添加聊天区域到分隔器
        self.splitter.addWidget(chat_container)
        
        # 创建侧边栏（默认不显示）
        self.sidebar = SidebarWidget()
        self.splitter.addWidget(self.sidebar)
        self.sidebar.setVisible(False)
        
        # 设置分隔器尺寸
        self.splitter.setSizes([self.width(), 0])
        
        # 主布局添加分隔器
        main_layout.addWidget(self.splitter)
    
    def _on_scroll_value_changed(self, value):
        """滚动条值变化处理函数"""
        scrollbar = self.chat_list.verticalScrollBar()
        # 当用户向上滚动时关闭自动滚动，向下滚动到底部时重新启用
        if value < scrollbar.maximum():
            self.auto_scroll = False
        elif value == scrollbar.maximum():
            self.auto_scroll = True
    
    def _on_scroll_range_changed(self, min_val, max_val):
        """滚动条范围变化处理函数"""
        if self.auto_scroll:
            # 平滑滚动到底部
            scrollbar = self.chat_list.verticalScrollBar()
            
            # 使用动画实现平滑滚动
            animation = QPropertyAnimation(scrollbar, b"value")
            animation.setDuration(150)  # 150毫秒
            animation.setStartValue(scrollbar.value())
            animation.setEndValue(max_val)
            animation.setEasingCurve(QEasingCurve.OutCubic)
            animation.start(QPropertyAnimation.DeleteWhenStopped)
    
    def select_files(self):
        """选择要发送的文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择文件",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif);;视频文件 (*.mp4 *.avi *.mov *.wmv)"
        )
        
        if files:
            self.media_files = files
            # 显示选择的文件名
            file_names = [os.path.basename(f) for f in files]
            self.file_label.setText("已选择: " + ", ".join(file_names))
        else:
            self.media_files = []
            self.file_label.setText("")
    
    def send_message(self):
        """发送消息"""
        content = self.input_text.toPlainText().strip()
        
        if not content and not self.media_files:
            return
        
        # 发送消息 - 立即清空输入框
        self.input_text.clear()
        
        # 保存当前媒体文件引用，因为我们将清空媒体文件列表
        media_files = self.media_files.copy()
        self.media_files = []
        self.file_label.setText("")
        
        # 发送消息并处理
        self.chat_engine.send_message(content, media_files)
        
        # 滚动到底部
        self.chat_list.scrollToBottom()
    
    def on_new_message(self, message):
        """处理新消息"""
        message_id = id(message)
        
        # 检查是否已有这条消息的控件
        if message_id in self.message_widgets:
            # 更新现有消息控件
            item_widget = self.message_widgets[message_id]
            item_widget.update_content(message.content)
        else:
            # 创建新的消息控件
            is_user = message.sender == "user"
            item_widget = MessageItem(message, is_user, self.chat_list)
            
            # 创建列表项并设置自定义小部件
            list_item = QListWidgetItem(self.chat_list)
            list_item.setSizeHint(item_widget.sizeHint())
            self.chat_list.addItem(list_item)
            self.chat_list.setItemWidget(list_item, item_widget)
            
            # 存储消息控件引用
            self.message_widgets[message_id] = item_widget
        
        # 滚动到底部
        self.chat_list.scrollToBottom()
    
    def on_message_chunk(self, message, chunk):
        """处理消息流片段"""
        message_id = id(message)
        
        # 检查是否已有这条消息的控件
        if message_id in self.message_widgets:
            # 更新现有消息控件，添加新内容块
            item_widget = self.message_widgets[message_id]
            item_widget.add_content_chunk(chunk)
        else:
            # 创建新消息控件
            item_widget = MessageItem(message, False, self.chat_list)
            
            # 创建列表项并设置自定义小部件
            list_item = QListWidgetItem(self.chat_list)
            list_item.setSizeHint(item_widget.sizeHint())
            self.chat_list.addItem(list_item)
            self.chat_list.setItemWidget(list_item, item_widget)
            
            # 存储消息控件引用
            self.message_widgets[message_id] = item_widget
        
        # 滚动到底部
        self.chat_list.scrollToBottom()
    
    def on_processing(self, is_processing, message=None):
        """处理状态回调"""
        self.progress_bar.setVisible(is_processing)
        if message and is_processing:
            self.progress_bar.setFormat(message)
    
    def on_require_params(self, task_type, missing_params):
        """需要补充参数回调"""
        dialog = ParamDialog(task_type, missing_params, self)
        
        if dialog.exec():
            # 用户确认，获取参数
            params = dialog.get_parameters()
            
            # 更新消息
            self.chat_engine.update_message_with_params(task_type, params)
    
    def clear_chat(self):
        """清空聊天记录"""
        self.chat_list.clear()
        self.message_widgets.clear()  # 清空消息控件引用
        self.chat_engine.clear_history()
    
    def toggle_sidebar(self):
        """切换侧边栏显示状态"""
        self.sidebar_visible = not self.sidebar_visible
        self.sidebar.setVisible(self.sidebar_visible)
        
        # 更新按钮文本
        self.sidebar_btn.setText("隐藏侧边栏" if self.sidebar_visible else "显示侧边栏")
        
        # 调整分隔器大小
        if self.sidebar_visible:
            self.splitter.setSizes([int(self.width() * 0.6), int(self.width() * 0.4)])
        else:
            self.splitter.setSizes([self.width(), 0])
    
    def refresh_ui(self):
        """刷新UI文本"""
        self.file_btn.setText(_("chat.select_file"))
        self.clear_btn.setText(_("chat.clear"))
        self.send_btn.setText(_("chat.send"))
        
        sidebar_text = _("chat.hide_sidebar") if self.sidebar_visible else _("chat.show_sidebar")
        self.sidebar_btn.setText(sidebar_text)
        
        if self.progress_bar.isVisible():
            self.progress_bar.setFormat(_("chat.processing") + ": %p%")
        
        # 刷新侧边栏
        if self.sidebar:
            self.sidebar.refresh_ui()
    
    def on_show_sidebar(self, display_type, *args):
        """侧边栏显示回调"""
        # 如果侧边栏不可见，显示它
        if not self.sidebar_visible:
            self.toggle_sidebar()
        
        # 根据不同类型显示对应内容
        if display_type == "image_comparison" and len(args) >= 2:
            self.sidebar.show_image_comparison(args[0], args[1])
        elif display_type == "video" and args:
            self.sidebar.show_video(args[0])
        elif display_type == "camera" and len(args) >= 1:
            camera_id = args[0]
            process_type = args[1] if len(args) > 1 else None
            self.sidebar.show_camera(camera_id, process_type)
        elif display_type == "directory" and args:
            # 目录显示可以使用图像比较组件，或实现专门的目录浏览组件
            pass
    
    def _show_welcome_message(self):
        """显示欢迎消息"""
        welcome_msg = Message(
            "您好！我是ChatVision，既可以进行普通聊天，也能处理图像和视频。\n\n"
            "- 直接发送文字消息可以进行普通聊天\n"
            "- 发送图片可以请我描述图片内容或识别图中物体\n"
            "- 您也可以明确指出任务，例如「识别这张图片中有什么物体」", 
            "assistant"
        )
        self.on_new_message(welcome_msg)
    
    def resizeEvent(self, event: QResizeEvent):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        
        # 调整侧边栏大小
        if self.sidebar_visible:
            self.splitter.setSizes([int(self.width() * 0.6), int(self.width() * 0.4)])

    def keyPressEvent(self, event):
        """键盘事件处理"""
        # Ctrl+Enter 发送消息
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
            self.send_message()
            return

        super().keyPressEvent(event)
