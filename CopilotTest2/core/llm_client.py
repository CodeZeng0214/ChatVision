import requests
import json
import logging
from config.llm_config import LLMConfig

class LLMClient:
    def __init__(self):
        self.config = LLMConfig.get_config()
        self.conversation_history = []
    
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
        """发送消息并获取回复"""
        try:
            # 记录普通聊天请求
            logging.info("发送普通聊天消息到LLM")
            self.add_message("user", user_message)
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config['api_key']}"
            }
            
            payload = {
                "model": self.config["model"],
                "messages": self.conversation_history,
                "temperature": 0.7
            }
            
            logging.info(f"发送请求到 LLM API: {self.config['base_url']}")
            
            response = requests.post(
                f"{self.config['base_url']}/chat/completions",
                headers=headers,
                data=json.dumps(payload),
                timeout=30  # 设置超时时间为30秒
            )
            
            response_data = response.json()
            
            if response.status_code == 200:
                assistant_message = response_data["choices"][0]["message"]["content"]
                self.add_message("assistant", assistant_message)
                logging.info("收到LLM普通聊天回复")
                return assistant_message
            else:
                error_message = f"API错误: {response_data.get('error', {}).get('message', '未知错误')}"
                logging.error(f"LLM API 错误: {error_message}")
                return error_message
                
        except requests.exceptions.ConnectionError:
            error_msg = "连接错误: 无法连接到 LLM API 服务器"
            logging.error(error_msg)
            return error_msg
        except requests.exceptions.Timeout:
            error_msg = "请求超时: LLM API 响应超时"
            logging.error(error_msg)
            return error_msg
        except json.JSONDecodeError:
            error_msg = "解析错误: LLM API 返回了无效的 JSON"
            logging.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"通信错误: {str(e)}"
            logging.error(f"LLM 请求异常: {str(e)}", exc_info=True)
            return error_msg
