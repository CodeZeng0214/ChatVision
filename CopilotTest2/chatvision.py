#!/usr/bin/env python3
"""
ChatVision 主启动脚本
用法: python chatvision.py [--debug]
"""
import sys
import argparse
import logging
from main import main

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="ChatVision - 图像识别聊天机器人")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--log", default="info", choices=["debug", "info", "warning", "error"], 
                        help="日志级别")
    parser.add_argument("--no-gui", action="store_true", help="无GUI模式")
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = {
        "debug": logging.DEBUG,
        "info": logging.INFO, 
        "warning": logging.WARNING,
        "error": logging.ERROR
    }.get(args.log, logging.INFO)
    
    # 启动应用
    try:
        main(debug=args.debug, log_level=log_level, no_gui=args.no_gui)
    except Exception as e:
        print(f"启动失败: {str(e)}", file=sys.stderr)
        sys.exit(1)
