### 2024.11.17-11.18 
## 此文件定义了各类 ChatCase 用于与语义大模型交流； 定义了ChatRobot 
##            聊天机器人 用于接受、处理用户的信息，完成用户指定的任务，回答用户的问题，

#@@ 待改进的地方
#@ 目前的聊天机器人类的 聊天框架的 case 还只局限于GPTcase，考虑一个通用的聊天框架，不用考虑内部的聊天实例
#@ 一句话多任务支持

from openai import OpenAI
from AuxiliaryFunction import ExtractStrBetween
from ultralytics import YOLO
from transformers import AutoProcessor, Blip2ForConditionalGeneration

BASE_URL = "https://api.chatanywhere.tech/v1" # 默认语义大模型网站
API_KEY = "sk-AencKA6Oy7WnhukWgquDlbis89fhQ5q4Nz8ba4BvYJUjy8LR" # 默认网站密钥
GPT_MODEL = 'gpt-4o-mini' # 默认GPT模型
IOD_WEI_PATH = './/weights//YOLOv8//yolov8m.pt' # 默认的图像检测类任务的权重路径


## GPT类
class ChatGPTCase():
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
    def GPTUnstream(self, messages: list):
        """为提供的对话消息创建新的回答(非流式响应)\n
        messages (list): 完整的对话消息以增强上下文的记忆
        """
        completion = self.chatcase.chat.completions.create(model=self.model, messages=messages)
        response_unstream = completion.choices[0].message.content
        #print(response_unstream)
        return response_unstream
    
        # 流式响应
    
    # 流式响应
    def GPTStream(self, messages: list):
        """为提供的对话消息创建新的回答(流式响应)\n
        messages (list): 完整的对话消息以增强上下文的记忆
        """
        stream = self.chatcase.chat.completions.create(
            model = self.model,
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
    

## 聊天机器人类
class ChatRobot():
    """聊天机器人"""
    
    def __init__(self, init_role="assistant", init_message="你是一个能够进行图像识别的聊天机器人.", init_case=ChatGPTCase()):
        """
        init_role="user" 初始化要求该机器人扮演的角色 默认值 "image recognition assistant."\n
        init_message 初始化信息，告诉ChatRobot扮演的角色 默认值 "You are an image recognition assistant."\n
                    该信息指该聊天机器人的唯一信息列表，不可作为GPT提取信息的中转\n
        init_case 聊天接口实例 默认为GPT的ChatGPTCase()
        """
        self.role = init_role
        self.messages = [{"role": "user", "content": f"{init_message}"}] 
        self.case = init_case # GPT的聊天接口实例
    
    # 聊天框架
    def ChatFrame(self, question: str):
        """
        传入参数：question 用户的问题
        """
        # 先将用户消息加入信息列表
        self.MessagesAdd(question,role='user')
        
        # 分析用户的当前输入，
        extracted_informations = self.AnalyticInput(question) 
        
        # 如果输入不含有识别的倾向，则直接调用GPT的流式响应
        if extracted_informations == 'General':
            self.MessagesAdd(self.case.GPTStream(self.messages))
            return
        
        # 获取任务识别的信息结果 （兼容多目标识别）
        recognition_informations = self.CallIRBot(extracted_informations)
        id = 1
        org_information = ''
        for recognition_information in recognition_informations:
            org_information += f'第{id}张图片的识别结果是：\n{recognition_information}\n'
            id += 1
        # 让GPT根据任务的结果回答用户的问题
        GPT_response = self.case.GPTStream([{'role': 'user', 'content': (org_information+self.HintTemplates('IA')+question)}])
        self.MessagesAdd(GPT_response)
    
    # 将信息添加到当前聊天机器人
    def MessagesAdd(self, message,role=None):
        """将信息添加到当前聊天机器人，不指定role则默认role为self当前属性"""
        if role is None:
            self.messages.append({"role": f"{self.role}", "content": f"{message}"})
        else:
            self.messages.append({"role": f"{role}", "content": f"{message}"})
    
    # 为输入的信息添加提示信息的模板内容
    def HintTemplates(self, option):
        """
        为输入的信息添加提示信息的模板内容\n
        用于与GPT聊天的过程中
        option = 'IE'   用户输入信息提取模板 information extract \n
        option = 'IA' YOLO信息整理模板 information arrangement
        """
        if option == 'Init':
             template = '你是一个能够进行图像识别的聊天机器人'
        elif option == 'IE':
            template = f"我正在利用YOLO等模型进行图像识别任务，我需要你从用户的输入信息提取并按要求返回我信息。\n\
                            可能提取到的信息以及返回的信息格式如下：\n\
                            1.图片或视频路径：例如brid.png、bus.jpg等常见图片或视频格式文件,\
                                返回格式：一个计算机能够读取的路径，请在返回的路径前加上字符串'@OBJ'，在路径末尾加上字符串'&OBJ'\n\
                                    如果用户输入的是文件夹路径，也在返回的路径前加上字符串'@OBJ'，在路径末尾加上字符串'&OBJ'\n\
                                    如果用户输入的内容不包含图片或视频路径，请返回一个字符串'%General%'\n\
                            2.想采用的权重路径：例如yolov8n.pt格式的文件,\n\
                                返回格式：一个计算机能够读取的路径，请在返回的路径前加上字符串'@WEI'，在路径末尾加上字符串'&WEI'\n\
                                    如果用户输入的内容不包含想采用的权重路径，请返回一个字符串'!WEI'\n\
                            3.任务的种类：请理解用户的意图是以下这些种类哪一个,\n\
                                可能属于的种类：图像物体检测，图像物体数数，图像描述.\n\
                                返回格式：如果是 检测图像物体 类任务，请返回字符串'#IOD&TASK',\n\
                                        \n\
                                            \n\
                            以下是用户输入的信息，请你按照以上规则和要求返回信息，'\
                                返回的字符串间请换行：\n"
                                # 如果是 数图像物体个数 类任务，请返回字符串'#IOC&TASK',
        elif option == 'IA':
            template = '\n以上的内容是利用图像识别模型识别用户输入的目标的返回信息，请你根据这些信息回答用户的如下问题,注意不需要完全利用以上内容，且将对象名称翻译为中文，针对性的回复用户提出的问题即可：\n'
        else:
            print("错误不存在该模板,返回空值")
            template = ''
        return template
    
    # 利用聊天实例的接口解析用户输入获取任务的详情
    def AnalyticInput(self, information):
        """
        利用聊天接口初步解析用户输入\n
        从中提取图像路径、任务类型等信息。\n
        输入：\n  
        information : 用户输入的信息\n
        role: 默认为当前聊天机器人的role\n
        输出：\n
        Extracted_information 存储了图像/视频路径 target_path、任务类型 task_type、使用权重 weight_path 的字典，\n
                            如果无提取到的信息则为空
        """
        
        # 调用GPT进行预处理 
        unprocessed_information  = [{'role': 'user', 'content': self.HintTemplates('IE')+information}]
        processed_information = self.case.GPTUnstream(unprocessed_information)
        
        # 如果提取的字符串含General，表明用户输入是与GPT正常聊天
        isGeneral = ExtractStrBetween('%', '%', processed_information)
        if isGeneral and isGeneral[0] == 'General' : return 'General'
        
        # 提取的信息
        extracted_informations = {'target_path':ExtractStrBetween('@OBJ', '&OBJ', processed_information), 
                                  'task_type': ExtractStrBetween('#','&TASK', processed_information), 
                                  'weight_path': ExtractStrBetween('@WEI','&WEI', processed_information)}
        return extracted_informations
    
    # 调用 图像识别机器人 完成任务
    def CallIRBot(self, extracted_informations=None):
        if extracted_informations is None: return
        ir_robot = ImgRecRobot()
        recognition_informations = ir_robot.RecognitionFrame(extracted_informations)
        return recognition_informations
          
    # 清空当前机器人消息记录
    def ResetMessages(self):
        """
        重置对话历史，清空消息记录。
        """
        self.messages = []
        

## 图像识别机器人的类
class ImgRecRobot:
    def __init__(self):
        self.id = 1
    
    # 针对不同识别任务的具体框架调用方法
    def RecognitionFrame(self, extracted_informations):
        
        # 从信息列表中提却信息，并检查是否为空
        target_path = extracted_informations['target_path']
        task_type = extracted_informations['task_type']
        weight_path = extracted_informations['weight_path']
        if task_type: task_type = task_type[0]
        if target_path: target_path = target_path[0]

        
        # 判断任务类型
        if task_type == 'IOD':
            if weight_path: weight = weight_path[0]
            else: weight = IOD_WEI_PATH
            recognition_result = self.YOLODetect(target_path, weight)
        else: 
            recognition_result = "图像识别任务处理失败"
            print("图像识别任务处理失败")
        return recognition_result
        
    # 利用YOLO完成图像识别类任务
    def YOLODetect(self, target_path, weight=IOD_WEI_PATH,is_save=False, is_show=False):
        print("正在使用YOLO执行图像识别任务")
        model = YOLO(weight)
        results = model.predict(source=target_path, save=is_save, save_txt=False,  verbose=False)
        print("检测完成")
        recognition_results = []
        for result in results:
            # result是一个检测结果对象，通常包含边界框、标签、置信度等信息
            recognition_result = ''
            for detection in result.boxes:  # 访问每个检测的框
            # 提取边界框坐标、置信度和标签
                x1, y1, x2, y2 = detection.xyxy[0]  # 左上角和右下角坐标
                conf = detection.conf[0]  # 置信度
                conf = 100*conf
                cls = int(detection.cls[0])  # 类别索引
                label = model.names[cls]  # 获取类别名称
                recognition_result += f"检测到有{conf:.2f}%置信度的 {label} 对象\n"
            if is_show: result.show()
            recognition_results.append(recognition_result)
        return recognition_results


## 调试主程序
if __name__ == '__main__':

    chat_robot = ChatRobot()
    
    print("开始对话（输入'退出'以结束）：")
    while True:
        user_input = input("你: ")
        if user_input.lower() == '退出':
            break
        print("ChatYOLO:", end="")
        chat_robot.ChatFrame(question=user_input)