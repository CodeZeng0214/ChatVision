### 2024.11.19
## 此文件用于定义一些常用辅助函数

import re
import os


# 提取取两个指定字符串之间的内容
def ExtractStrBetween(start_str, end_str, text):
    """
    提取两个指定字符串之间的内容。\n
    
    参数:\n
    start_str (str): 起始字符串\n
    end_str (str): 结束字符串\n
    text (str): 目标文本\n

    返回:\n
    list: 提取的内容列表
    """
    # 使用正则表达式来提取两个指定字符串之间的内容
    pattern = re.compile(f'(?<={re.escape(start_str)})(.*?)(?={re.escape(end_str)})', re.DOTALL)

    # 查找所有匹配的内容
    matches = pattern.findall(text)
    
    # 处理空格问题
    promatches = []
    for match in matches:
        promatches.append(re.sub("\s", "", match))
    return promatches

# 如果路径不存在则自动创建
def PathCheck(file_path):
    """
    如果路径不存在则自动创建
    """
    dir_path = os.path.dirname(file_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return file_path
