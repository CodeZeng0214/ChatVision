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
import threading  # 导入threading模块
from time import sleep as wait

### 全局参数
# CHAT_INTER = ChatGPT() # 聊天接口
INIT_MESSAGE = "You are a chatbot capable of image recognition " # 初始化消息
ATT_MAX = 3 # 尝试分析用户意图并转化成json格式的最大次数

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
    plugin_completed = Signal() if HAS_PYSIDE else None  # 插件完成时的信号
    stream_content = Signal(str) if HAS_PYSIDE else None  # 流式内容更新信号

    def __init__(self, chat_inter=ChatGPT(), init_message=INIT_MESSAGE):
        """
        可选参数：\n
        -chat_inter 与语言模型通讯的聊天接口，默认为ChatGPT
        init_message "You are a chatbot capable of image recognition " 初始化消息"
        """
        if HAS_PYSIDE:
            super().__init__()
        
        self.chat_inter = chat_inter
        self.messages = [{"role": "system", "content": init_message}]
        self._analyse_messages = [] # 分析用户意图的消息流
        self.plugin_manager = PluginManager() # 实例化一个插件管理器
        self.current_plugin = None  # 当前处理的插件
        self.current_plugin_params = None  # 当前处理的插件参数
        self.waiting_for_params = False  # 是否等待参数

    def refresh(self):
        """刷新当前处理的插件和参数"""
        self.current_plugin = None
        self.current_plugin_params = None
        self.waiting_for_params = False
        
    def check_plugin(self, plugin_name)->bool:
        """检查插件是否存在"""
        self.current_plugin = self.plugin_manager.get_plugin(plugin_name)
        if not self.current_plugin:
            response = f"未知插件类型：{plugin_name}"
            if HAS_PYSIDE:
                self.response_ready.emit(response)
            return False
        return True

    def check_params(self)->dict:
        """检查插件参数是否完整"""
        required_params = [p for p in self.current_plugin.parameters if p.get("required", False)]
        missing_params = [] # 缺少的参数列表
        
        for param in required_params:
            if param['name'] not in self.current_plugin_params.keys():
                missing_params.append(param) 
        
        # 如果缺少必要参数，通知GUI
        if missing_params:
            self.waiting_for_params = True
 
            if HAS_PYSIDE:
                self.parameters_needed.emit(missing_params)
            missing_message = f"需要提供以下参数：{', '.join([p['name'] for p in missing_params])}"
            print(missing_message)
            
            # 等待参数输入
            while self.waiting_for_params:
                wait(0.3)
                
            # 控制台模式：如果缺少参数，等待参数输入
            if not HAS_PYSIDE:
                for param in missing_params:
                    input_value = input(f"请输入参数值param['name']：")
                    self.current_plugin_params[param['name']] = input_value
            return True
    
    def _AnalyInput(self, user_input):
        """
        使用 大语言模型接口 分析用户输入并提取插件信息。
        """
        # 告知 语言大模型 支持的插件的 提示模板
        plugin_descriptions = self.plugin_manager.describe_plugins()
        template = f"""
        You're a plugin analysis assistant. When a user enters a question, 
        match the most suitable plugin according to the following supported plugins,
        and extract the information to return:
        {plugin_descriptions}
        Only Return format:
        {{
            "plugin_name": <plugin name>,
            "parameters": <parameter dictionary>
        }}
        Hint: 
        1. If the description of the parameter "required" is "False", there is no need to write the returned content. However, if the user enters the corresponding parameter requirements, the return information needs to be written. 
        2. If the user input does not match any of the plugins that can be used, return the string "General". 
        3. If the user intends to use a plugin, but the parameter "required" is "True" is missing, do not write this parameter in the return information.
        
        An example of a user entering correct parameters:
            User enters: "D:\Code\ChatVision\photos\\bus.jpg", what is on this picture, please display on the screen "
            Your answer: {{
                "plugin_name": "ObjectDetect",
                "parameters": {{
                "image_path": "D:\\\\Code\\\\ChatVision\\\\photos\\\\bus.jpg"  
                "is_show": True
                }}
            }}
        An example of insufficient user input parameters:
           User enters: what is on this picture
            Your answer: {{
                "plugin_name": "ObjectDetect",
                "parameters": {{ 
                }}
            }}
        User input is as follows: 
        {user_input}
        """
        message = {"role": "user", "content": template}
        
        self._analyse_messages.clear() # 清空上一次的分析消息流
        self._analyse_messages.append({"role": "system", "content": "You're a plugin extraction assistant."})
        self._analyse_messages.append(message)
        plugin_info = None
        attempt_count = 0 # 尝试分析用户意图并转化成json格式的次数
        while not plugin_info:
            plugin_info = self.chat_inter.UnstreamResponse(self._analyse_messages)
            attempt_count += 1
            if plugin_info == "General": 
                # 如果用户输入匹配不到插件则正常调用聊天接口
                return "General" 
            if attempt_count >= ATT_MAX:
                print("error: 尝试次数超过最大值")
                return "MAX"
            # 格式转化
            try: 
                # print(f"第{attempt_count}次尝试转化用户意图为json格式: {plugin_info}")
                plugin_info = eval(plugin_info)
            except Exception as e:
                error_message = f"第{attempt_count}次尝试转化失败，可能是格式不正确: {e}"
                print(error_message)
                self._analyse_messages.append[{"role": "user", "content": f"These are the questions you need to answer in the format:\n{template}\n"
                                               + f"The following is the message returned after the last processing failure：{plugin_info}"
                                               + f"\nError message: {error_message}"}]
                plugin_info = None
                continue
        return plugin_info
    
    def _stream_callback(self, content):
        """处理流式内容的回调函数"""
        if HAS_PYSIDE:
            self.stream_content.emit(content)
    
    # 主框架
    def ChatFrame(self, question):
        """
        主处理逻辑：从用户输入到插件结果返回。\n
        输入参数，即用户的问题输入
        """
        #print(f"用户: {question}")
        self.messages.append({"role": "user", "content": question})
        try:
            # 使用 语言大模型 分析用户输入意图
            plugin_info = self._AnalyInput(question)
            if plugin_info == "MAX": return "error: 尝试次数超过最大值"
            
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
            current_plugin_name = plugin_info['plugin_name']
            self.current_plugin_params = plugin_info['parameters']
            
            # 检查插件的存在性
            self.check_plugin(current_plugin_name)
            if self.current_plugin == False:
                return f"未知插件类型：{current_plugin_name}" 

            # 检查是否缺少必要参数
            self.check_params()
                
            # 查找并执行插件
            plugin_callable = self.current_plugin.execute
            
            # 通知GUI插件开始处理
            if HAS_PYSIDE:
                self.processing_plugin.emit(f"正在执行{current_plugin_name}插件...")
            
            # 执行插件
            plugin_results = plugin_callable(self.current_plugin_params)
            
            # 通知插件已完成
            if HAS_PYSIDE:
                self.plugin_completed.emit()
            
            # 用 GPT 根据结果生成自然语言回复
            result_summary = f"插件类型：{current_plugin_name}\n插件结果：{plugin_results}"
            response = self.chat_inter.StreamResponse([{"role": "user", "content": result_summary 
                                        + "\n请你根据用户的问题内容，提取或者统计以上插件执行的结果信息来回答用户的问题(全部使用中文)：\n" 
                                        + question}], self._stream_callback if HAS_PYSIDE else None)
            self.messages.append({"role": "assistant", "content": response})
            
            self.refresh() # 刷新当前处理的插件和参数
            
            if HAS_PYSIDE and not response:
                self.response_ready.emit(response)
            return response
        except Exception as e:
            error_message = f"处理消息时发生错误: {e}"
            print(error_message)
            if HAS_PYSIDE:
                self.response_ready.emit(error_message)
            return error_message


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