### 大修改
### 2024.11.18 创建主函数，调用其他模块完成对话
### 2024.11.23 基于CodeCopilot进行代码重构，代码汇总至这一个文件
### 2024.11.26 代码框架分散化，提高可维护性

#@ 待解决的问题： 如何确保一个新加的模块的库的安装准确
#@ 待解决的问题： 如何让ChatGPT记忆上次任务的结果并认为是自己完成了任务


### ========== 导入辅助模块 ========== ###
from ChatInter import ChatGPT # 导入ChatGPT聊天接口
from TasksManager import TasksManager # 导入任务管理器

### ========== 导入任务模块 ========== ###
from modules.YOLOTasks import ObjDetect, HummanPoseTrack  # YOLO 图像检测和人类姿态估计模块 ObjDetect HummanPoseTrack
from modules.YOLODeepsort.YOLO_Deepsort import PedCarTrack # 行人车辆跟踪模块 PedCarTrack
from modules.BLIPTasks import ImgDescription
    
    

### ========== 聊天机器人类 ========== ###
class ChatRobot:
    def __init__(self, chat_inter=ChatGPT(), init_message="你是一个能够进行图像识别的聊天机器人."):
        """
        可选参数：\n
        -chat_inter 与语言模型通讯的聊天接口，默认为ChatGPT
        init_message 初始化内容，默认"你是一个能够进行图像识别的聊天机器人."
        """
        self.chat_inter = chat_inter
        self.messages = [{"role": "system", "content": init_message}]
        self.task_manager = TasksManager() # 实例化一个任务管理器
        self._RegisterTasks()

    def _RegisterTasks(self):
        """注册任务"""
        self.task_manager.register_task(
            "ObjectDetect",
            ObjDetect,
            "Detect objects or humans in the image, can count",
             [{"name": "image_path", "description": "A task object is moved to a file path in image or video format","required": True}, 
             {"name": "weight_path", "description": "The weight that the user specifies when the task is performed", "required": False},
             {"name": "is_show", "description": "Whether it needs to be displayed on screen, return a boolean value without quotation marks: True or False(capitalize the first letter)", "required": False}]
        )
        self.task_manager.register_task(
            "HumanPoseEstimate", 
            HummanPoseTrack, 
            "Can only estimate human posture, not count",
             [{"name": "image_path", "description": "A task object is moved to a file path in image or video format","required": True}, 
             {"name": "weight_path", "description": "The weight that the user specifies when the task is performed", "required": False}, 
             {"name": "is_show", "description": "Whether it needs to be displayed on screen, return a boolean value without quotation marks: True or False(capitalize the first letter)", "required": False}]
        )
        self.task_manager.register_task(
            "Pedestrian and Vehicle tracking", 
            PedCarTrack, 
            "Track pedestrians and vehicles",
             [{"name": "image_path", "description": "A task object is moved to a file path in image or video format","required": True}, 
             {"name": "weight_path", "description": "The weight that the user specifies when the task is performed", "required": False},
            {"name": "save_path", "description": "Storage path of the task result file", "required": False}]
        )
        self.task_manager.register_task(
            "Image Description", 
            ImgDescription, 
            "Can describe the image in one sentence",
             [{"name": "image_path", "description": "A task object is moved to a file path in image or video format","required": True}, 
             {"name": "weight_path", "description": "The weight that the user specifies when the task is performed", "required": False}]
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
        
        # 如果用户输入匹配不到任务则正常调用聊天接口
        if task_info == "General": 
            response = self.chat_inter.StreamResponse(self.messages)
            self.messages.append({"role": "assistant", "content": response})
            return response
            
            
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
                                        + "\n请你根据用户的问题内容，提取或者统计以上任务执行的结果信息来回答用户的问题(全部使用中文)：\n" 
                                        + question}])
        self.messages.append({"role": "assistant", "content": response})
        return response

    def _AnalyInput(self, user_input, task_descriptions):
        """
        使用 大语言模型接口 分析用户输入并提取任务信息。
        """
        template = f"""
        You're a task analysis assistant.  When a user enters a task, 
        match the most suitable task according to the following supported task types, 
        and extract the information to return: ：
        {task_descriptions}
        Only Return format:
        {{
            "task_type": <task type>,
            "parameters": <parameter dictionary>
        }}
        Precautions: 1. If the suffix unnecessary for a parameter is unnecessary and no information about the parameter is entered, it is unnecessary to write the returned content. 
        User input is as follows:
        2.If the user input does not match the task, please return with the string 'General' 
        {user_input}
        """
        messages = [{"role": "system", "content": "You're a task extraction assistant."},
                    {"role": "user", "content": template}]
        task_info = self.chat_inter.UnstreamResponse(messages)
        
        # print(task_info)
        if task_info == "General" : return "General"
        
        # 格式转化
        try: 
            task_info = eval(task_info)
        except Exception as e:
            print(task_info)
            input("返回的内容格式不正确，输入任意内容继续：")
        else:
            return task_info  # 假设 GPT 返回 Python 字典格式

    
if __name__ == '__main__':

    chat_robot = ChatRobot()
    
    print("开始对话（输入'退出'或'q'以结束）：")
    while True:
        user_input = input("你: ")
        if user_input.lower() == '退出' or user_input.lower() == 'q':
            break
        print("ChatIR:", end='')
        chat_robot.ChatFrame(question=user_input)
        print('')