"""
错误处理和异常恢复工具
"""
import sys
import traceback
import logging
from PySide6.QtWidgets import QMessageBox, QApplication

class ErrorHandler:
    """全局错误处理器"""
    
    @staticmethod
    def setup_exception_handling():
        """设置全局异常处理"""
        # 保存原始的excepthook
        original_excepthook = sys.excepthook
        
        # 自定义异常处理
        def exception_hook(exctype, value, tb):
            # 记录异常
            logging.critical("未捕获的异常:", exc_info=(exctype, value, tb))
            
            # 获取完整的堆栈跟踪
            stack_trace = "".join(traceback.format_exception(exctype, value, tb))
            
            # 如果GUI可用，显示错误对话框
            try:
                app = QApplication.instance()
                if app:
                    ErrorHandler.show_error_dialog(str(value), stack_trace)
            except Exception as e:
                logging.error(f"显示错误对话框失败: {e}")
            
            # 调用原始的异常处理
            original_excepthook(exctype, value, tb)
            
        # 设置全局异常处理器
        sys.excepthook = exception_hook
    
    @staticmethod
    def show_error_dialog(error_message, details=None):
        """显示错误对话框"""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("错误")
        msg_box.setText("程序遇到了一个错误:")
        msg_box.setInformativeText(error_message)
        
        if details:
            msg_box.setDetailedText(details)
        
        msg_box.addButton(QMessageBox.Ok)
        msg_box.exec()
    
    @staticmethod
    def report_error(error, context="", send_report=False):
        """记录错误并可选择发送报告"""
        logging.error(f"{context}: {str(error)}")
        
        if send_report:
            # 这里可以添加发送错误报告到服务器的代码
            from utils.log_collector import LogCollector
            log_path = LogCollector.collect_logs()
            if log_path:
                logging.info(f"错误日志已收集到: {log_path}")
                return log_path
        
        return None
