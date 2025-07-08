# Updating the export_manager.py file is not necessary for the specified modifications. Instead, I will provide the updated contents for the config.py file and the ui_handler.py file, which are relevant to the changes requested.

# Contents for config.py
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

# 图标路径
BRUSH_ICON_SELECTED = os.path.join(PROJECT_ROOT, 'assets', 'brush_se.svg')
BRUSH_ICON_UNSELECTED = os.path.join(PROJECT_ROOT, 'assets', 'brush_un.svg')
SELECT_ICON_SELECTED = os.path.join(PROJECT_ROOT, 'assets', 'select_se.svg')
SELECT_ICON_UNSELECTED = os.path.join(PROJECT_ROOT, 'assets', 'select_un.svg')
STAR_ICON_SELECTED = os.path.join(PROJECT_ROOT, 'assets', 'star_se.svg')
STAR_ICON_UNSELECTED = os.path.join(PROJECT_ROOT, 'assets', 'star_un.svg')
TRIANGLE_ICON_SELECTED = os.path.join(PROJECT_ROOT, 'assets', 'triangle_se.svg')
TRIANGLE_ICON_UNSELECTED = os.path.join(PROJECT_ROOT, 'assets', 'triangle_un.svg')

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

# Contents for ui_handler.py
"""
负责创建、布局和管理所有的 pygame_gui 界面元素。
将 UI 的创建和逻辑与主应用程序逻辑分离。
"""
from config import DRAW_AREA_WIDTH, UI_PANEL_WIDTH, LAYER_PANEL_WIDTH, SCREEN_HEIGHT, WHITE
import pygame_gui

class UIHandler:
    """管理所有 UI 元素的创建、更新和交互逻辑。"""
    def __init__(self, manager):
        self.manager = manager
        self.elements = {}
        self.spectrum_surface = None
        self._setup_ui()

    def _create_divider(self, y_pos, container, width_offset=30):
        """创建一个可视的分割线 UIPanel。"""
        return pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(5, y_pos, UI_PANEL_WIDTH - width_offset, 2),
            manager=self.manager, container=container, object_id="@divider")

    def _setup_ui(self):
        """初始化并布局所有的 UI 元素。"""
        control_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((DRAW_AREA_WIDTH, 0, UI_PANEL_WIDTH, SCREEN_HEIGHT)),
            manager=self.manager)
        
        y, p, lh, eh, sp = 10, 5, 20, 40, 10
        
        # --- 工具箱 ---
        self.elements['toolbox_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect(10, y, 100, lh), text="Toolbox", manager=self.manager, container=control_panel)
        y += lh
        btn_w = 48
        btn_h = 48  # Fixed square size for buttons
        self.elements['brush_tool_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10, y, btn_w, btn_h), text='', manager=self.manager, container=control_panel, object_id="@tool_button")
        self.elements['select_tool_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10 + btn_w, y, btn_w, btn_h), text='', manager=self.manager, container=control_panel, object_id="@tool_button")
        self.elements['triangle_tool_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10 + btn_w * 2, y, btn_w, btn_h), text='', manager=self.manager, container=control_panel, object_id="@tool_button")
        self.elements['star_tool_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10 + btn_w * 3, y, btn_w, btn_h), text='', manager=self.manager, container=control_panel, object_id="@tool_button")
        
        # Set button icons
        self.elements['brush_tool_btn'].set_image(pygame.image.load(config.BRUSH_ICON_UNSELECTED))
        self.elements['select_tool_btn'].set_image(pygame.image.load(config.SELECT_ICON_UNSELECTED))
        self.elements['triangle_tool_btn'].set_image(pygame.image.load(config.TRIANGLE_ICON_UNSELECTED))
        self.elements['star_tool_btn'].set_image(pygame.image.load(config.STAR_ICON_UNSELECTED))
        
        y += btn_h + sp
        self._create_divider(y - sp / 2, control_panel)

        # --- Slice Count Slider ---
        self.elements['slice_count_slider'] = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(5, y, UI_PANEL_WIDTH - 10, 20),
            start_value=4,
            value_range=(4, 16),
            manager=self.manager,
            container=control_panel
        )
        self.elements['slice_count_slider'].set_value(4)  # Set initial value to 4

    def update_tool_buttons(self, active_tool):
        """更新工具按钮的状态和图标。"""
        for tool in ['brush', 'select', 'triangle', 'star']:
            btn = self.elements[f'{tool}_tool_btn']
            if tool == active_tool:
                btn.set_image(pygame.image.load(config[f'{tool.upper()}_ICON_SELECTED']))
            else:
                btn.set_image(pygame.image.load(config[f'{tool.upper()}_ICON_UNSELECTED']))