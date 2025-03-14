from core.llm_client import LLMClient
from core.intent_analyzer import IntentAnalyzer
from core.message import Message  # 导入消息类而不是重新定义

class ChatEngine:
    """聊天引擎，处理消息和调用插件"""
    
    def __init__(self, plugin_manager):
        self.llm_client = LLMClient()
        self.intent_analyzer = IntentAnalyzer(self.llm_client)
        self.plugin_manager = plugin_manager
        self.messages = []
        self.on_new_message = None  # 新消息回调
        self.on_processing = None  # 处理状态回调
        self.on_require_params = None  # 需要补充参数回调
        self.on_show_sidebar = None  # 显示侧边栏回调
    
    def send_message(self, content, media_files=None):
        """发送用户消息并获取回复"""
        # 创建并存储用户消息
        user_msg = Message(content, "user", media_files)
        self.messages.append(user_msg)
        
        # 通知UI更新
        if self.on_new_message:
            self.on_new_message(user_msg)
        
        # 分析用户意图
        intent_data = self.intent_analyzer.analyze_intent(content, media_files)
        task_type = intent_data["task_type"]
        parameters = intent_data["parameters"]
        
        # 检查参数是否完整
        params_complete, missing_params = self.intent_analyzer.check_parameters(task_type, parameters)
        
        if not params_complete and self.on_require_params:
            # 如果参数不完整且设置了参数请求回调，调用回调
            self.on_require_params(task_type, missing_params)
            return
            
        # 参数完整，处理消息
        if task_type != "general_chat":
            # 任务型消息，使用插件处理
            if self.on_processing:
                self.on_processing(True, f"正在处理{task_type}任务...")
                
            try:
                # 获取并调用对应的插件
                plugin = self.plugin_manager.get_plugin_for_task(task_type)
                if plugin:
                    result = plugin.process(parameters)
                    
                    # 根据任务类型和结果自动显示侧边栏
                    self._handle_sidebar_display(task_type, parameters, result)
                    
                    # 将处理结果添加到最后一条用户消息
                    user_msg.processed_results = result
                    
                    # 将处理结果发送给LLM生成自然语言回复
                    response = self._generate_response_with_result(content, result, task_type)
                else:
                    response = f"抱歉，找不到处理{task_type}的插件。"
            except Exception as e:
                response = f"处理任务时出错: {str(e)}"
            finally:
                if self.on_processing:
                    self.on_processing(False)
        else:
            # 普通聊天消息，直接发送给LLM
            response = self.llm_client.send_message(content)
        
        # 创建并存储机器人回复消息
        assistant_msg = Message(response, "assistant")
        self.messages.append(assistant_msg)
        
        # 通知UI更新
        if self.on_new_message:
            self.on_new_message(assistant_msg)
            
        return assistant_msg
    
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
    
    def _generate_response_with_result(self, user_query, result, task_type):
        """根据处理结果生成自然语言回复"""
        summary = ""
        if isinstance(result, dict) and "summary" in result:
            summary = result["summary"]
        elif isinstance(result, str):
            summary = result
            
        prompt = (
            f"用户查询: {user_query}\n\n"
            f"任务类型: {task_type}\n\n"
            f"处理结果摘要: {summary}\n\n"
            f"请根据以上信息，以友好的方式回复用户，解释处理结果。回答要自然、易懂，如同在与用户对话。"
        )
        return self.llm_client.send_message(prompt)
    
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
