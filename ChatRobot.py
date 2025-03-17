### 大修改
### 2024.11.18 创建主函数，调用其他模块完成对话
### 2024.11.23 基于CodeCopilot进行代码重构，代码汇总至这一个文件
### 2024.11.26 代码框架分散化，提高可维护性
### 2025.03.14 添加GUI支持和参数交互能力
### 2025.03.15 添加多线程支持，避免界面卡顿

### ========== 导入辅助模块 ========== ###
from core.ChatInter import ChatGPT # 导入ChatGPT聊天接口
from core.PluginManager import PluginManager # 导入插件管理器
from core.Plugin import Plugin # 导入插件基类
import threading  # 确保导入threading模块

# 条件导入PySide6，当此脚本不是启动脚本时导入
if __name__ != '__main__':
    from PySide6.QtCore import QObject, Signal
    HAS_PYSIDE = True
else:
    ## 此脚本作为调试脚本debug时，不导入PySide6
    HAS_PYSIDE = False
    # 在调试的时候，创建一个简单的替代类
    class QObject: pass
    class Signal:
        def __init__(self, *args): pass
        def emit(self, *args): pass

    
### ========== 聊天机器人类 ========== ###
class ChatRobot(QObject):
    # 定义信号
    response_ready = Signal(str) if HAS_PYSIDE else None  # 回复准备好时的信号
    parameters_needed = Signal(list) if HAS_PYSIDE else None  # 需要参数时的信号
    processing_plugin = Signal(str) if HAS_PYSIDE else None  # 处理插件时的信号
    plugin_completed = Signal(str, str) if HAS_PYSIDE else None  # 插件完成时的信号
    stream_content = Signal(str) if HAS_PYSIDE else None  # 流式内容更新信号

    def __init__(self, chat_inter=ChatGPT(), init_message="你是一个能够进行图像识别的聊天机器人."):
        """
        可选参数：\n
        -chat_inter 与语言模型通讯的聊天接口，默认为ChatGPT
        init_message 初始化内容，默认"你是一个能够进行图像识别的聊天机器人."
        """
        if HAS_PYSIDE:
            super().__init__()
        
        self.chat_inter = chat_inter
        self.messages = [{"role": "system", "content": init_message}]
        self.plugin_manager = PluginManager() # 实例化一个插件管理器
        self.current_plugin = None  # 当前处理的插件
        self.waiting_for_params = False  # 是否等待参数


    # 主框架
    def ChatFrame(self, question):
        """
        主处理逻辑：从用户输入到插件结果返回。\n
        输入参数，即用户的问题输入
        """
        try:
            #print(f"用户: {question}")
            self.messages.append({"role": "user", "content": question})

            # 告知 语言大模型 支持的插件的 提示模板
            plugin_descriptions = self.plugin_manager.describePlugins()

            # 使用 语言大模型 分析用户输入意图
            plugin_info = self._AnalyInput(question, plugin_descriptions)
            
            # 如果用户输入匹配不到插件则正常调用聊天接口
            if plugin_info == "General": 
                if HAS_PYSIDE:
                    self.processing_plugin.emit("正在思考...")
                # 使用回调函数处理流式内容
                response = self.chat_inter.StreamResponse(self.messages, 
                                                         self._stream_callback if HAS_PYSIDE else None)
                self.messages.append({"role": "assistant", "content": response})
                return response
                
            # 获取插件名称和参数
            plugin_type = plugin_info['plugin_type']
            plugin_params = plugin_info['parameters']
            
            # 检查是否缺少必要参数
            plugin = self.plugin_manager.GetPlugin(plugin_type)
            if not plugin:
                response = f"未知插件类型：{plugin_type}"
                if HAS_PYSIDE:
                    self.response_ready.emit(response)
                return response
                
            required_params = [p for p in plugin.parameters if p.get("required", False)]
            missing_params = []
            
            for param in required_params:
                if param["name"] not in plugin_params:
                    missing_params.append(param)
            
            # 如果缺少必要参数，通知GUI
            if missing_params:
                self.current_plugin = plugin_type
                self.waiting_for_params = True
                if HAS_PYSIDE:
                    self.parameters_needed.emit(required_params)
                missing_message = f"需要提供以下参数：{', '.join([p['name'] for p in missing_params])}"
                print(missing_message)
                return missing_message
                
            # 查找并执行插件
            plugin_callable = plugin.execute
            
            # 通知GUI插件开始处理
            if HAS_PYSIDE:
                self.processing_plugin.emit(f"正在执行{plugin_type}插件...")
            
            # 执行插件
            plugin_results = plugin_callable(plugin_params)
            
            # 通知插件已完成
            if "image_path" in plugin_params and HAS_PYSIDE:
                self.plugin_completed.emit(plugin_type, plugin_params["image_path"])
            
            # 用 GPT 根据结果生成自然语言回复
            result_summary = f"插件类型：{plugin_type}\n插件结果：{plugin_results}"
            response = self.chat_inter.StreamResponse([{"role": "user", "content": result_summary 
                                        + "\n请你根据用户的问题内容，提取或者统计以上插件执行的结果信息来回答用户的问题(全部使用中文)：\n" 
                                        + question}], self._stream_callback if HAS_PYSIDE else None)
            self.messages.append({"role": "assistant", "content": response})
            if HAS_PYSIDE:
                self.response_ready.emit(response)
            return response
        except Exception as e:
            error_message = f"处理消息时发生错误: {e}"
            print(error_message)
            if HAS_PYSIDE:
                self.response_ready.emit(error_message)
            return error_message

    def _AnalyInput(self, user_input, plugin_descriptions):
        """
        使用 大语言模型接口 分析用户输入并提取插件信息。
        """
        template = f"""
        You're a plugin analysis assistant. When a user enters a question, 
        match the most suitable plugin according to the following supported plugins,
        and extract the information to return:
        {plugin_descriptions}
        Only Return format:
        {{
            "plugin_type": <plugin type>,
            "parameters": <parameter dictionary>
        }}
        Hint: 
        1. If the description of the parameter "required" is "False", there is no need to write the returned content. However, if the user enters the corresponding parameter requirements, the return information needs to be written. 
        2. If the user input does not match any of the plugins that can be used, return the string "General". 
        3. If the user intends to use a plugin, but the parameter "required" is "True" is missing, do not write this parameter in the return information.
        
        An example of a user entering correct parameters:
            User enters: "D:\Code\ChatVision\photos\\bus.jpg", what is on this picture"
            Your answer: {{
                "plugin_type": "ObjectDetect",
                "parameters": {{
                "image_path": "D:\\\\Code\\\\ChatVision\\\\photos\\\\bus.jpg"  
                }}
            }}
        An example of insufficient user input parameters:
           User enters: what is on this picture
            Your answer: {{
                "plugin_type": "ObjectDetect",
                "parameters": {{ 
                }}
            }}
        User input is as follows: 
        {user_input}
        """
        messages = [{"role": "system", "content": "You're a plugin extraction assistant."},
                    {"role": "user", "content": template}]
        plugin_info = self.chat_inter.UnstreamResponse(messages)
        
        # print(plugin_info)
        if plugin_info == "General" : return "General"
        
        # 格式转化
        try: 
            plugin_info = eval(plugin_info)
            # 兼容旧版本返回格式（task_type -> plugin_type）
            if "task_type" in plugin_info and "plugin_type" not in plugin_info:
                plugin_info["plugin_type"] = plugin_info.pop("task_type")
        except Exception as e:
            print(f"返回的内容格式不正确: {e}")
            return "General"
        else:
            return plugin_info
    
    def _stream_callback(self, content):
        """处理流式内容的回调函数"""
        if HAS_PYSIDE:
            self.stream_content.emit(content)
    
    def set_parameters(self, parameters):
        """设置参数并继续执行插件"""
        if not self.waiting_for_params or not self.current_plugin:
            return False
            
        plugin = self.plugin_manager.GetPlugin(self.current_plugin)
        if not plugin:
            return False
            
        # 通知GUI插件开始处理
        if HAS_PYSIDE:
            self.processing_plugin.emit(f"正在执行{self.current_plugin}插件...")
        
        # 保存当前状态供线程使用
        current_plugin = self.current_plugin
        last_question = self.messages[-1]["content"] if self.messages else ""
        
        # 重置状态，避免重复触发处理
        self.waiting_for_params = False
        self.current_plugin = None
        
        # 在新线程中执行插件
        threading.Thread(
            target=self._execute_plugin_in_thread, 
            args=(plugin, parameters, current_plugin, last_question),
            daemon=True
        ).start()
        
        return True

    def _execute_plugin_in_thread(self, plugin, parameters, plugin_name, last_question):
        """在新线程中执行插件处理"""
        try:
            # 执行插件
            plugin_results = plugin.execute(parameters)
            
            # 通知插件已完成
            if "image_path" in parameters and HAS_PYSIDE:
                self.plugin_completed.emit(plugin_name, parameters["image_path"])
            
            # 用 GPT 根据结果生成自然语言回复
            result_summary = f"插件类型：{plugin_name}\n插件结果：{plugin_results}"
            response = self.chat_inter.StreamResponse([{"role": "user", "content": result_summary 
                                    + "\n请你根据用户的问题内容，提取或者统计以上插件执行的结果信息来回答用户的问题(全部使用中文)：\n" 
                                    + last_question}], self._stream_callback if HAS_PYSIDE else None)
            
            self.messages.append({"role": "assistant", "content": response})
            if HAS_PYSIDE:
                self.response_ready.emit(response)
        except Exception as e:
            error_message = f"处理插件参数时发生错误: {e}"
            print(error_message)
            if HAS_PYSIDE:
                self.response_ready.emit(error_message)

    
if __name__ == '__main__':
        
    chat_robot = ChatRobot()
    
    print("开始对话（输入'exit'或'q'以结束）：")
    while True:
        user_input = input("你: ")
        if user_input.lower() == 'exit' or user_input.lower() == 'q':
            break
        print("ChatCV:", end='')
        chat_robot.ChatFrame(question=user_input)
        print('')