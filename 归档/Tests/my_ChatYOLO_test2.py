##利用非流式响应加流式响应实现选择性输出ChatGPT回复的内容

from openai import OpenAI
import re
from ultralytics import YOLO


GPT_model = 'gpt-4o-mini'
YOLO_weight = "./weights\YOLO11\yolo11s.pt"
YOLO_results_dir = "./runs"



client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key = "sk-AencKA6Oy7WnhukWgquDlbis89fhQ5q4Nz8ba4BvYJUjy8LR",
    base_url = "https://api.chatanywhere.tech/v1"
)

# 非流式响应
def GPT_un_stream(messages: list):
    """为提供的对话消息创建新的回答

    Args:
        messages (list): 完整的对话消息
    """
    completion = client.chat.completions.create(model = GPT_model, messages = messages)
    response_un_stream = completion.choices[0].message.content
    #print(completion.choices[0].message.content)
    return response_un_stream

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
    chatYOLO_response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            chatYOLO_response += chunk.choices[0].delta.content
            print(chunk.choices[0].delta.content, end = "")
    print("\n")
    return chatYOLO_response
    
    
def GPT_reponse(messages: list, is_print):
    
    isYOLO = False
    yolo_response = []
    
    response_un_stream = GPT_un_stream(messages)
    
    ## 提取GPT回答的信息
    path_match = re.findall(r'￥(.*?)￥', response_un_stream)
    if path_match != []:
        #print(path_match[0])
        isYOLO = True
        messages[-1]['content'] = re.sub(r'^".*\\', '"', messages[-1]['content'])
    else:
        #print("输入不包含路径")
        isYOLO = False
        
    
    ## 执行YOLO图像识别
    if isYOLO:
        print("正在执行图像识别任务")
        model = YOLO(YOLO_weight)
        results = model.predict(source=path_match[0], save=True, show=False, project = YOLO_results_dir, save_txt=True,  verbose=False)
        print("检测完成")
        with open('./results\detection_results.txt', 'w') as file:
            for result in results:
            # result是一个检测结果对象，通常包含边界框、标签、置信度等信息
                for detection in result.boxes:  # 访问每个检测的框
                # 提取边界框坐标、置信度和标签
                    x1, y1, x2, y2 = detection.xyxy[0]  # 左上角和右下角坐标
                    conf = detection.conf[0]  # 置信度
                    conf = 100*conf
                    cls = int(detection.cls[0])  # 类别索引
                    label = model.names[cls]  # 获取类别名称

                    # 写入文本文件
                    file.write(f"在图像的 [{x1:.2f}, {y1:.2f}, {x2:.2f}, {y2:.2f}] 位置检测到有{conf:.2f}%置信度的 {label} 对象\n")
        with open('./results\detection_results.txt', 'r') as file:
            yolo_response = file.read()
            
    ## 将处理后的回答再返回给GPT做流式响应
    if is_print:
        if yolo_response != []:
            temp_message = []
            yolo_response =  ''.join(yolo_response) + "以上的内容是我利用YOLO识别用户输入的图像的返回信息，请你根据这些信息回答用户的问题：\n" + messages[-1]['content']
            temp_message.append({'role': 'user', 'content': yolo_response})
            messages.append({'role': 'assistant', 'content': GPT_stream(temp_message)})
        else:
            messages.append({'role': 'assistant', 'content': GPT_stream(messages)})
    return messages
            
        
## 教会GPT接下来按需求回复的初始化模板
def Init_message(messages: list):
    init_messages = '我需要你在接下来的对话中。如果我有输入的文件路径，先将其返回，并在路径首尾加上￥，你的回答就另起一段,并在段首加上@，如果我最新输入的内容不包含文件路径，请正常回复我' 
    messages.append({'role': 'user', 'content': init_messages})
    GPT_reponse(messages, False)
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
        
        # 调用响应函数
        print("ChatYOLO: ", end = "")
        messages = GPT_reponse(messages, 1)
        