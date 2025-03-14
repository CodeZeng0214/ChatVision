import requests
import json
import logging
import threading
from PySide6.QtCore import QObject, Signal
from config.llm_config import LLMConfig

class LLMClient(QObject):
    # 定义信号
    response_started = Signal()  # 响应开始信号
    response_chunk = Signal(str)  # 响应片段信号
    response_finished = Signal(str)  # 响应完成信号
    response_error = Signal(str)  # 响应错误信号
    
    def __init__(self):
        super().__init__()
        self.config = LLMConfig.get_config()
        self.conversation_history = []
        self.response_text = ""
    
    def update_config(self, **kwargs):
        """更新配置"""
        LLMConfig.update_config(**kwargs)
        self.config = LLMConfig.get_config()
    
    def add_message(self, role, content):
        """添加消息到历史"""
        self.conversation_history.append({"role": role, "content": content})
        # 维持历史长度
        if len(self.conversation_history) > self.config["max_history"]:
            self.conversation_history = self.conversation_history[-self.config["max_history"]:]
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
    
    def send_message(self, user_message):
        """发送消息并获取回复（同步版本，保留以兼容旧代码）"""
        # 创建线程等待响应完成
        response_received = threading.Event()
        complete_response = [""]
        
        def on_complete(response_text):
            complete_response[0] = response_text
            response_received.set()
        
        # 注册临时的完成和错误处理器
        self.response_finished.connect(on_complete)
        self.response_error.connect(on_complete)
        
        # 启动异步发送
        self.send_message_async(user_message)
        
        # 等待响应
        response_received.wait()
        
        # 断开信号连接
        self.response_finished.disconnect(on_complete)
        self.response_error.disconnect(on_complete)
        
        return complete_response[0]
    
    def send_message_async(self, user_message):
        """异步发送消息并通过信号返回流式响应"""
        # 重置状态
        self.response_text = ""
        
        # 创建工作线程
        thread = threading.Thread(
            target=self._process_message_stream,
            args=(user_message,)
        )
        thread.daemon = True
        thread.start()
    
    def _process_message_stream(self, user_message):
        """在工作线程中处理消息流"""
        try:
            logging.info("发送普通聊天消息到LLM（流式响应）")
            self.add_message("user", user_message)
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config['api_key']}"
            }
            
            payload = {
                "model": self.config["model"],
                "messages": self.conversation_history,
                "temperature": 0.7,
                "stream": True  # 启用流式输出
            }
            
            logging.info(f"发送流式请求到 LLM API: {self.config['base_url']}")
            
            # 通知开始响应
            self.response_started.emit()
            
            # 发送流式请求
            response = requests.post(
                f"{self.config['base_url']}/chat/completions",
                headers=headers,
                data=json.dumps(payload),
                stream=True,  # 启用流式响应
                timeout=60     # 增加超时时间
            )
            
            if response.status_code != 200:
                error_data = json.loads(response.text)
                error_msg = f"API错误: {error_data.get('error', {}).get('message', '未知错误')}"
                logging.error(f"LLM API 流式响应错误: {error_msg}")
                self.response_error.emit(error_msg)
                return
                
            # 处理流式响应
            for line in response.iter_lines():
                if line:
                    # 去除 "data: " 前缀
                    line_text = line.decode('utf-8')
                    if line_text.startswith("data: "):
                        line_text = line_text[6:]
                    else:
                        continue
                        
                    if line_text == "[DONE]":
                        break
                        
                    try:
                        chunk_data = json.loads(line_text)
                        if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                            delta = chunk_data["choices"][0].get("delta", {})
                            if "content" in delta:
                                content = delta["content"]
                                self.response_text += content
                                self.response_chunk.emit(content)
                    except json.JSONDecodeError:
                        logging.warning(f"无法解析流式响应行: {line_text}")
                        continue
            
            # 保存完整响应到历史
            self.add_message("assistant", self.response_text)
            logging.info("流式响应完成")
            
            # 发送完成信号
            self.response_finished.emit(self.response_text)
            
        except requests.exceptions.ConnectionError:
            error_msg = "连接错误: 无法连接到 LLM API 服务器"
            logging.error(error_msg)
            self.response_error.emit(error_msg)
        except requests.exceptions.Timeout:
            error_msg = "请求超时: LLM API 响应超时"
            logging.error(error_msg)
            self.response_error.emit(error_msg)
        except Exception as e:
            error_msg = f"通信错误: {str(e)}"
            logging.error(f"LLM 请求异常: {str(e)}", exc_info=True)
            self.response_error.emit(error_msg)
