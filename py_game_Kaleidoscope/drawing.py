# filepath: f:\X_code\Projects\25_summer_python\py_game_Kaleidoscope\ui_handler.py
"""
负责创建、布局和管理所有的 pygame_gui 界面元素。
将 UI 的创建和逻辑与主应用程序逻辑分离。
"""
from config import DRAW_AREA_WIDTH, UI_PANEL_WIDTH, LAYER_PANEL_WIDTH, SCREEN_HEIGHT, WHITE, ICON_PATHS, SLICE_COUNT_RANGE, SLICE_COUNT_STEP
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
        
        y, p, lh, eh, sp = 10, 5, 20, 40, 10  # Example values for layout

        # --- 工具箱 ---
        self.elements['toolbox_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect(10, y, 100, lh), text="Toolbox", manager=self.manager, container=control_panel)
        y += lh
        btn_w = 50  # Fixed square size for buttons
        self.elements['brush_tool_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10, y, btn_w, btn_w), text='', manager=self.manager, container=control_panel, object_id="@tool_button")
        self.elements['select_tool_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10 + btn_w + sp, y, btn_w, btn_w), text='', manager=self.manager, container=control_panel, object_id="@tool_button")
        self.elements['triangle_tool_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10 + (btn_w + sp) * 2, y, btn_w, btn_w), text='', manager=self.manager, container=control_panel, object_id="@tool_button")
        self.elements['star_tool_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10 + (btn_w + sp) * 3, y, btn_w, btn_w), text='', manager=self.manager, container=control_panel, object_id="@tool_button")
        
        # Set button icons
        self.update_tool_button_icons()

        y += btn_w + sp
        self._create_divider(y - sp / 2, control_panel)

        # --- 切片数量滑块 ---
        self.elements['slice_slider'] = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(10, y, UI_PANEL_WIDTH - 20, 20),
            start_value=SLICE_COUNT_RANGE[0],
            value_range=(SLICE_COUNT_RANGE[0], SLICE_COUNT_RANGE[1]),
            manager=self.manager,
            container=control_panel
        )

    def update_tool_button_icons(self):
        """更新工具按钮的图标。"""
        for tool, paths in ICON_PATHS.items():
            button = self.elements[f'{tool}_tool_btn']
            if button.selected:
                button.set_image(paths['selected'])
            else:
                button.set_image(paths['unselected'])

    def update_tool_buttons(self, active_tool):
        """更新工具按钮的状态。"""
        for tool in ICON_PATHS.keys():
            self.elements[f'{tool}_tool_btn'].selected = (tool == active_tool)
        self.update_tool_button_icons()

    # ... (其他方法保持不变)