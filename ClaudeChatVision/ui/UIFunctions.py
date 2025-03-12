# -*- coding: utf-8 -*-
# @作者: CatfishW🚀
# @时间: 2023/5/1
from ClaudeChatVision.main import *
from ui.custom_grips import CustomGrip
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QEvent, QTimer
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
import time

GLOBAL_STATE = False    # 最大化/最小化标志
GLOBAL_TITLE_BAR = True  # 标题栏显示标志


class UIFuncitons(MainWindow):
    """UI功能类，实现窗口界面的特殊效果和交互功能
    
    提供菜单展开/收起、窗口最大化/恢复、窗口拖动和调整大小等功能。
    这个类扩展了MainWindow，添加了额外的UI交互功能和动画效果。
    """
    
    def toggleMenu(self, enable):
        """展开或收起左侧菜单
        
        通过动画效果平滑地改变左侧菜单的宽度，实现展开和收起的效果。
        使用Qt的属性动画系统实现过渡效果，提供更好的用户体验。
        
        参数:
            enable (bool): 是否启用菜单切换
        """
        if enable:
            standard = 68  # 收起状态的标准宽度
            maxExtend = 180  # 展开状态的最大宽度
            width = self.LeftMenuBg.width()  # 获取当前宽度

            # 判断当前状态决定目标宽度
            if width == 68:
                widthExtended = maxExtend  # 如果是收起状态，则展开
            else:
                widthExtended = standard  # 如果是展开状态，则收起
            
            # 创建Qt动画
            self.animation = QPropertyAnimation(self.LeftMenuBg, b"minimumWidth")
            self.animation.setDuration(500)  # 动画持续时间(毫秒)
            self.animation.setStartValue(width)  # 起始宽度
            self.animation.setEndValue(widthExtended)  # 目标宽度
            self.animation.setEasingCurve(QEasingCurve.InOutQuint)  # 设置缓动曲线
            self.animation.start()  # 启动动画

    def settingBox(self, enable):
        """展开或收起右侧设置面板
        
        通过动画效果平滑地改变右侧设置面板的宽度，同时也会调整左侧菜单的宽度。
        使用并行动画组同时执行两个动画，实现协调一致的UI变换效果。
        
        参数:
            enable (bool): 是否启用设置面板切换
        """
        if enable:
            # 获取当前宽度
            widthRightBox = self.prm_page.width()  # 右侧设置列宽度
            widthLeftBox = self.LeftMenuBg.width()  # 左侧列宽度
            maxExtend = 220  # 展开状态的最大宽度
            standard = 0  # 收起状态的标准宽度

            # 设置目标宽度
            if widthRightBox == 0:
                widthExtended = maxExtend  # 如果当前是收起状态，则展开
            else:
                widthExtended = standard  # 如果当前是展开状态，则收起

            # 创建左侧菜单的动画      
            self.left_box = QPropertyAnimation(self.LeftMenuBg, b"minimumWidth")
            self.left_box.setDuration(500)  # 持续时间
            self.left_box.setStartValue(widthLeftBox)  # 起始宽度
            self.left_box.setEndValue(68)  # 目标宽度（收起状态）
            self.left_box.setEasingCurve(QEasingCurve.InOutQuart)  # 缓动曲线

            # 创建右侧设置面板的动画      
            self.right_box = QPropertyAnimation(self.prm_page, b"minimumWidth")
            self.right_box.setDuration(500)  # 持续时间
            self.right_box.setStartValue(widthRightBox)  # 起始宽度
            self.right_box.setEndValue(widthExtended)  # 目标宽度
            self.right_box.setEasingCurve(QEasingCurve.InOutQuart)  # 缓动曲线

            # 创建并行动画组 - 同时执行两个动画
            self.group = QParallelAnimationGroup()
            self.group.addAnimation(self.left_box)
            self.group.addAnimation(self.right_box)
            self.group.start()  # 启动动画组

    def maximize_restore(self):
        """最大化或恢复窗口大小
        
        根据当前窗口状态切换最大化和恢复正常大小，并适当显示或隐藏边框拖动控件。
        更新工具提示文本和全局状态标志，确保UI状态与窗口状态一致。
        """
        global GLOBAL_STATE
        status = GLOBAL_STATE
        if status == False:  # 如果当前不是最大化状态
            GLOBAL_STATE = True
            self.showMaximized()  # 最大化窗口
            self.max_sf.setToolTip("还原")  # 更新工具提示
            # 最大化时隐藏所有边缘拖动控件
            self.frame_size_grip.hide()        
            self.left_grip.hide()       
            self.right_grip.hide()
            self.top_grip.hide()
            self.bottom_grip.hide()
        else:  # 如果当前是最大化状态
            GLOBAL_STATE = False
            self.showNormal()  # 恢复正常大小
            self.resize(self.width()+1, self.height()+1)  # 微调大小修复可能的显示问题
            self.max_sf.setToolTip("最大化")  # 更新工具提示
            # 恢复正常大小时显示所有边缘拖动控件
            self.frame_size_grip.show()
            self.left_grip.show()
            self.right_grip.show()
            self.top_grip.show()
            self.bottom_grip.show()
    
    def uiDefinitions(self):
        """窗口控制定义
        
        设置窗口的各种控制功能，如双击标题栏最大化、拖动窗口移动、自定义边缘调整大小等。
        为窗口添加各种事件处理，实现无边框窗口的完整功能。
        """
        # 双击标题栏最大化/还原功能
        def dobleClickMaximizeRestore(event):
            if event.type() == QEvent.MouseButtonDblClick:
                QTimer.singleShot(250, lambda: UIFuncitons.maximize_restore(self))
        self.top.mouseDoubleClickEvent = dobleClickMaximizeRestore
        
        # 窗口移动/最大化/还原功能
        def moveWindow(event):
            # 如果窗口已最大化，则先还原
            if GLOBAL_STATE:
                UIFuncitons.maximize_restore(self)
            # 在按下左键的情况下移动窗口
            if event.buttons() == Qt.LeftButton:
                self.move(self.pos() + event.globalPos() - self.dragPos)
                self.dragPos = event.globalPos()
        self.top.mouseMoveEvent = moveWindow
        
        # 创建自定义边缘拖动控件
        self.left_grip = CustomGrip(self, Qt.LeftEdge, True)  # 左边缘
        self.right_grip = CustomGrip(self, Qt.RightEdge, True)  # 右边缘
        self.top_grip = CustomGrip(self, Qt.TopEdge, True)  # 上边缘
        self.bottom_grip = CustomGrip(self, Qt.BottomEdge, True)  # 下边缘

        # 最小化按钮功能
        self.min_sf.clicked.connect(lambda: self.showMinimized())
        # 最大化/还原按钮功能
        self.max_sf.clicked.connect(lambda: UIFuncitons.maximize_restore(self))
        # 关闭按钮功能
        self.close_button.clicked.connect(self.close)

    def resize_grips(self):
        """调整窗口边缘拖动控件的大小
        
        根据窗口当前大小重新设置四个边缘拖动控件的位置和大小。
        这个方法通常在窗口大小改变后调用，确保拖动控件始终在正确位置。
        """
        # 设置左边缘拖动控件的位置和大小
        self.left_grip.setGeometry(0, 10, 10, self.height())
        # 设置右边缘拖动控件的位置和大小
        self.right_grip.setGeometry(self.width() - 10, 10, 10, self.height())
        # 设置上边缘拖动控件的位置和大小
        self.top_grip.setGeometry(0, 0, self.width(), 10)
        # 设置下边缘拖动控件的位置和大小
        self.bottom_grip.setGeometry(0, self.height() - 10, self.width(), 10)

    def shadow_style(self, widget, Color):
        """为控件添加阴影效果
        
        创建并应用一个阴影效果到指定控件，增强UI的立体感。
        可以指定阴影的颜色，使界面元素更具视觉深度。
        
        参数:
            widget (QWidget): 需要添加阴影的控件
            Color (QColor): 阴影的颜色
        """
        # 创建阴影效果对象
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setOffset(8, 8)  # 设置阴影偏移距离
        shadow.setBlurRadius(38)  # 设置阴影模糊半径
        shadow.setColor(Color)  # 设置阴影颜色
        widget.setGraphicsEffect(shadow)  # 将阴影效果应用到控件