### 2024.11.18 创建主函数，调用其他模块完成对话
### 2024.11.23 基于CodeCopilot进行代码重构
## 此文件为最新的ChatYOLO详细实现，目前的状态是代码汇总至这一个文件

from openai import OpenAI
from typing import Dict, Callable, Any
from ultralytics import YOLO


### ========== 全局参数 ========== ###
BASE_URL = "https://api.chatanywhere.tech/v1" # 默认语义大模型网站
API_KEY = "sk-AencKA6Oy7WnhukWgquDlbis89fhQ5q4Nz8ba4BvYJUjy8LR" # 默认网站密钥
GPT_MODEL = 'gpt-4o-mini' # 默认GPT模型
DET_WEI_PATH = './/weights//YOLO_World//yolov8s-worldv2.pt' # 默认的图像检测类任务的权重路径
TRA_WEI_PATH = ".//weights//YOLO11//yolo11s-pose.pt" # 默认的图像跟踪类任务的权重路径


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
    def StreamResponse(self, messages: list):
        """为提供的对话消息创建新的回答(流式响应)\n
        messages (list): 完整的对话消息以增强上下文的记忆
        """
        print(messages[0]['content'])
        stream = self.chatcase.chat.completions.create(
            model = self.model,
            messages = messages,
            stream = True,
        )
        response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                response += chunk.choices[0].delta.content
                print(chunk.choices[0].delta.content, end = "")
        print("\n")
        return response
    

### ========== 任务注册与管理 ========== ###
class TaskManager:
    """
    任务注册管理器：支持动态注册与调用任务。
    """
    def __init__(self):
        self.tasks = {}

    # 注册任务
    def register_task(self, task_name: str, task_callable: Callable, description: str, parameters: list):
        """
        注册任务。\n
        - task_name: 任务名称(交给语言模型读取的)\n
        - task_callable: 任务的实现方法（调用哪个函数）\n
        - description: 任务描述\n
        - parameters: 参数需求列表，格式如下：\n
          [{"name": "image_path", "description": "建议英文", required": True}]\n
          其中required代表是否必需，不必须通常是指存在默认路径
        """
        self.tasks[task_name] = {
            "callable": task_callable,
            "description": description,
            "parameters": parameters,
        }
    
    # 为注册的任务生成描述
    def DescribeTasks(self) -> str:
        descriptions = []
        for name, task in self.tasks.items():
            parameter_strings = []
            for parameter in task["parameters"]:
                if parameter["required"]:
                    parameter_strings.append(f"{parameter['name']} (necessary): {parameter['description']}")
                else:
                    parameter_strings.append(f"{parameter['name']} (unnecessary): {parameter['description']}")

            parameter_description = '\n'.join(parameter_strings)

            description = f"-- {name}: {task['description']},\nparameters: \n{parameter_description}"
            descriptions.append(description)
            # print("以下是支持的任务名称及所需参数:\n" + "\n".join(descriptions))
        return "以下是支持的任务名称及所需参数:\n" + "\n".join(descriptions)
        
    # 获取任务并实现
    def GetTask(self, task_name):
        """获取任务实现"""
        return self.tasks.get(task_name)
    
    
    
### ========== 可实现的任务列表 ========== ###
# 图像物体识别（YOLO）
def ObjDetect(params):
    """
    物体检测任务实现。\n
    参数：{'image_path': str, 'weight_path': str (可选), 'is_show': bool (可选)}\n
    """
    image_path = params['image_path']
    weight_path = params.get('weight_path', DET_WEI_PATH)
    is_show = params.get('is_show', False)

    # 加载 YOLO 模型
    model = YOLO(weight_path)
    results = model.predict(source=image_path, save=False, verbose=False)

    # 格式化结果
    detection_results = []
    for result in results:
        # result是一个检测结果对象，通常包含边界框、标签、置信度等信息
        detection_result = ''
        for box in result.boxes:  # 访问每个检测的框
        # 提取边界框坐标、置信度和标签
            x1, y1, x2, y2 = box.xyxy[0]  # 左上角和右下角坐标
            conf = box.conf[0]  # 置信度
            conf = 100*conf
            cls = int(box.cls[0])  # 类别索引
            label = model.names[cls]  # 获取类别名称
            detection_result += f"检测到有{conf:.2f}%置信度的 {label} 对象\n"
        if is_show: result.show()
        detection_results.append(detection_result)
    return detection_results


# 人体姿态跟踪（YOLO）
def HummanPoseTrack(params):
    """
    人体姿态跟踪任务实现。\n
    参数：{'image_path': str, 'weight_path': str (可选), 'is_show': bool (可选)}\n
    """
    image_path = params['image_path']
    weight_path = params.get('weight_path', TRA_WEI_PATH)
    is_show = params.get('is_show', False)
    
    model = YOLO(weight_path)
    
    results = model.track(source=image_path, show=is_show, stream=True)
    if results : return("已经显示于屏幕上")
    
    

#图像描述
def ImgDescription(params):
# pip install accelerate
    import requests
    from PIL import Image
    from transformers import Blip2Processor, Blip2ForConditionalGeneration

    processor = Blip2Processor.from_pretrained("Salesforce/blip2-opt-2.7b")
    # model = Blip2ForConditionalGeneration.from_pretrained("Salesforce/blip2-opt-2.7b", device_map="auto")
    model = Blip2ForConditionalGeneration.from_pretrained("Salesforce/blip2-opt-2.7b")

    img_url = 'https://storage.googleapis.com/sfr-vision-language-research/BLIP/demo.jpg' 
    raw_image = Image.open(requests.get(img_url, stream=True).raw).convert('RGB')

    question = "how many dogs are in the picture?"
    inputs = processor(raw_image, question, return_tensors="pt").to("cuda")

    out = model.generate(**inputs)
    print(processor.decode(out[0], skip_special_tokens=True).strip())

    return 1
    

### ========== 聊天机器人类 ========== ###
class ChatRobot:
    def __init__(self, chat_inter=ChatGPT(), init_message="你是一个能够进行图像识别的聊天机器人."):
        """
        可选参数：\n
        -chat_inter 与语言模型通讯的聊天接口，默认为ChatGPT
        init_message 初始化内容，默认"你是一个能够进行图像识别的聊天机器人."
        """
        self.chat_inter = ChatGPT()
        self.messages = [{"role": "system", "content": init_message}]
        self.task_manager = TaskManager() # 实例化一个任务管理器
        self._RegisterTasks()

    def _RegisterTasks(self):
        """注册任务"""
        self.task_manager.register_task(
            "ObjectDetect",
            ObjDetect,
            "Detect objects in the image",
             [{"name": "image_path", "description": "A task object is moved to a file path in image or video format","required": True}, 
             {"name": "weight_path", "description": "The weight that the user specifies when the task is performed", "required": False},
             {"name": "is_show", "description": "Whether it needs to be displayed on screen, return True or False", "required": False}]
        )
        self.task_manager.register_task(
            "HumanPoseTrack", 
            HummanPoseTrack, 
            "Track and estimate human posture",
             [{"name": "image_path", "description": "A task object is moved to a file path in image or video format","required": True}, 
             {"name": "weight_path", "description": "The weight that the user specifies when the task is performed", "required": False}, 
             {"name": "is_show", "description": "Whether it needs to be displayed on screen, return True or False", "required": False}]
        )

    # 主框架
    def ChatFrame(self, question):
        """
        主处理逻辑：从用户输入到任务结果返回。\n
        输入参数，即用户的问题输入
        """
        self.messages.append({"role": "user", "content": question})

        # 告知 语言大模型 支持的任务的 提示模板
        task_descriptions = self.task_manager.DescribeTasks()

        # 使用 语言大模型 分析用户输入意图
        task_info = self._AnalyInput(question, task_descriptions)

        # 获取任务名称和参数
        task_type = task_info['task_type']
        task_params = task_info['parameters']

        # 查找并执行任务
        task_callable = self.task_manager.GetTask(task_type)
        if not task_callable:
            return f"未知任务类型：{task_type}"

        # 执行任务
        task_results = task_callable["callable"](task_params)

        # 用 GPT 根据结果生成自然语言回复
        result_summary = f"任务类型：{task_type}\n任务结果：{task_results}"
        response = self.chat_inter.StreamResponse([{"role": "user", "content": result_summary 
                                        + "\n请你根据用户的问题内容，提取以上任务执行的结果信息来回答用户的问题：\n" 
                                        + question}])
        self.messages.append({"role": "assistant", "content": response})
        return response

    def _AnalyInput(self, user_input, task_descriptions):
        """
        使用 大语言模型接口 分析用户输入并提取任务信息。
        """
        template = f"""
        你是一个任务分析助手。用户输入任务时，请根据以下支持的任务类型与参数提取信息：
        {task_descriptions}
        返回格式：
        {{
            "task_type": <任务类型>,
            "parameters": <参数字典>
        }}
        注意事项：1.若参数后缀为unnecessary，且用户没有输入有关该参数的信息，则不必写入返回内容，
        用户输入如下：
        {user_input}
        """
        messages = [{"role": "system", "content": "你是一个任务信息提取助手。"},
                    {"role": "user", "content": template}]
        task_info = self.chat_inter.UnstreamResponse(messages)
        return eval(task_info)  # 假设 GPT 返回 Python 字典格式

    

if __name__ == '__main__':

    chat_robot = ChatRobot()
    
    print("开始对话（输入'退出'或'q'以结束）：")
    while True:
        user_input = input("你: ")
        if user_input.lower() == 'q':
            break
        #print("ChatYOLO:")
        chat_robot.ChatFrame(question=user_input)