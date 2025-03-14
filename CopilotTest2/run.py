#!/usr/bin/env python3
"""
ChatVision 启动脚本
"""
import os
import sys
import subprocess

def main():
    """启动主应用"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.join(script_dir, "main.py")
    
    if not os.path.exists(main_py):
        print(f"错误: 找不到主程序文件 {main_py}", file=sys.stderr)
        sys.exit(1)
    
    # 检查必要的包
    required_packages = [
        "PySide6", "opencv-python", "requests", "numpy"
    ]
    
    missing_packages = []
    for pkg in required_packages:
        try:
            __import__(pkg.split("-")[0])  # 尝试导入包
        except ImportError:
            missing_packages.append(pkg)
    
    # 如果有缺失的包，提示安装
    if missing_packages:
        print("以下必需的Python包未安装:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        
        install_choice = input("是否自动安装这些包? (y/n): ").strip().lower()
        if install_choice == 'y':
            print("安装必要的包...")
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
        else:
            print("请手动安装必要的包后再运行程序")
            sys.exit(1)
    
    # 启动主程序
    print("启动 ChatVision...")
    sys.exit(subprocess.call([sys.executable, main_py]))

if __name__ == "__main__":
    main()
