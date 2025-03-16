### Task基类定义
from typing import Dict, Any, Callable, List

class Task:
    def __init__(self, task_name: str, parameters: List[Dict[str, Any]], description: str = ""):
        """参数解释：\n
        - task_name: str 任务名称\n
        - parameters: list 参数列表，参考格式如下：\n
          [{"name": "image_path", "description": "图像路径", "required": True}, ...]\n
          其中required代表是否必需，不必须通常是指存在默认值\n
        - description: str 任务描述\n
        - calltask: fuc 任务实现方法\n
        - result: 任务执行结果\n
        - enable: bool 任务是否启用\n"""
        self.task_name = task_name
        self.parameters = parameters
        self.description = description
        self.calltask = None
        self.result = None
        self.enable = True
    
    def describeTask(self):
        """为任务生成描述"""
        parameter_description = []
        for parameter in self.parameters:
            if parameter.get("required", False):
                parameter_description.append(f"{parameter['name']} (necessary): {parameter['description']}")
            else:
                parameter_description.append(f"{parameter['name']} (unnecessary): {parameter['description']}")
        parameter_description = '\n'.join(parameter_description)
        return f"-- {self.task_name}: {self.description},\nparameters: \n{parameter_description}"