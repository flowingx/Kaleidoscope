"""
应用程序的主入口点。
负责初始化环境、创建应用程序实例并启动主循环。
"""
import os
from modern_app import ModernApp
from config import EXPORTS_DIR

if __name__ == '__main__':
    # 确保用于保存导出文件的 'exports' 目录存在
    if not os.path.exists(EXPORTS_DIR):
        os.makedirs(EXPORTS_DIR)
        
    # 创建应用实例
    app = ModernApp()
    # 启动应用程序的主循环
    app.run()
