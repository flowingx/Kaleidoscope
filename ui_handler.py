"""
负责创建、布局和管理所有的 pygame_gui 界面元素。
将 UI 的创建和逻辑与主应用程序逻辑分离。
"""
import pygame
import pygame_gui
from config import (DRAW_AREA_WIDTH, UI_PANEL_WIDTH, LAYER_PANEL_WIDTH, 
                    SCREEN_HEIGHT, WHITE, TOOL_BUTTON_SIZE, ICONS)
import utils

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
        
        y, p, lh, eh, sp = 10, 5, 20, 30, 15
        
        # --- 工具箱 ---
        self.elements['toolbox_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect(10, y, 100, lh), text="Toolbox", manager=self.manager, container=control_panel)
        y += lh
        
        btn_w, btn_h = TOOL_BUTTON_SIZE
        btn_gap = 5
        
        self.elements['brush_tool_btn'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, y, btn_w, btn_h), text='', manager=self.manager, 
            container=control_panel, object_id='#tool_button')
        self.elements['select_tool_btn'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10 + btn_w + btn_gap, y, btn_w, btn_h), text='', manager=self.manager, 
            container=control_panel, object_id='#tool_button')
        self.elements['triangle_tool_btn'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10 + (btn_w + btn_gap) * 2, y, btn_w, btn_h), text='', manager=self.manager, 
            container=control_panel, object_id='#tool_button')
        self.elements['star_tool_btn'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10 + (btn_w + btn_gap) * 3, y, btn_w, btn_h), text='', manager=self.manager, 
            container=control_panel, object_id='#tool_button')

        y += btn_h + sp
        self._create_divider(y - sp/2, control_panel)

        panel_height = 135
        # --- 像素笔刷设置面板 ---
        self.elements['brush_panel'] = pygame_gui.elements.UIPanel(relative_rect=pygame.Rect(5, y, UI_PANEL_WIDTH-25, panel_height), manager=self.manager, container=control_panel, starting_layer_height=1)
        b_y = 5
        self.elements['brush_dropdown'] = pygame_gui.elements.UIDropDownMenu(options_list=['Line', 'Circle', 'Spray'], starting_option='Line', relative_rect=pygame.Rect(5, b_y, UI_PANEL_WIDTH-55, eh), manager=self.manager, container=self.elements['brush_panel'])
        b_y += eh + p
        self.elements['brush_size_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect(5, b_y, 40, lh), text="Size:", manager=self.manager, container=self.elements['brush_panel'])
        self.elements['brush_size_value_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect(50, b_y, 50, lh), text="1.0", manager=self.manager, container=self.elements['brush_panel'], object_id="@value_label")
        b_y += lh
        self.elements['brush_size_slider'] = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(5, b_y, UI_PANEL_WIDTH-80, 20), start_value=5, value_range=(1, 15), manager=self.manager, container=self.elements['brush_panel'])
        self.elements['brush_preview_pos'] = (DRAW_AREA_WIDTH + UI_PANEL_WIDTH - 45, y + b_y)
        
        # --- 矢量形状属性面板 ---
        self.elements['shape_props_panel'] = pygame_gui.elements.UIPanel(relative_rect=pygame.Rect(5, y, UI_PANEL_WIDTH-25, panel_height), manager=self.manager, container=control_panel, starting_layer_height=1, visible=0)
        s_y = 5
        self.elements['shape_size_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect(5, s_y, 40, lh), text="Size:", manager=self.manager, container=self.elements['shape_props_panel'])
        self.elements['shape_size_slider'] = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(50, s_y, 140, 20), start_value=50, value_range=(10, 300), manager=self.manager, container=self.elements['shape_props_panel'])
        s_y += lh + p
        self.elements['shape_rot_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect(5, s_y, 40, lh), text="Rot:", manager=self.manager, container=self.elements['shape_props_panel'])
        self.elements['shape_rot_slider'] = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(50, s_y, 140, 20), start_value=0, value_range=(0, 360), manager=self.manager, container=self.elements['shape_props_panel'])
        s_y += lh + p * 2
        self.elements['delete_shape_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(5, s_y, 185, 30), text='Delete Selected Shape', manager=self.manager, container=self.elements['shape_props_panel'])
        
        y += panel_height + sp
        self._create_divider(y - sp/2, control_panel)

        # --- 对称性设置 ---
        self.elements['symmetry_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect(10, y, UI_PANEL_WIDTH-40, lh), text="Symmetry", manager=self.manager, container=control_panel)
        y += lh
        self.elements['kaleido_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10, y, 95, eh), text='Kaleido', manager=self.manager, container=control_panel)
        self.elements['rotate_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(115, y, 95, eh), text='Rotate', manager=self.manager, container=control_panel)
        y += eh + p
        
        self.elements['slice_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect(10, y, 60, eh), text="Slices:", manager=self.manager, container=control_panel)
        self.elements['slice_value_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect(65, y, 30, eh), text="12", manager=self.manager, container=control_panel, object_id="@value_label")
        self.elements['slice_slider'] = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(100, y + 5, UI_PANEL_WIDTH - 125, 20),
            start_value=12, value_range=(4, 16), manager=self.manager, container=control_panel)
        
        y += eh + sp
        self._create_divider(y - sp/2, control_panel)
        
        # --- 颜色选择器 ---
        self.elements['color_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect(10, y, UI_PANEL_WIDTH - 40, lh), text="Color", manager=self.manager, container=control_panel)
        y += lh
        self.elements['start_color_rect'] = pygame.Rect(DRAW_AREA_WIDTH + 15, y, 85, 40)
        self.elements['end_color_rect'] = pygame.Rect(DRAW_AREA_WIDTH + 120, y, 85, 40)
        y += 40 + p
        spectrum_rect_size = (UI_PANEL_WIDTH - 50, 100)
        self.elements['spectrum_rect'] = pygame.Rect((DRAW_AREA_WIDTH + 15, y), spectrum_rect_size)
        self.spectrum_surface = utils.create_color_spectrum(spectrum_rect_size)
        y += 100 + sp
        self._create_divider(y - sp/2, control_panel)
        
        # --- 动态效果与辅助工具 ---
        self.elements['dynamics_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect(10, y, UI_PANEL_WIDTH-40, lh), text="Dynamics & Aids", manager=self.manager, container=control_panel)
        y += lh
        self.elements['global_rotate_toggle'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10, y, 95, eh), text='Global Rot', manager=self.manager, container=control_panel, object_id='#dynamic_toggle_button')
        self.elements['object_rotate_toggle'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(115, y, 95, eh), text='Object Rot', manager=self.manager, container=control_panel, object_id='#dynamic_toggle_button')
        y += eh + p
        self.elements['pulse_toggle'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10, y, 95, eh), text='Pulse', manager=self.manager, container=control_panel, object_id='#dynamic_toggle_button')
        self.elements['trail_toggle'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(115, y, 95, eh), text='Trail', manager=self.manager, container=control_panel, object_id='#dynamic_toggle_button')
        y += eh + p
        self.elements['guides_value_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect(10, y, 95, eh), text="Guides: Off", manager=self.manager, container=control_panel)
        self.elements['guides_slider'] = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(115, y + 5, 95, 20), start_value=0, value_range=(0, 3), manager=self.manager, container=control_panel)
        y += eh + sp
        self._create_divider(y - sp/2, control_panel)
        
        # --- 最终操作按钮 ---
        y += p
        self.elements['undo_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10, y, 95, 30), text='Undo', manager=self.manager, container=control_panel, visible=0)
        self.elements['redo_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(115, y, 95, 30), text='Redo', manager=self.manager, container=control_panel, visible=0)
        y += 30 + p
        self.elements['export_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10, y, UI_PANEL_WIDTH - 40, 40), text='Export...', manager=self.manager, container=control_panel)
        
        # --- 图层面板 ---
        layer_panel = pygame_gui.elements.UIPanel(relative_rect=pygame.Rect((DRAW_AREA_WIDTH + UI_PANEL_WIDTH, 0, LAYER_PANEL_WIDTH, SCREEN_HEIGHT)), manager=self.manager)
        self.elements['layer_label'] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect(0, 5, LAYER_PANEL_WIDTH, 20), text="Layers", manager=self.manager, container=layer_panel, object_id="@centered_label")
        
        generate_button_rect = pygame.Rect(10, 30, 160, 40)
        self.elements['generate_btn'] = pygame_gui.elements.UIButton(relative_rect=generate_button_rect, text='Generate New Layer', manager=self.manager, container=layer_panel)
        self.elements['skip_animation_btn'] = pygame_gui.elements.UIButton(relative_rect=generate_button_rect, text="I Can't Wait!", manager=self.manager, container=layer_panel, visible=0)

        self.elements['layer_list'] = pygame_gui.elements.UISelectionList(relative_rect=pygame.Rect(10, 80, 160, SCREEN_HEIGHT - 175), item_list=[], manager=self.manager, container=layer_panel)
        self.elements['clear_all_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10, SCREEN_HEIGHT - 90, 160, 30), text='Clear All Drawings', manager=self.manager, container=layer_panel)
        self.elements['delete_layer_btn'] = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10, SCREEN_HEIGHT - 55, 160, 30), text='Delete Selected Layer', manager=self.manager, container=layer_panel)
    
    def update_tool_buttons(self, active_tool):
        """
        根据当前激活的工具，更新工具栏按钮的图标。
        此方法现在是控制按钮外观的唯一途径。
        """
        tool_map = {
            'brush': self.elements['brush_tool_btn'],
            'select': self.elements['select_tool_btn'],
            'triangle': self.elements['triangle_tool_btn'],
            'star': self.elements['star_tool_btn']
        }

        # 从主题中获取按钮的背景色
        # 我们假设所有状态的背景色都一样
        try:
            bg_color = self.manager.ui_theme.get_colour('#tool_button', 'normal_bg')
        except (ValueError, AttributeError):
            bg_color = pygame.Color('#282c34') # 如果获取失败，使用一个备用颜色

        for tool_name, button in tool_map.items():
            is_active = (tool_name == active_tool)
            icon_key = 'selected' if is_active else 'normal'
            
            try:
                # [FIX] 创建一个与按钮大小相同的独立 Surface 作为画布
                button_surface = pygame.Surface(TOOL_BUTTON_SIZE, pygame.SRCALPHA)
                button_surface.fill(bg_color) # 用主题背景色填充画布

                # 加载并缩放我们的图标
                icon_path = ICONS[tool_name][icon_key]
                icon_surface = pygame.image.load(icon_path).convert_alpha()
                scaled_icon = pygame.transform.smoothscale(icon_surface, TOOL_BUTTON_SIZE)
                
                # 将图标绘制到我们的画布中央
                rect = scaled_icon.get_rect(center=(TOOL_BUTTON_SIZE[0] // 2, TOOL_BUTTON_SIZE[1] // 2))
                button_surface.blit(scaled_icon, rect)

                # 将最终合成的画布设置为按钮的图像
                button.set_image(button_surface)

            except pygame.error as e:
                print(f"Error loading icon for {tool_name} at {ICONS[tool_name][icon_key]}: {e}")
                button.set_text(tool_name[0].upper())

    def show_shape_properties(self, shape):
        """显示矢量形状属性面板，并用选中形状的属性更新滑块。"""
        self.elements['brush_panel'].hide()
        self.elements['shape_props_panel'].show()
        
        self.elements['shape_size_slider'].disable()
        self.elements['shape_rot_slider'].disable()
        
        self.elements['shape_size_slider'].set_current_value(shape.size)
        self.elements['shape_rot_slider'].set_current_value(shape.rotation % 360)
        
        self.elements['shape_size_slider'].enable()
        self.elements['shape_rot_slider'].enable()

    def show_brush_properties(self):
        """显示像素笔刷属性面板。"""
        self.elements['shape_props_panel'].hide()
        self.elements['brush_panel'].show()
        
    def hide_all_tool_properties(self):
        """隐藏所有与工具相关的属性面板。"""
        self.elements['brush_panel'].hide()
        self.elements['shape_props_panel'].hide()

    def draw_custom_ui(self, surface, start_color, end_color, active_color_selection, brush_size):
        """
        绘制非 pygame_gui 标准的自定义 UI 元素，如颜色选择器和笔刷预览。
        """
        pygame.draw.rect(surface, start_color, self.elements['start_color_rect'])
        pygame.draw.rect(surface, end_color, self.elements['end_color_rect'])
        active_rect = self.elements['start_color_rect'] if active_color_selection == 'start' else self.elements['end_color_rect']
        pygame.draw.rect(surface, WHITE, active_rect, 2)
        
        surface.blit(self.spectrum_surface, self.elements['spectrum_rect'].topleft)
        
        if self.elements['brush_panel'].visible:
            preview_pos = self.elements['brush_preview_pos']
            max_radius = 15
            current_radius = 1 + ((brush_size - 1) / (10 - 1)) * (max_radius - 1)
            pygame.draw.circle(surface, WHITE, preview_pos, max(1, int(current_radius)))

    def handle_color_picker_click(self, event_pos):
        """处理在自定义颜色选择器区域的点击事件。"""
        if self.elements['start_color_rect'].collidepoint(event_pos):
            return {'type': 'select', 'target': 'start'}
        if self.elements['end_color_rect'].collidepoint(event_pos):
            return {'type': 'select', 'target': 'end'}
        if self.elements['spectrum_rect'].collidepoint(event_pos):
            local_pos = (event_pos[0] - self.elements['spectrum_rect'].left, event_pos[1] - self.elements['spectrum_rect'].top)
            picked_color = self.spectrum_surface.get_at(local_pos)
            return {'type': 'pick', 'color': picked_color}
        return None