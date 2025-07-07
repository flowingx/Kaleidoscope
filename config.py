"""
存储应用程序的所有全局配置常量。
包括屏幕尺寸、布局、文件路径和颜色定义等。
"""
import os
import sys

def get_base_path():
    """
    获取应用程序的根路径，以兼容 PyInstaller 打包后的环境。
    在打包后，资源路径会变为 sys._MEIPASS。
    """
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.abspath(os.path.dirname(__file__))

# 项目的绝对根路径
PROJECT_ROOT = get_base_path()

# --- 屏幕与布局 ---
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
UI_PANEL_WIDTH = 220
LAYER_PANEL_WIDTH = 180
DRAW_AREA_WIDTH = SCREEN_WIDTH - UI_PANEL_WIDTH - LAYER_PANEL_WIDTH
CENTER_X, CENTER_Y = DRAW_AREA_WIDTH // 2, SCREEN_HEIGHT // 2

# --- 性能 ---
FPS = 60
GUIDE_LINE_COLOR = (80, 80, 80)

# --- 文件路径 ---
THEME_PATH = os.path.join(PROJECT_ROOT, 'theme.json')

# 根据运行环境（打包或源码）确定导出目录的父路径
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

EXPORTS_DIR = os.path.join(application_path, 'exports')

# --- 颜色 ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
STATUS_TEXT_COLOR = (255, 255, 0)
PREVIEW_LINE_COLOR = (200, 200, 200)
BACKGROUND_COLOR = (20, 20, 20)
SELECTION_COLOR = (0, 150, 255) # 用于选择框和旋转手柄的颜色