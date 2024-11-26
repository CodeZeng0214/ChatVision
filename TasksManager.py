### 任务管理器

from typing import Dict, Callable, Any

### ========== 任务注册与管理 ========== ###
class TasksManager:
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
        # print("The following are the supported task names and required parameters:\n" + "\n".join(descriptions))
        return "The following are the supported task names and required parameters:\n" + "\n".join(descriptions)
        
    # 获取任务并实现
    def GetTask(self, task_name):
        """获取任务实现"""
        return self.tasks.get(task_name)