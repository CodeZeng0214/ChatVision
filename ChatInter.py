## 定义语言大模型聊天接口

from openai import OpenAI
from typing import Callable, Optional


### ========== 全局参数 ========== ###
BASE_URL = "https://api.chatanywhere.tech/v1" # 默认语义大模型网站
API_KEY = "sk-AencKA6Oy7WnhukWgquDlbis89fhQ5q4Nz8ba4BvYJUjy8LR" # 默认网站密钥
GPT_MODEL = 'gpt-4o-mini' # 默认GPT模型


### ========== ChatGPT聊天类 ========== ###
class ChatGPT():
    """
    实例化一个GPT聊天\n
    api_key 密钥设置 默认值 "sk-AencKA6Oy7WnhukWgquDlbis89fhQ5q4Nz8ba4BvYJUjy8LR"\n
    base_url 网址设置 默认值 "https://api.chatanywhere.tech/v1"\n
    gpt_model GPT选用的模型 默认值 'gpt-4o-mini'
    """
    def __init__(self, api_key=API_KEY, base_url=BASE_URL, gpt_model=GPT_MODEL):
        self.api_key = api_key # 密钥
        self.base_url = base_url # 网址
        self.model = gpt_model # 选用的模型
        self.chatcase = OpenAI(api_key=self.api_key, base_url=self.base_url) # 创建的聊天接口
        
    # 非流式响应
    def UnstreamResponse(self, messages: list):
        """为提供的对话消息创建新的回答(非流式响应)\n
        messages (list): 完整的对话消息以增强上下文的记忆
        """
        completion = self.chatcase.chat.completions.create(model=self.model, messages=messages)
        response = completion.choices[0].message.content
        #print(response_unstream)
        return response
    
    # 流式响应
    def StreamResponse(self, messages: list, progress_callback: Optional[Callable[[str], None]] = None):
        """
        为提供的对话消息创建新的回答(流式响应)\n
        messages (list): 完整的对话消息以增强上下文的记忆\n
        progress_callback (callable, optional): 用于接收部分响应的回调函数
        """
        # print(messages[0]['content']) # 测试输入给ChatGPT的信息
        stream = self.chatcase.chat.completions.create(
            model = self.model,
            messages = messages,
            stream = True,
        )
        response = ""
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                response += content
                print(content, end="")
                
                # 如果提供了回调函数，则调用它传递当前进度
                if progress_callback:
                    progress_callback(content)
                    
        print("")
        return response