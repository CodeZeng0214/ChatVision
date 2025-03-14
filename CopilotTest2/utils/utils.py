"""
工具函数模块
"""
import os
import cv2
import tempfile
import logging
import time
import hashlib
import numpy as np
from pathlib import Path

def ensure_dir(directory):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def get_file_hash(file_path):
    """计算文件的SHA256哈希值"""
    hash_obj = hashlib.sha256()
    with open(file_path, "rb") as f:
        # 读取文件块并更新哈希
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def get_temp_path(prefix='chatvision_', suffix=None):
    """获取临时文件路径"""
    temp_dir = os.path.join(tempfile.gettempdir(), "chatvision")
    ensure_dir(temp_dir)
    
    if suffix:
        return os.path.join(temp_dir, f"{prefix}{int(time.time())}{suffix}")
    else:
        return os.path.join(temp_dir, f"{prefix}{int(time.time())}")

def is_image_file(file_path):
    """检查文件是否为图像文件"""
    if not os.path.exists(file_path):
        return False
    
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']
    return Path(file_path).suffix.lower() in image_extensions

def is_video_file(file_path):
    """检查文件是否为视频文件"""
    if not os.path.exists(file_path):
        return False
    
    video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv']
    return Path(file_path).suffix.lower() in video_extensions

def resize_image(image, max_width=800, max_height=600):
    """调整图像大小，保持宽高比"""
    height, width = image.shape[:2]
    
    # 计算缩放比例
    scale_w = max_width / width if width > max_width else 1
    scale_h = max_height / height if height > max_height else 1
    scale = min(scale_w, scale_h)
    
    # 如果不需要缩放，直接返回原图
    if scale >= 1:
        return image
    
    # 计算新尺寸
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    # 调整大小
    resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    return resized

def get_video_info(video_path):
    """获取视频信息"""
    if not is_video_file(video_path):
        return None
    
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        # 获取视频参数
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 提取视频缩略图
        success, frame = cap.read()
        thumbnail = None
        if success:
            thumbnail = resize_image(frame)
        
        cap.release()
        
        return {
            "width": width,
            "height": height,
            "fps": fps,
            "frame_count": frame_count,
            "duration": frame_count / fps if fps > 0 else 0,
            "thumbnail": thumbnail
        }
    except Exception as e:
        logging.error(f"获取视频信息失败: {e}")
        return None

def extract_video_frame(video_path, frame_number=0):
    """从视频中提取特定帧作为图像"""
    if not is_video_file(video_path):
        return None
    
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        # 设置帧位置
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        # 读取帧
        success, frame = cap.read()
        cap.release()
        
        if success:
            return frame
        else:
            return None
    except Exception as e:
        logging.error(f"提取视频帧失败: {e}")
        return None

def create_thumbnail(file_path, output_path=None, width=200, height=200):
    """为图像或视频创建缩略图"""
    if not os.path.exists(file_path):
        return None
    
    try:
        if is_image_file(file_path):
            # 处理图像
            image = cv2.imread(file_path)
            if image is None:
                return None
            thumbnail = resize_image(image, width, height)
        elif is_video_file(file_path):
            # 处理视频
            video_info = get_video_info(file_path)
            if video_info and video_info["thumbnail"] is not None:
                thumbnail = video_info["thumbnail"]
            else:
                return None
        else:
            return None
        
        # 如果指定了输出路径，保存缩略图
        if output_path:
            cv2.imwrite(output_path, thumbnail)
        
        return thumbnail
    except Exception as e:
        logging.error(f"创建缩略图失败: {e}")
        return None

def overlay_text(image, text, position=(10, 30), font_scale=1.0, color=(255, 255, 255),
               thickness=2, background=True, bg_color=(0, 0, 0), bg_alpha=0.5):
    """在图像上叠加文本，可选带背景"""
    # 复制原图像，以免修改原图
    result = image.copy()
    
    # 获取文本大小
    (text_width, text_height), baseline = cv2.getTextSize(
        text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
    
    if background:
        # 添加背景矩形
        p1 = (position[0], position[1] - text_height - baseline)
        p2 = (position[0] + text_width, position[1] + baseline)
        
        # 创建叠加图层
        overlay = result.copy()
        cv2.rectangle(overlay, p1, p2, bg_color, -1)
        
        # 应用透明度
        cv2.addWeighted(overlay, bg_alpha, result, 1 - bg_alpha, 0, result)
    
    # 绘制文本
    cv2.putText(result, text, position, cv2.FONT_HERSHEY_SIMPLEX,
              font_scale, color, thickness)
    
    return result
