"""
日志收集器，用于收集和打包日志文件以便故障排查
"""
import os
import zipfile
import datetime
import tempfile
import shutil
import logging
from config.app_config import AppConfig

class LogCollector:
    """日志收集和打包工具"""
    
    @staticmethod
    def collect_logs(output_path=None):
        """
        收集日志文件并打包
        
        Args:
            output_path: 输出路径，默认为用户桌面
            
        Returns:
            打包后的zip文件路径
        """
        try:
            # 默认保存到用户桌面
            if not output_path:
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                if not os.path.exists(desktop):
                    desktop = os.path.expanduser("~")  # 如果没有桌面目录，使用用户主目录
                
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(desktop, f"chatvision_logs_{timestamp}.zip")
            
            # 临时目录用于收集文件
            temp_dir = os.path.join(tempfile.gettempdir(), "chatvision_log_collect")
            os.makedirs(temp_dir, exist_ok=True)
            
            # 复制日志文件
            log_file = os.path.join(AppConfig.TEMP_DIR, "chatvision.log")
            if os.path.exists(log_file):
                shutil.copy2(log_file, os.path.join(temp_dir, "chatvision.log"))
            
            # 添加系统信息
            with open(os.path.join(temp_dir, "system_info.txt"), "w") as f:
                import platform
                import sys
                
                f.write("ChatVision Log Collection\n")
                f.write("=======================\n\n")
                f.write(f"Time: {datetime.datetime.now().isoformat()}\n")
                f.write(f"OS: {platform.platform()}\n")
                f.write(f"Python: {sys.version}\n")
                f.write(f"App Version: {AppConfig.APP_VERSION}\n\n")
                
                # 添加已安装的包
                f.write("Installed Packages:\n")
                try:
                    import pkg_resources
                    for pkg in pkg_resources.working_set:
                        f.write(f"  - {pkg.project_name} {pkg.version}\n")
                except ImportError:
                    f.write("  (package info not available)\n")
            
            # 创建zip文件
            with zipfile.ZipFile(output_path, "w") as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
            
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
            logging.info(f"日志文件已收集并打包到: {output_path}")
            return output_path
            
        except Exception as e:
            logging.error(f"收集日志文件失败: {str(e)}")
            return None
    
    @staticmethod
    def get_recent_logs(lines=100):
        """获取最近的日志内容"""
        try:
            log_file = os.path.join(AppConfig.TEMP_DIR, "chatvision.log")
            if not os.path.exists(log_file):
                return "Log file not found."
            
            with open(log_file, "r", encoding="utf-8") as f:
                log_lines = f.readlines()
                
            return "".join(log_lines[-lines:]) if log_lines else "No logs found."
        except Exception as e:
            return f"Error reading logs: {str(e)}"
