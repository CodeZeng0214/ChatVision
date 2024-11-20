from openai import OpenAI

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key="sk-AencKA6Oy7WnhukWgquDlbis89fhQ5q4Nz8ba4BvYJUjy8LR",
    base_url="https://api.chatanywhere.tech/v1"
)



# 非流式响应
def gpt_35_api(messages: list):
    """为提供的对话消息创建新的回答

    Args:
        messages (list): 完整的对话消息
    """
    completion = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
    print(completion.choices[0].message.content)

def GPT_stream(messages: list):
    """为提供的对话消息创建新的回答 (流式传输)

    Args:
        messages (list): 完整的对话消息
    """
    stream = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=messages,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="")
    

#if __name__ == '__main__':
    #messages = [{'role': 'user','content': '鲁迅和周树人的关系'},]
    # 非流式调用
    # gpt_35_api(messages)
    # 流式调用
    #gpt_35_api_stream(messages)
    
if __name__ == '__main__':
    messages = []
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
    
    
    
        