## 流式响应无法实现选择性输出ChatGPT回复的内容

from openai import OpenAI

GPT_model = 'gpt-4o-mini'

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key = "sk-AencKA6Oy7WnhukWgquDlbis89fhQ5q4Nz8ba4BvYJUjy8LR",
    base_url = "https://api.chatanywhere.tech/v1"
)

# 流式响应
def GPT_stream(messages: list):
    """为提供的对话消息创建新的回答 (流式传输)

    Args:
        messages (list): 完整的对话消息
    """
    stream = client.chat.completions.create(
        model = GPT_model,
        messages = messages,
        stream = True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end = "")
    print("\n")
            
def Init_message(messages: list):
    init_messages = '我需要你在接下来的对话中。如果我有输入的文件路径，先将其返回，并在路径首尾加上￥，你的回答就另起一段' 
    messages.append({'role': 'user', 'content': init_messages})
    GPT_stream(messages)
    return messages
    
if __name__ == '__main__':
    messages = []
    messages = Init_message(messages)
    
    print("开始对话（输入'退出'以结束）：")
    while True:
        user_input = input("你: ")
        if user_input.lower() == '退出':
            break
        
        # 添加用户输入到消息列表
        messages.append({'role': 'user', 'content': user_input})
        
        # 调用流式响应函数
        print("助手: ", end = "")
        GPT_stream(messages)
        