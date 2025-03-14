from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QFont, QPen, QLinearGradient

def create_app_icon():
    """创建应用程序图标"""
    # 创建一个 256x256 的图标
    pixmap = QPixmap(256, 256)
    pixmap.fill(QColor(0, 0, 0, 0))  # 透明背景
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # 绘制渐变背景圆形
    gradient = QLinearGradient(0, 0, 256, 256)
    gradient.setColorAt(0, QColor(41, 128, 185))  # 蓝色
    gradient.setColorAt(1, QColor(109, 213, 250))  # 淡蓝色
    painter.setBrush(QBrush(gradient))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(28, 28, 200, 200)
    
    # 绘制一个视觉元素代表摄像头或图像
    painter.setPen(QPen(QColor(255, 255, 255), 6))
    painter.drawEllipse(88, 88, 80, 80)  # 镜头圆
    painter.drawEllipse(108, 108, 40, 40)  # 中心圆
    
    # 绘制图标名称"CV"
    painter.setFont(QFont("Arial", 80, QFont.Bold))
    painter.setPen(QColor(255, 255, 255))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "CV")
    
    painter.end()
    
    return QIcon(pixmap)

def get_app_icon_data():
    """获取图标的字节数据，用于保存到文件"""
    pixmap = create_app_icon().pixmap(256, 256)
    
    byte_array = QByteArray()
    buffer = QBuffer(byte_array)
    buffer.open(QIODevice.WriteOnly)
    pixmap.save(buffer, "PNG")
    
    return byte_array.data()

def save_icon_to_file(file_path):
    """将图标保存到文件"""
    try:
        icon = create_app_icon()
        pixmap = icon.pixmap(256, 256)
        result = pixmap.save(file_path, "PNG")
        return result
    except Exception as e:
        import logging
        logging.error(f"保存图标失败: {e}")
        return False

if __name__ == "__main__":
    # 如果直接运行此模块，保存图标到文件
    import os
    icon_dir = os.path.dirname(os.path.abspath(__file__))
    save_icon_to_file(os.path.join(icon_dir, "app_icon.png"))
    print(f"图标已保存到: {os.path.join(icon_dir, 'app_icon.png')}")
