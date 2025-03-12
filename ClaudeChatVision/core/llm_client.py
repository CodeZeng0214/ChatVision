import json
import requests
import os
import time

class LLMClient:
    """大语言模型客户端，用于生成自然语言响应
    
    提供与大语言模型API的通信功能，用于生成对话响应和格式化视觉任务结果。
    支持通过设置更改API参数，可根据需要启用或禁用API调用。
    """
    def __init__(self):
        """初始化LLM客户端
        
        设置默认的API配置，包括基础URL、API密钥和模型名称。
        默认禁用API调用，避免意外产生API费用。
        """
        # 默认配置 - 可以通过设置更改
        self.base_url = "https://api.chatanywhere.tech/v1"
        self.api_key = "sk-AencKA6Oy7WnhukWgquDlbis89fhQ5q4Nz8ba4BvYJUjy8LR"
        self.model = "gpt-4o-mini"
        self.enabled = False  # 默认禁用，避免意外的API调用
    
    def generate_response(self, prompt, system_message=None):
        """使用大语言模型生成响应
        
        将用户提示和可选的系统消息发送到LLM API，获取生成的回复。
        如果LLM功能被禁用，则返回占位符响应。
        
        参数:
            prompt (str): 用户提示文本
            system_message (str): 可选的系统指令消息
            
        返回:
            str: 大语言模型生成的响应或占位符文本
        """
        if not self.enabled:
            return "LLM集成功能已禁用。(占位符响应)"
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            messages = []
            
            # 如果提供了系统消息，添加到消息列表
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            # 添加用户提示
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": self.model,
                "messages": messages
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                print(f"错误: {response.status_code}")
                print(response.text)
                return f"调用LLM API时出错: {response.status_code}"
                
        except Exception as e:
            print(f"异常: {e}")
            return f"错误: {str(e)}"
    
    def format_vision_results(self, task_type, results_data):
        """将视觉处理结果格式化为自然语言
        
        使用LLM将技术性的视觉处理结果转换为更自然、更易于理解的文本。
        如果LLM功能被禁用，则使用简单的格式化方法。
        
        参数:
            task_type (str): 视觉任务类型，如"object_detection"
            results_data (dict): 任务处理结果数据
            
        返回:
            str: 格式化后的结果文本
        """
        if not self.enabled:
            # 如果LLM被禁用，返回简单格式化的字符串
            return self._simple_format_results(task_type, results_data)
        
        # 为LLM准备格式化结果的提示
        prompt = f"以下是来自{task_type}任务的结果。请以自然、对话式的方式格式化这些结果:\n\n"
        prompt += json.dumps(results_data, indent=2)
        
        system_message = "你是一个将技术结果转换为自然语言回复的助手。保持回答简洁友好。"
        
        return self.generate_response(prompt, system_message)
    
    def _simple_format_results(self, task_type, results_data):
        """当LLM被禁用时使用的简单格式化器
        
        根据任务类型使用不同的格式化逻辑，生成简单的结果描述。
        
        参数:
            task_type (str): 视觉任务类型
            results_data (dict): 任务处理结果数据
            
        返回:
            str: 简单格式化的结果文本
        """
        if task_type == "object_detection":
            text = "我检测到以下物体:\n"
            for obj, count in results_data.get("objects", {}).items():
                text += f"- {count}个 {obj}\n"
            return text
            
        elif task_type == "pose_estimation":
            return "我分析了图像中的姿势: " + results_data.get("summary", "无可用结果。")
            
        elif task_type == "image_caption":
            return "图像描述: " + results_data.get("caption", "无可用描述。")
            
        else:
            return "结果: " + str(results_data)
    
    def update_settings(self, settings):
        """更新LLM客户端设置
        
        允许从应用程序设置更新API配置参数。
        
        参数:
            settings (dict): 包含要更新的设置的字典
        """
        if "base_url" in settings:
            self.base_url = settings["base_url"]
        if "api_key" in settings:
            self.api_key = settings["api_key"]
        if "model" in settings:
            self.model = settings["model"]
        if "enabled" in settings:
            self.enabled = settings["enabled"]
    
    def process_user_query(self, query, task_results=None):
        """处理用户查询，可选择包含任务结果上下文
        
        使用LLM生成对用户查询的响应，如果有任务结果则将其作为上下文。
        如果LLM功能被禁用，则返回简单响应。
        
        参数:
            query (str): 用户查询文本
            task_results (dict): 可选的任务结果上下文
            
        返回:
            str: 对用户查询的响应
        """
        if not self.enabled:
            # 如果LLM被禁用，返回简单响应
            if task_results:
                return f"我已经使用{task_results.get('task_type', '视觉处理')}处理了您的请求。请在侧边栏查看结果。"
            else:
                return "我可以帮助您处理视觉任务。请提供图像或指定任务。"
        
        # 从任务结果构建上下文（如果有）
        context = ""
        if task_results:
            context = f"任务类型: {task_results.get('task_type', '未知')}\n"
            context += f"结果: {json.dumps(task_results, indent=2)}\n\n"
        
        # 准备提示
        prompt = f"{context}用户查询: {query}\n\n请根据任务结果回复用户查询。"
        
        system_message = "你是一个专注于计算机视觉任务的助手。根据视觉处理任务的结果回答用户。"
        
        return self.generate_response(prompt, system_message)
