import logging
import threading
from PySide6.QtCore import QObject, Signal
from core.llm_client import LLMClient
from core.intent_analyzer import IntentAnalyzer
from core.message import Message  # 导入消息类而不是重新定义

class ChatEngine(QObject):
    """聊天引擎，处理消息和调用插件"""
    
    # 定义新的信号
    message_response_started = Signal(object)  # 参数是Message对象
    message_response_chunk = Signal(object, str)  # 参数是Message对象和文本块
    message_response_complete = Signal(object)  # 参数是Message对象
    
    def __init__(self, plugin_manager):
        super().__init__()
        self.llm_client = LLMClient()
        self.intent_analyzer = IntentAnalyzer(self.llm_client)
        self.plugin_manager = plugin_manager
        self.messages = []
        self.on_new_message = None  # 新消息回调
        self.on_processing = None  # 处理状态回调
        self.on_require_params = None  # 需要补充参数回调
        self.on_show_sidebar = None  # 显示侧边栏回调
        
        # 连接LLM客户端信号
        self.llm_client.response_started.connect(self._on_llm_response_started)
        self.llm_client.response_chunk.connect(self._on_llm_response_chunk)
        self.llm_client.response_finished.connect(self._on_llm_response_finished)
        self.llm_client.response_error.connect(self._on_llm_response_error)
        
        # 当前处理的消息
        self.current_assistant_msg = None
    
    def send_message(self, content, media_files=None):
        """发送用户消息并获取回复"""
        # 创建并存储用户消息
        user_msg = Message(content, "user", media_files)
        self.messages.append(user_msg)
        
        # 立即通知UI更新，显示用户消息
        if self.on_new_message:
            self.on_new_message(user_msg)
        
        # 分析用户意图
        intent_data = self.intent_analyzer.analyze_intent(content, media_files)
        task_type = intent_data["task_type"]
        parameters = intent_data["parameters"]
        
        # 创建助手消息占位符，显示为"正在输入..."
        self.current_assistant_msg = Message("正在思考...", "assistant")
        self.messages.append(self.current_assistant_msg)
        
        # 立即通知UI更新，显示"正在输入..."
        if self.on_new_message:
            self.on_new_message(self.current_assistant_msg)
        
        # 使用线程处理消息，避免阻塞UI
        threading.Thread(
            target=self._process_message,
            args=(user_msg, task_type, parameters),
            daemon=True
        ).start()
        
        return user_msg
    
    def _process_message(self, user_msg, task_type, parameters):
        """在工作线程中处理消息"""
        try:
            # 根据任务类型选择处理方式
            if task_type == "general_chat":
                # 普通聊天消息，直接发送给LLM（使用异步流式响应）
                logging.info("检测到普通聊天，将消息发送给LLM")
                self.llm_client.send_message_async(user_msg.content)
                # 响应将通过信号处理
            else:
                # 任务型消息，检查参数是否完整
                params_complete, missing_params = self.intent_analyzer.check_parameters(task_type, parameters)
                
                if not params_complete:
                    # 如果参数不完整且设置了参数请求回调，在主线程中调用回调
                    if self.on_require_params:
                        # 移除临时的助手消息
                        self.messages.pop()
                        # 设置当前消息为None
                        self.current_assistant_msg = None
                        # 触发参数请求回调
                        self.on_require_params(task_type, missing_params)
                    return
                
                # 参数完整，使用插件处理任务
                if self.on_processing:
                    self.on_processing(True, f"正在处理{task_type}任务...")
                    
                try:
                    # 获取并调用对应的插件
                    plugin = self.plugin_manager.get_plugin_for_task(task_type)
                    if plugin:
                        result = plugin.process(parameters)
                        
                        # 根据任务类型和结果自动显示侧边栏
                        self._handle_sidebar_display(task_type, parameters, result)
                        
                        # 将处理结果添加到用户消息
                        user_msg.processed_results = result
                        
                        # 将处理结果发送给LLM生成自然语言回复
                        prompt = self._generate_response_prompt(user_msg.content, result, task_type)
                        self.llm_client.send_message_async(prompt)
                        # 响应将通过信号处理
                    else:
                        response = f"抱歉，找不到处理{task_type}的插件。如果您想进行普通聊天，请直接输入问题而不要提及图像处理相关词汇。"
                        self._update_assistant_message(response)
                except Exception as e:
                    response = f"处理任务时出错: {str(e)}"
                    self._update_assistant_message(response)
                finally:
                    if self.on_processing:
                        self.on_processing(False)
        except Exception as e:
            logging.error(f"处理消息时出错: {str(e)}", exc_info=True)
            self._update_assistant_message(f"处理消息时出错: {str(e)}")
    
    def _update_assistant_message(self, content):
        """更新助手消息内容"""
        if self.current_assistant_msg:
            self.current_assistant_msg.content = content
            # 通知UI更新
            if self.on_new_message:
                self.on_new_message(self.current_assistant_msg)
    
    def _generate_response_prompt(self, user_query, result, task_type):
        """生成根据处理结果的提示"""
        summary = ""
        if isinstance(result, dict) and "summary" in result:
            summary = result["summary"]
        elif isinstance(result, str):
            summary = result
            
        return (
            f"用户查询: {user_query}\n\n"
            f"任务类型: {task_type}\n\n"
            f"处理结果摘要: {summary}\n\n"
            f"请根据以上信息，以友好的方式回复用户，解释处理结果。回答要自然、易懂，如同在与用户对话。"
        )
    
    # LLM客户端信号处理程序
    def _on_llm_response_started(self):
        """LLM开始响应处理"""
        logging.info("LLM开始响应")
        if self.current_assistant_msg:
            self.current_assistant_msg.content = ""
            self.message_response_started.emit(self.current_assistant_msg)
    
    def _on_llm_response_chunk(self, chunk):
        """LLM响应片段处理"""
        if self.current_assistant_msg:
            self.current_assistant_msg.content += chunk
            self.message_response_chunk.emit(self.current_assistant_msg, chunk)
            # 通知UI更新
            if self.on_new_message:
                self.on_new_message(self.current_assistant_msg)
    
    def _on_llm_response_finished(self, complete_text):
        """LLM响应完成处理"""
        logging.info("LLM响应完成")
        if self.current_assistant_msg:
            # 确保最终内容是完整的
            self.current_assistant_msg.content = complete_text
            self.message_response_complete.emit(self.current_assistant_msg)
            # 通知UI更新
            if self.on_new_message:
                self.on_new_message(self.current_assistant_msg)
            self.current_assistant_msg = None
    
    def _on_llm_response_error(self, error_msg):
        """LLM响应错误处理"""
        logging.error(f"LLM响应错误: {error_msg}")
        if self.current_assistant_msg:
            self.current_assistant_msg.content = f"发生错误: {error_msg}"
            # 通知UI更新
            if self.on_new_message:
                self.on_new_message(self.current_assistant_msg)
            self.current_assistant_msg = None
    
    def _handle_sidebar_display(self, task_type, parameters, result):
        """根据任务类型和结果处理侧边栏显示"""
        if not self.on_show_sidebar:
            return
            
        if task_type == "image_recognition" or task_type == "image_description" or task_type == "pose_estimation":
            # 图像处理任务，显示原始图像和处理后的图像对比
            if isinstance(result, dict) and "original_image" in result and "result_image" in result:
                self.on_show_sidebar("image_comparison", result["original_image"], result["result_image"])
                
        elif task_type == "batch_processing":
            # 批量处理任务，如果有示例结果图像，显示
            if isinstance(result, dict) and "result_dir" in result:
                self.on_show_sidebar("directory", result["result_dir"])
                
        elif task_type == "realtime_processing":
            # 实时处理任务，启动摄像头
            if isinstance(result, dict) and "camera_id" in result and "task" in result:
                camera_id = result.get("camera_id", 0)
                process_type = result.get("task", "none")
                self.on_show_sidebar("camera", camera_id, process_type)
    
    def update_message_with_params(self, task_type, parameters):
        """更新消息并添加补充的参数"""
        # 获取最后一条用户消息
        last_user_msg = next((msg for msg in reversed(self.messages) if msg.sender == "user"), None)
        if last_user_msg:
            self.send_message(last_user_msg.content, parameters.get("files"))
    
    def clear_history(self):
        """清空聊天历史"""
        self.messages = []
        self.llm_client.clear_history()
        self.current_assistant_msg = None
    
    def get_last_user_message(self):
        """获取最后一条用户消息"""
        for msg in reversed(self.messages):
            if msg.sender == "user":
                return msg
        return None
    
    def get_processing_status(self):
        """获取当前处理状态"""
        # 可以添加更多状态指示
        return {
            "total_messages": len(self.messages),
            "has_user_message": any(msg.sender == "user" for msg in self.messages),
            "has_assistant_message": any(msg.sender == "assistant" for msg in self.messages),
            "has_media": any(msg.media_files for msg in self.messages)
        }
