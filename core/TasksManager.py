### 任务管理器

import os
import json
import importlib
import inspect
from typing import Dict, Callable, Any, List
from core.Task import Task
import sys
from core.AuxiliaryFunction import PathCheck

### ========== 任务注册与管理 ========== ###
class TasksManager:
    """
    任务注册管理器：支持动态注册与调用任务。
    """
    def __init__(self):
        self.tasks = {}  # 任务字典，键为任务名称，值为Task对象
        self.tasks_config_path = "tasks/TasksConfigs.json"  # 任务配置的默认路径
        
        # 确保配置文件目录存在
        PathCheck(self.tasks_config_path)
        
        # 尝试从配置文件中加载任务
        try:
            self.load_tasks_from_config(self.tasks_config_path)
        except Exception as e:
            print(f"从配置文件加载任务失败: {e}")
            # 如果加载失败，尝试扫描并创建默认配置
            self._discover_task_classes()
            self.write_tasks_to_config(self.tasks_config_path)
    
    def _discover_task_classes(self):
        """扫描任务模块目录，发现所有Task子类并创建配置项"""
        print("开始扫描任务模块...")
        config = {}
        try:
            # 添加任务目录到Python路径
            task_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tasks')
            if task_dir not in sys.path:
                sys.path.append(task_dir)
            
            # 遍历任务目录下所有.py文件
            for filename in os.listdir(task_dir):
                if filename.endswith(".py") and not filename.startswith("__"):
                    module_name = filename[:-3]  # 去掉.py后缀
                    try:
                        # 导入模块
                        module = importlib.import_module(f"tasks.{module_name}")
                        
                        # 查找模块中的Task子类并收集信息
                        for class_name, obj in inspect.getmembers(module):
                            if (inspect.isclass(obj) and 
                                issubclass(obj, Task) and 
                                obj != Task):  # 排除基类本身
                                try:
                                    # 实例化任务以获取信息
                                    task_instance = obj()
                                    
                                    # 收集配置信息
                                    config[task_instance.task_name] = {
                                        'enable': True,
                                        'module_path': f"tasks.{module_name}",
                                        'class_name': class_name,
                                        'description': task_instance.description,
                                        'parameters': task_instance.parameters
                                    }
                                    
                                    # 注册任务
                                    self.tasks[task_instance.task_name] = task_instance
                                    print(f"发现任务: {task_instance.task_name} ({class_name})")
                                except Exception as e:
                                    print(f"收集任务信息失败 {class_name}: {e}")
                    except Exception as e:
                        print(f"加载模块 {module_name} 失败: {e}")
            
            print(f"扫描完成，共发现 {len(config)} 个任务")
            return config
        except Exception as e:
            print(f"扫描任务类时出错: {e}")
            return {}
    
    def register_task(self, task: Task):
        """注册一个任务实例"""
        self.tasks[task.task_name] = task
    
    def load_tasks_from_config(self, tasks_config_path: str):
        """从配置文件中加载任务"""
        if not os.path.exists(tasks_config_path):
            # 如果配置文件不存在，创建默认配置
            print(f"配置文件 {tasks_config_path} 不存在，将扫描任务并创建配置")
            config = self._discover_task_classes()
            self.write_tasks_to_config(tasks_config_path)
            return
        
        # 从配置文件加载
        print(f"从配置文件加载任务: {tasks_config_path}")
        try:
            with open(tasks_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 清空当前任务，按配置重新加载
            self.tasks.clear()
            
            # 根据配置动态导入和实例化任务
            for task_name, task_config in config.items():
                if task_config.get('enable', True):
                    try:
                        # 从配置获取模块路径和类名
                        module_path = task_config.get('module_path')
                        class_name = task_config.get('class_name')
                        
                        if not module_path or not class_name:
                            print(f"任务配置缺少module_path或class_name: {task_name}")
                            continue
                        
                        # 动态导入模块
                        module = importlib.import_module(module_path)
                        
                        # 获取任务类
                        task_class = getattr(module, class_name)
                        
                        # 实例化任务类
                        task_instance = task_class()
                        
                        # 从配置更新任务属性
                        if 'description' in task_config and task_config['description']:
                            task_instance.description = task_config['description']
                            
                        # 更新参数默认值
                        if 'parameters' in task_config:
                            # 根据名称匹配参数并更新默认值
                            config_params = {param.get('name'): param for param in task_config['parameters'] 
                                            if 'name' in param}
                            
                            for param in task_instance.parameters:
                                param_name = param.get('name')
                                if param_name in config_params:
                                    config_param = config_params[param_name]
                                    # 复制默认值
                                    if 'default' in config_param:
                                        param['default'] = config_param['default']
                        
                        # 注册任务
                        self.register_task(task_instance)
                        print(f"已加载并启用任务: {task_name}")
                    except Exception as e:
                        print(f"加载任务失败 {task_name}: {e}")
                else:
                    print(f"任务已在配置中禁用: {task_name}")
            
            print(f"加载完成，共启用 {len(self.tasks)} 个任务")
        except Exception as e:
            print(f"加载任务配置失败: {e}")
            raise
    
    # 将任务配置写入配置文件
    def write_tasks_to_config(self, tasks_config_path: str = None):
        """将任务配置写入配置文件"""
        if tasks_config_path is None:
            tasks_config_path = self.tasks_config_path
        
        # 确保配置文件目录存在
        os.makedirs(os.path.dirname(tasks_config_path), exist_ok=True)
        
        # 如果没有现有配置文件，创建默认配置
        if not os.path.exists(tasks_config_path):
            # 扫描任务目录以创建初始配置
            config = self._discover_task_classes()
        else:
            # 读取现有配置
            try:
                with open(tasks_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception:
                config = {}
                
            # 更新配置中任务的当前状态
            for task_name, task in self.tasks.items():
                if task_name in config:
                    # 更新现有任务的启用状态
                    config[task_name]['enable'] = task.enable
                else:
                    # 为新任务创建配置项
                    # 从任务实例获取模块和类名信息
                    class_info = task.__class__.__module__
                    class_name = task.__class__.__name__
                    
                    config[task_name] = {
                        'enable': task.enable,
                        'module_path': class_info,
                        'class_name': class_name,
                        'description': task.description,
                        'parameters': task.parameters
                    }
        
        # 写入文件
        try:
            with open(tasks_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            print(f"已将 {len(config)} 个任务配置写入 {tasks_config_path}")
        except Exception as e:
            print(f"写入任务配置失败: {e}")
    
    # 为启用的任务生成描述
    def describeTasks(self) -> str:
        descriptions = []
        for task_name, task in self.tasks.items():
            if task.enable:
                descriptions.append(task.describeTask())
        return "The following are the supported task names and required parameters:\n" + "\n".join(descriptions)
        
    # 获取任务
    def GetTask(self, task_name):
        """获取任务"""
        task = self.tasks.get(task_name)
        if task and task.enable:
            return task
        return None
    
    # 启用/禁用任务
    def toggle_task(self, task_name, enable=None):
        """启用或禁用指定任务"""
        if task_name in self.tasks:
            if enable is not None:
                self.tasks[task_name].enable = enable
            else:
                self.tasks[task_name].enable = not self.tasks[task_name].enable
            return True
        return False
    
    # 保存当前设置
    def save_settings(self):
        """保存当前任务设置到配置文件"""
        self.write_tasks_to_config()



