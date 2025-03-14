import os
import cv2
import tempfile
import logging
import glob
import threading
from plugins.base_plugin import BasePlugin

class BatchProcessingPlugin(BasePlugin):
    """批量处理插件，处理文件夹中的多个图像"""
    
    def __init__(self):
        super().__init__()
        self.name = "批量图像处理"
        self.description = "批量处理指定目录中的图像文件"
        self.config = {
            "result_dir": os.path.join(tempfile.gettempdir(), "chatvision_results"),
            "supported_extensions": ['.jpg', '.jpeg', '.png', '.bmp', '.gif'],
            "task_plugin": "YOLO目标检测",  # 默认使用YOLO处理
            "max_files": 100,  # 最大处理文件数
            "recursive": False  # 是否递归处理子文件夹
        }
        
        # 创建结果目录
        os.makedirs(self.config["result_dir"], exist_ok=True)
        
        self.stop_flag = False
        self.progress_callback = None
    
    def process(self, parameters):
        """处理批量任务"""
        # 获取参数
        directory = None
        target_plugin = None
        
        if "directory" in parameters:
            directory = parameters["directory"]
        if "target" in parameters:
            target_plugin = parameters["target"]
        else:
            target_plugin = self.config["task_plugin"]
        
        # 验证参数
        if not directory or not os.path.isdir(directory):
            return "请指定有效的目录路径"
        
        # 从插件管理器获取目标插件
        from plugins.plugin_manager import PluginManager
        plugin_manager = PluginManager()
        plugin_manager.load_plugins()
        
        target_plugin_obj = plugin_manager.get_plugin_by_name(target_plugin)
        if not target_plugin_obj:
            return f"找不到插件: {target_plugin}"
        
        # 创建批处理结果目录
        batch_result_dir = os.path.join(
            self.config["result_dir"],
            f"batch_result_{os.path.basename(directory)}"
        )
        os.makedirs(batch_result_dir, exist_ok=True)
        
        # 获取所有图片文件
        pattern = os.path.join(directory, "*" if not self.config["recursive"] else "**/*")
        all_files = []
        
        for ext in self.config["supported_extensions"]:
            if self.config["recursive"]:
                all_files.extend(glob.glob(pattern + ext, recursive=True))
            else:
                all_files.extend(glob.glob(pattern + ext))
        
        # 限制文件数量
        if len(all_files) > self.config["max_files"]:
            all_files = all_files[:self.config["max_files"]]
        
        # 处理所有文件
        results = []
        success_count = 0
        fail_count = 0
        
        # 创建线程对象
        self.stop_flag = False
        processing_thread = threading.Thread(
            target=self._process_files_thread,
            args=(target_plugin_obj, all_files, batch_result_dir, results)
        )
        
        # 开始处理
        processing_thread.start()
        
        # 返回初步结果
        return {
            "status": "processing",
            "total_files": len(all_files),
            "result_dir": batch_result_dir,
            "message": f"正在处理 {len(all_files)} 个文件，使用 {target_plugin} 插件"
        }
    
    def _process_files_thread(self, plugin, files, result_dir, results):
        """在线程中处理所有文件"""
        success_count = 0
        fail_count = 0
        total_count = len(files)
        
        for i, file_path in enumerate(files):
            if self.stop_flag:
                break
                
            try:
                # 构建参数
                params = {
                    "files": [file_path]
                }
                
                # 调用插件处理
                result = plugin.process(params)
                
                # 记录结果
                if isinstance(result, dict) and "result_image" in result:
                    # 复制结果到批处理结果目录
                    file_name = os.path.basename(file_path)
                    result_path = os.path.join(result_dir, file_name)
                    
                    try:
                        # 复制处理结果图片
                        img = cv2.imread(result["result_image"])
                        cv2.imwrite(result_path, img)
                        
                        # 记录成功
                        results.append({
                            "file": file_path,
                            "result": result_path,
                            "success": True,
                            "data": result.get("summary", "")
                        })
                        success_count += 1
                    except Exception as e:
                        logging.error(f"保存结果失败: {e}")
                        results.append({
                            "file": file_path,
                            "success": False,
                            "error": f"保存结果失败: {str(e)}"
                        })
                        fail_count += 1
                else:
                    # 处理失败
                    results.append({
                        "file": file_path,
                        "success": False,
                        "error": str(result) if isinstance(result, str) else "未知错误"
                    })
                    fail_count += 1
            
            except Exception as e:
                logging.error(f"处理文件失败 {file_path}: {e}")
                results.append({
                    "file": file_path,
                    "success": False,
                    "error": str(e)
                })
                fail_count += 1
            
            # 更新进度
            if self.progress_callback:
                self.progress_callback(i+1, total_count)
        
        # 生成报告
        report_path = os.path.join(result_dir, "batch_report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"批处理报告\n")
            f.write(f"总文件数: {total_count}\n")
            f.write(f"成功处理: {success_count}\n")
            f.write(f"处理失败: {fail_count}\n\n")
            
            f.write("详细结果:\n")
            for r in results:
                if r["success"]:
                    f.write(f"[成功] {r['file']} -> {r['result']}\n")
                    if "data" in r:
                        f.write(f"  结果: {r['data']}\n")
                else:
                    f.write(f"[失败] {r['file']}: {r['error']}\n")
    
    def stop_processing(self):
        """停止当前处理"""
        self.stop_flag = True
    
    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback
    
    def get_required_parameters(self):
        """获取插件需要的参数列表"""
        return ["directory"]
    
    def get_task_types(self):
        """获取插件支持的任务类型列表"""
        return ["batch_processing"]
