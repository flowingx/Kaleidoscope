# filepath: f:\X_code\Projects\25_summer_python\py_game_Kaleidoscope\ui_handler.py
"""
负责创建、布局和管理所有的 pygame_gui 界面元素。
将 UI 的创建和逻辑与主应用程序逻辑分离。
"""
from config import DRAW_AREA_WIDTH, UI_PANEL_WIDTH, LAYER_PANEL_WIDTH, SCREEN_HEIGHT, WHITE, ICONS_PATH
import pygame_gui
import pygame

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
        
        btn_size = 48
        self.elements['brush_tool_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10, y, btn_size, btn_size), 
                                                                       text='', 
                                                                       manager=self.manager, 
                                                                       container=control_panel, 
                                                                       object_id="@tool_button")
        self.elements['brush_tool_btn'].set_image(ICONS_PATH['brush_un'])
        
        self.elements['select_tool_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10 + btn_size, y, btn_size, btn_size), 
                                                                        text='', 
                                                                        manager=self.manager, 
                                                                        container=control_panel, 
                                                                        object_id="@tool_button")
        self.elements['select_tool_btn'].set_image(ICONS_PATH['select_un'])
        
        self.elements['triangle_tool_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10 + btn_size * 2, y, btn_size, btn_size), 
                                                                          text='', 
                                                                          manager=self.manager, 
                                                                          container=control_panel, 
                                                                          object_id="@tool_button")
        self.elements['triangle_tool_btn'].set_image(ICONS_PATH['triangle_un'])
        
        self.elements['star_tool_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10 + btn_size * 3, y, btn_size, btn_size), 
                                                                      text='', 
                                                                      manager=self.manager, 
                                                                      container=control_panel, 
                                                                      object_id="@tool_button")
        self.elements['star_tool_btn'].set_image(ICONS_PATH['star_un'])
        
        y += btn_size + sp
        self._create_divider(y - sp / 2, control_panel)

        # --- 切片数量滑块 ---
        self.elements['slice_slider'] = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(5, y, UI_PANEL_WIDTH - 10, 20), 
                                                                               start_value=4, 
                                                                               value_range=(4, 16), 
                                                                               manager=self.manager, 
                                                                               container=control_panel)
        self.elements['slice_slider'].set_step(2)  # Only allow even numbers

    def update_tool_buttons(self, active_tool):
        """更新工具按钮的状态和图标。"""
        for tool in ['brush', 'select', 'triangle', 'star']:
            btn = self.elements[f'{tool}_tool_btn']
            if tool == active_tool:
                btn.set_image(ICONS_PATH[f'{tool}_se'])
            else:
                btn.set_image(ICONS_PATH[f'{tool}_un'])

    def show_shape_properties(self, shape):
        pass

    def show_brush_properties(self):
        pass

    def hide_all_tool_properties(self):
        pass

    def draw_custom_ui(self, surface, start_color, end_color, active_color_selection, brush_size):
        pass

    def handle_color_picker_click(self, event_pos):
        pass