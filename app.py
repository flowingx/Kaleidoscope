"""
主应用程序类。
负责管理游戏循环、事件处理、状态更新和屏幕绘制。
这是整个项目的核心协调器。
"""
import pygame, pygame_gui, math, datetime, random
from collections import deque

import config, utils, drawing
from layer import Layer
from shapes import Triangle, Star
from ui_handler import UIHandler
from export_manager import ExportManager
from history_manager import (HistoryManager, AddLayerAction, AddShapeAction, 
                             DeleteShapeAction, ModifyShapeAction, DeleteLayerAction, ClearAllAction, AddPixelAction)

class App:
    """
    封装了整个万花筒应用程序。
    管理所有子系统（UI, 历史, 导出）和应用程序状态。
    """
    def __init__(self):
        """初始化应用程序，设置 Pygame、窗口、时钟和所有管理器。"""
        pygame.init()
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption("Kaleidoscope Vector Edition")
        self.clock = pygame.time.Clock()
        self.is_running = True

        # --- 状态变量 ---
        # 像素笔刷相关状态
        self.brush_type = 'Line'
        self.brush_size = 1.0
        self.user_path, self.is_drawing = [], False
        
        self.brush_spacing = 100.0  # (计划 2) Circle笔刷的间距，百分比
        self.brush_color_jitter = 0.0 # (计划 3) 颜色抖动, 0.0 to 1.0
        self.brush_flow = 30.0        # (计划 4) Spray笔刷的流量（每秒喷洒次数）
        self.brush_size_jitter = 1.0  # (计划 5) Spray笔刷的粒子大小变化（像素）
        self.spray_timer = 0.0        # (计划 4) 用于流量控制的计时器

        
        # 矢量形状相关状态
        self.active_tool = 'brush'
        self.selected_shape = None
        self.preview_shape = None
        self.is_creating_shape = False
        self.creation_start_pos = None
        self.shape_drag_offset = None
        self.shape_pre_drag_attrs = None
        self.is_rotating_shape = False
        self.rotation_handle_pos = pygame.Vector2(0, 0)

        # 共享状态
        self.num_slices, self.symmetry_mode = 12, 'Kaleidoscope'
        self.start_color, self.end_color = (255, 0, 255), (0, 255, 255)
        self.active_color_selection = 'start'
        
        # 动态效果状态
        self.enable_global_rotation, self.global_rotation_angle = False, 0.0
        self.enable_object_rotation, self.object_rotation_angle = False, 0.0
        self.enable_pulsing, self.pulsing_scale = False, 1.0
        self.enable_trails, self.trail_frames = False, deque(maxlen=15)
        self.guide_line_slices = 0

        # 图层管理
        self.layers = [Layer()]
        self.active_layer_index = 0
        
        # --- 管理器 ---
        self.export_manager = ExportManager()
        self.export_window = None
        self.history_manager = HistoryManager(self)
        try:
            self.ui_manager = pygame_gui.UIManager((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), config.THEME_PATH)
        except (FileNotFoundError, pygame.error):
            print("Warning: theme.json not found."); self.ui_manager = pygame_gui.UIManager((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        
        self.ui_handler = UIHandler(self.ui_manager)
        self.status_font = pygame.font.Font(None, 40)
        self._initialize_ui_state()

    def _initialize_ui_state(self):
        self.ui_handler.elements['slice_slider'].set_current_value(self.num_slices)
        self.ui_handler.elements['slice_value_label'].set_text(str(self.num_slices))
        self.ui_handler.elements['kaleido_btn'].select()
        
        initial_slider_value = 5
        self.ui_handler.elements['brush_size_slider'].set_current_value(initial_slider_value)
        self.brush_size = self._calculate_and_update_brush_size(initial_slider_value)
        
        self._update_layer_list_ui()
        self.ui_handler.update_tool_buttons(self.active_tool)
        self.ui_handler.show_brush_properties()
        self.ui_handler.update_brush_options_visibility(self.brush_type)


    def _calculate_and_update_brush_size(self, slider_value):
        normalized_value = (slider_value - 1) / (15 - 1)
        final_brush_size = 1 + normalized_value**2 * 9
        self.ui_handler.elements['brush_size_value_label'].set_text(f"{final_brush_size:.1f}")
        return final_brush_size

    def _update_layer_list_ui(self):
        if 'layer_list' in self.ui_handler.elements and self.ui_handler.elements['layer_list'] is not None:
            container = self.ui_handler.elements['layer_list'].ui_container
            rect = self.ui_handler.elements['layer_list'].relative_rect
            self.ui_handler.elements['layer_list'].kill()
        else:
            return

        item_list = [l.name for l in self.layers]
        selected_item = self.layers[self.active_layer_index].name if self.layers and self.active_layer_index < len(self.layers) else None
        
        self.ui_handler.elements['layer_list'] = pygame_gui.elements.UISelectionList(
            relative_rect=rect, item_list=item_list, manager=self.ui_manager, container=container)
        
        if selected_item and selected_item in item_list:
            try: self.ui_handler.elements['layer_list'].set_selection(selected_item)
            except AttributeError:
                try: self.ui_handler.elements['layer_list'].set_single_selection(selected_item)
                except AttributeError: pass

    def run(self):
        while self.is_running:
            time_delta_seconds = self.clock.tick(config.FPS) / 1000.0
            self._handle_events()
            self._update(time_delta_seconds)
            self._draw()

    def _handle_events(self):
        is_input_blocked = self.export_manager.is_active() or self.export_window is not None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            
            if event.type == pygame.KEYDOWN and not is_input_blocked:
                if event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                    if self.selected_shape: self._action_delete_selected_shape()
                if event.mod & pygame.KMOD_CTRL:
                    if event.key == pygame.K_z: self.history_manager.undo()
                    if event.key == pygame.K_y: self.history_manager.redo()

            if not is_input_blocked:
                self._handle_mouse_events(event)
            
            self._handle_gui_events(event)
            self.ui_manager.process_events(event)

    def _handle_mouse_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            color_event = self.ui_handler.handle_color_picker_click(event.pos)
            if color_event:
                if color_event['type'] == 'select': self.active_color_selection = color_event['target']
                elif color_event['type'] == 'pick':
                    color_to_set = color_event['color']
                    if self.active_color_selection == 'start': self.start_color = color_to_set
                    else: self.end_color = color_to_set
                    if self.selected_shape:
                        self._action_modify_selected_shape({'fill_color': color_to_set})
            elif pygame.Rect(0, 0, config.DRAW_AREA_WIDTH, config.SCREEN_HEIGHT).collidepoint(event.pos):
                if self.active_tool == 'brush':
                    self.is_drawing = True
                    self.user_path = [{'pos': event.pos, 'size': self.brush_size}]
                elif self.active_tool in ['triangle', 'star']:
                    self._start_shape_creation(event.pos)
                elif self.active_tool == 'select':
                    self._handle_selection(event.pos)
        
        if event.type == pygame.MOUSEMOTION:
            if self.is_drawing and pygame.Rect(0, 0, config.DRAW_AREA_WIDTH, config.SCREEN_HEIGHT).collidepoint(event.pos):
                self.user_path.append({'pos': event.pos, 'size': self.brush_size})
            elif self.is_creating_shape:
                self._update_shape_creation(event.pos)
            elif self.selected_shape and event.buttons[0]:
                self._drag_selected_shape(event.pos)
            elif self.is_rotating_shape:
                self._update_shape_rotation(event.pos)
        
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_drawing: self._action_finish_drawing()
            elif self.is_creating_shape: self._finish_shape_creation()
            elif self.shape_drag_offset: self._finish_shape_drag()
            elif self.is_rotating_shape: self._finish_shape_rotation()
    
    def _handle_gui_events(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            el = event.ui_element
            if el == self.ui_handler.elements['brush_tool_btn']: self._set_active_tool('brush')
            elif el == self.ui_handler.elements['select_tool_btn']: self._set_active_tool('select')
            elif el == self.ui_handler.elements['triangle_tool_btn']: self._set_active_tool('triangle')
            elif el == self.ui_handler.elements['star_tool_btn']: self._set_active_tool('star')
            elif el == self.ui_handler.elements['add_layer_btn']: self._action_add_new_layer()
            elif el == self.ui_handler.elements['clear_all_btn']: self._action_clear_all()
            elif el == self.ui_handler.elements['delete_layer_btn']: self._action_delete_layer()
            elif el == self.ui_handler.elements['delete_shape_btn']: self._action_delete_selected_shape()
            elif el == self.ui_handler.elements['undo_btn']: self.history_manager.undo()
            elif el == self.ui_handler.elements['redo_btn']: self.history_manager.redo()
            elif el == self.ui_handler.elements['export_btn']: self._action_open_export_window()
            elif el == self.ui_handler.elements['kaleido_btn']: self.symmetry_mode = 'Kaleidoscope'
            elif el == self.ui_handler.elements['rotate_btn']: self.symmetry_mode = 'Rotate'
            
            elif el == self.ui_handler.elements['global_rotate_toggle']: self.enable_global_rotation = not self.enable_global_rotation
            elif el == self.ui_handler.elements['object_rotate_toggle']: self.enable_object_rotation = not self.enable_object_rotation
            elif el == self.ui_handler.elements['pulse_toggle']: self.enable_pulsing = not self.enable_pulsing
            elif el == self.ui_handler.elements['trail_toggle']: self.enable_trails = not self.enable_trails
        
        if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            el = event.ui_element
            if el == self.ui_handler.elements['brush_size_slider']:
                self.brush_size = self._calculate_and_update_brush_size(event.value)
            elif el == self.ui_handler.elements['slice_slider']:
                value = int(event.value)
                self.num_slices = value if value % 2 == 0 else value - 1
                if self.num_slices < 4: self.num_slices = 4
                self.ui_handler.elements['slice_slider'].set_current_value(self.num_slices)
                self.ui_handler.elements['slice_value_label'].set_text(str(self.num_slices))
            elif el == self.ui_handler.elements['guides_slider']:
                self.guide_line_slices = {0:0, 1:8, 2:12, 3:16}.get(int(event.value),0)
                self.ui_handler.elements['guides_value_label'].set_text(f"Guides: {self.guide_line_slices if self.guide_line_slices > 0 else 'Off'}")
            elif el == self.ui_handler.elements['shape_size_slider']:
                if self.selected_shape: self._action_modify_selected_shape({'size': event.value})
            elif el == self.ui_handler.elements['shape_rot_slider']:
                 if self.selected_shape: self._action_modify_selected_shape({'rotation': event.value})
            elif el == self.ui_handler.elements['brush_spacing_slider']:
                self.brush_spacing = event.value
            elif el == self.ui_handler.elements['brush_color_jitter_slider']:
                self.brush_color_jitter = event.value / 100.0 # 转换为 0-1 范围
            elif el == self.ui_handler.elements['brush_flow_slider']:
                self.brush_flow = event.value
            elif el == self.ui_handler.elements['brush_size_jitter_slider']:
                self.brush_size_jitter = event.value


        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED and event.ui_element == self.ui_handler.elements['brush_dropdown']:
            self.brush_type = event.text
            self.ui_handler.update_brush_options_visibility(self.brush_type)


        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION and event.ui_element == self.ui_handler.elements['layer_list']:
            for i, layer in enumerate(self.layers):
                if layer.name == event.text: self.active_layer_index = i; break

        if event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED and event.ui_element == self.export_window:
            self._action_start_export()
    
    def _update_ui_button_states(self):
        """ 
        更新 UI 按钮状态以反映当前应用程序状态。
        """
        if self.symmetry_mode == 'Kaleidoscope':
            self.ui_handler.elements['kaleido_btn'].select()
            self.ui_handler.elements['rotate_btn'].unselect()
        else:
            self.ui_handler.elements['kaleido_btn'].unselect()
            self.ui_handler.elements['rotate_btn'].select()

        toggles = {
            self.enable_global_rotation: self.ui_handler.elements['global_rotate_toggle'],
            self.enable_object_rotation: self.ui_handler.elements['object_rotate_toggle'],
            self.enable_pulsing: self.ui_handler.elements['pulse_toggle'],
            self.enable_trails: self.ui_handler.elements['trail_toggle'],
        }
        for is_enabled, button in toggles.items():
            if is_enabled:
                button.select()
            else:
                button.unselect()

        if self.history_manager.can_undo(): self.ui_handler.elements['undo_btn'].show()
        else: self.ui_handler.elements['undo_btn'].hide()
        if self.history_manager.can_redo(): self.ui_handler.elements['redo_btn'].show()
        else: self.ui_handler.elements['redo_btn'].hide()

    def _update(self, time_delta_seconds):
        self.ui_manager.update(time_delta_seconds)

        if self.is_drawing and self.brush_type == 'Spray':
            self.spray_timer += time_delta_seconds
            flow_interval = 1.0 / self.brush_flow
            while self.spray_timer >= flow_interval:
                self.spray_timer -= flow_interval
                current_pos = pygame.mouse.get_pos()
                # 确保只在绘制区域内添加点
                if pygame.Rect(0, 0, config.DRAW_AREA_WIDTH, config.SCREEN_HEIGHT).collidepoint(current_pos):
                    self.user_path.append({'pos': current_pos, 'size': self.brush_size})
        self._update_ui_button_states()
        
        self.ui_handler.update_tool_buttons(self.active_tool)

        if self.enable_global_rotation: self.global_rotation_angle = (self.global_rotation_angle - 0.5) % 360
        if self.enable_object_rotation: self.object_rotation_angle = (self.object_rotation_angle + 1.0) % 360
        if self.enable_pulsing: self.pulsing_scale = 1.0 + 0.05 * math.sin(pygame.time.get_ticks() * 0.002)
        else: self.pulsing_scale = 1.0
        
        self.export_manager.update()
        self.export_manager.update_timer(time_delta_seconds * 1000)


    def _draw(self):
        self.screen.fill(config.BACKGROUND_COLOR)
        composite_image = drawing.get_composite_image(self.layers, self.num_slices, self.symmetry_mode, self.object_rotation_angle)
        
        if self.enable_trails:
            trail_copy = composite_image.copy()
            alpha = int(255 * (0.85 ** (len(self.trail_frames) + 1)))
            self.trail_frames.append((trail_copy, alpha))
        else:
            self.trail_frames.clear()

        final_image = drawing.apply_global_dynamics(composite_image, self.global_rotation_angle, self.pulsing_scale, self.trail_frames)
        
        if self.guide_line_slices > 0: drawing.draw_guide_lines(final_image, self.guide_line_slices)

        self.screen.blit(final_image, (0, 0))

        if self.preview_shape: self.preview_shape.draw(self.screen)
        if self.selected_shape:
            pygame.draw.rect(self.screen, config.SELECTION_COLOR, self.selected_shape.get_bounding_box(), 2)
        
        if self.is_drawing and self.user_path and len(self.user_path) > 1:
            points_to_draw = [p['pos'] for p in self.user_path]
            slice_angle_deg = 360 / self.num_slices
            center_vector = pygame.Vector2(config.CENTER_X, config.CENTER_Y)
            for i in range(self.num_slices):
                slice_rotation_angle = i * slice_angle_deg
                transformed_points = []
                for p in points_to_draw:
                    pos_relative_to_center = pygame.Vector2(p) - center_vector
                    rotated_pos = pos_relative_to_center.rotate(slice_rotation_angle)
                    if self.symmetry_mode == 'Kaleidoscope' and i % 2 == 1:
                        rotated_pos.y *= -1
                    final_pos = rotated_pos + center_vector
                    transformed_points.append(final_pos)
                pygame.draw.lines(self.screen, config.PREVIEW_LINE_COLOR, False, transformed_points, 2)

        self._draw_layer_highlight()

        self.ui_manager.draw_ui(self.screen)
        self.ui_handler.draw_custom_ui(self.screen, self.start_color, self.end_color, self.active_color_selection, self.brush_size)
        self._draw_export_status()
        
        pygame.display.flip()
    
    def _draw_layer_highlight(self):
        """Draws a visible border around the currently active layer in the UI list."""
        try:
            layer_list = self.ui_handler.elements['layer_list']
            if not layer_list.item_list: return

            list_rect = layer_list.get_abs_rect()
            item_height = layer_list.list_item_height
            list_view_rect = layer_list.viewable_area.get_abs_rect() 

            scroll_offset = 0
            if layer_list.scroll_bar:
                scroll_offset = layer_list.scroll_bar.scroll_position

            item_y_in_full_list = self.active_layer_index * item_height
            visible_item_y = list_rect.top + 5 + item_y_in_full_list - scroll_offset 

            if visible_item_y >= list_view_rect.top and (visible_item_y + item_height) <= list_view_rect.bottom:
                highlight_rect = pygame.Rect(
                    list_rect.left + 5,
                    visible_item_y,
                    list_rect.width - 25,
                    item_height
                )
                pygame.draw.rect(self.screen, config.SELECTION_COLOR, highlight_rect, 2, border_radius=3)
        except (KeyError, AttributeError):
            pass

    def _set_active_tool(self, tool_name):
        if self.active_tool == tool_name: return
        self.active_tool = tool_name
        if self.selected_shape: self.selected_shape = None
        if tool_name == 'brush': self.ui_handler.show_brush_properties()
        else: self.ui_handler.hide_all_tool_properties()
        
        self.ui_handler.update_tool_buttons(self.active_tool)

    def _start_shape_creation(self, pos):
        self.is_creating_shape = True
        self.creation_start_pos = pos
        stroke_color, stroke_width = self.start_color, self.brush_size
        fill_color = (0, 0, 0, 0)
        if self.active_tool == 'triangle': 
            self.preview_shape = Triangle(pos, 1, fill_color, stroke_width=stroke_width, stroke_color=stroke_color)
        elif self.active_tool == 'star': 
            self.preview_shape = Star(pos, 1, fill_color, stroke_width=stroke_width, stroke_color=stroke_color)

    def _update_shape_creation(self, pos):
        if not self.preview_shape: return
        self.preview_shape.size = pygame.Vector2(pos).distance_to(self.creation_start_pos)
        self.preview_shape.pos = self.creation_start_pos

    def _finish_shape_creation(self):
        if not self.preview_shape or self.preview_shape.size < 5:
            self.is_creating_shape = False; self.preview_shape = None; return
        action = AddShapeAction(self.layers[self.active_layer_index], self.preview_shape)
        self.history_manager.execute_action(action)
        self.is_creating_shape, self.preview_shape = False, None

    def _handle_selection(self, pos):
        if self.selected_shape: self.selected_shape.selected = False
        self.selected_shape = None
        self.ui_handler.hide_all_tool_properties()
        click_pos_vec = pygame.Vector2(pos)
        center_vector = pygame.Vector2(config.CENTER_X, config.CENTER_Y)
        slice_angle_deg = 360 / self.num_slices
        active_layer = self.layers[self.active_layer_index]
        if not active_layer.is_visible: return

        for shape in reversed(active_layer.shapes):
            for i in range(self.num_slices):
                pos_relative_to_center = click_pos_vec - center_vector
                if self.symmetry_mode == 'Kaleidoscope' and i % 2 == 1:
                    pos_relative_to_center.y *= -1
                inversely_rotated_pos = pos_relative_to_center.rotate(-(i * slice_angle_deg))
                test_pos = inversely_rotated_pos + center_vector
                
                if shape.get_bounding_box().collidepoint(test_pos):
                    self.selected_shape = shape; shape.selected = True
                    self.shape_drag_offset = test_pos - shape.pos
                    self.shape_pre_drag_attrs = {'pos': shape.pos}
                    self.ui_handler.show_shape_properties(shape)
                    return

    def _drag_selected_shape(self, pos):
        if not self.selected_shape or not self.shape_drag_offset: return
        self.selected_shape.pos = pygame.Vector2(pos) - self.shape_drag_offset

    def _finish_shape_drag(self):
        if not self.selected_shape or not self.shape_pre_drag_attrs: return
        new_attrs = {'pos': self.selected_shape.pos}
        if self.shape_pre_drag_attrs['pos'] != new_attrs['pos']:
            action = ModifyShapeAction(self.selected_shape, self.shape_pre_drag_attrs, new_attrs)
            self.history_manager.execute_action(action)
        self.shape_drag_offset, self.shape_pre_drag_attrs = None, None

    def _action_modify_selected_shape(self, new_attrs):
        if not self.selected_shape: return
        old_attrs = {key: getattr(self.selected_shape, key) for key in new_attrs}
        action = ModifyShapeAction(self.selected_shape, old_attrs, new_attrs)
        self.history_manager.execute_action(action)

    def _action_delete_selected_shape(self):
        if not self.selected_shape: return
        action = DeleteShapeAction(self.layers[self.active_layer_index], self.selected_shape)
        self.history_manager.execute_action(action)
        self.selected_shape = None
        self.ui_handler.hide_all_tool_properties()
    
    def _action_add_new_layer(self):
        new_layer = Layer()
        action = AddLayerAction(self, new_layer)
        self.history_manager.execute_action(action)

    def _action_finish_drawing(self):
        """
        将用户绘制的路径根据不同的笔刷类型（Line, Circle, Spray）转换成一系列可绘制的元素。
        这是实现不同笔刷效果的核心。
        """
        if not self.user_path:
            self.is_drawing, self.spray_timer = False, 0.0
            return

        elements_to_draw = []
        path_len = len(self.user_path)

        # [FIX] 将 path_length_pixels 的计算提到所有 if/elif 之前
        # 这样 'Line' 和 'Circle' 笔刷都可以安全地使用它。
        path_length_pixels = 0
        if path_len >= 2:
            path_length_pixels = sum(pygame.Vector2(self.user_path[i+1]['pos']).distance_to(self.user_path[i]['pos']) for i in range(path_len-1))

        if self.brush_type == 'Line':
            if path_len < 2 or path_length_pixels == 0:
                self.is_drawing, self.spray_timer = False, 0.0; self.user_path.clear(); return

            current_dist = 0
            for i in range(path_len-1):
                p1, p2 = self.user_path[i], self.user_path[i+1]
                dist = pygame.Vector2(p2['pos']).distance_to(p1['pos'])
                steps = max(1, int(dist))
                for j in range(steps):
                    t = j / steps
                    pos = pygame.Vector2(p1['pos']).lerp(p2['pos'], t)
                    size = p1['size'] * (1 - t) + p2['size'] * t
                    color_t = (current_dist + dist*t) / path_length_pixels
                    color = utils.lerp_color(self.start_color, self.end_color, color_t)
                    elements_to_draw.append({'pos': pos, 'color': color, 'size': int(size), 'type': 'Circle'})
                current_dist += dist

        elif self.brush_type == 'Circle':
            if path_len < 2 or path_length_pixels == 0:
                self.is_drawing, self.spray_timer = False, 0.0; self.user_path.clear(); return

            distance_covered = 0.0
            distance_since_last_stamp = 0.0

            for i in range(path_len - 1):
                p1_data, p2_data = self.user_path[i], self.user_path[i+1]
                p1, p2 = pygame.Vector2(p1_data['pos']), pygame.Vector2(p2_data['pos'])
                segment_length = p1.distance_to(p2)
                if segment_length == 0: continue

                dist_in_segment = 0.0
                while dist_in_segment < segment_length:
                    current_t = dist_in_segment / segment_length if segment_length > 0 else 0
                    current_size = p1_data['size'] * (1 - current_t) + p2_data['size'] * current_t
                    spacing_pixels = current_size * (self.brush_spacing / 100.0)

                    if distance_since_last_stamp >= spacing_pixels:
                        stamp_pos = p1.lerp(p2, current_t)
                        path_t = (distance_covered + dist_in_segment) / path_length_pixels
                        jitter_amount = self.brush_color_jitter * (random.random() - 0.5)
                        final_t = max(0.0, min(1.0, path_t + jitter_amount))
                        color = utils.lerp_color(self.start_color, self.end_color, final_t)
                        
                        elements_to_draw.append({
                            'pos': stamp_pos,
                            'color': color,
                            'size': int(current_size),
                            'type': 'Circle'
                        })
                        distance_since_last_stamp = 0

                    step = 1.0 
                    dist_in_segment += step
                    distance_since_last_stamp += step
                
                distance_covered += segment_length

        elif self.brush_type == 'Spray':
            spray_radius_multiplier = 5
            dots_per_size_unit = 2
            
            for i, point_data in enumerate(self.user_path):
                center_pos = pygame.Vector2(point_data['pos'])
                brush_size = point_data['size']
                num_dots = int(brush_size * dots_per_size_unit)
                spray_radius = brush_size * spray_radius_multiplier
                
                color_t = i / (path_len - 1) if path_len > 1 else 0.5
                base_color = utils.lerp_color(self.start_color, self.end_color, color_t)

                for _ in range(num_dots):
                    random_angle = random.uniform(0, 360)
                    sigma = spray_radius / 3.0
                    random_dist = abs(random.gauss(0, sigma))
                    offset = pygame.Vector2(random_dist, 0).rotate(random_angle)
                    dot_pos = center_pos + offset

                    min_size = max(1, 2 - self.brush_size_jitter)
                    max_size = 2 + self.brush_size_jitter
                    dot_size = random.uniform(min_size, max_size)

                    elements_to_draw.append({
                        'pos': dot_pos,
                        'color': base_color,
                        'size': int(dot_size),
                        'type': 'Circle'
                    })

        if elements_to_draw:
            action = AddPixelAction(
                layer=self.layers[self.active_layer_index], elements=elements_to_draw,
                num_slices=self.num_slices, symmetry_mode=self.symmetry_mode
            )
            self.history_manager.execute_action(action)

        self.is_drawing = False
        self.user_path.clear()
        self.spray_timer = 0.0

        
    def _action_clear_all(self):
        if not self.layers: return
        action = ClearAllAction(self, list(self.layers))
        self.history_manager.execute_action(action)

    def _action_delete_layer(self):
        if len(self.layers) > 1:
            layer_to_delete = self.layers[self.active_layer_index]
            index = self.active_layer_index
            action = DeleteLayerAction(self, layer_to_delete, index)
            self.history_manager.execute_action(action)

    def _action_open_export_window(self):
        self.export_window = pygame_gui.windows.UIConfirmationDialog(
            rect=pygame.Rect((0, 0), (400, 220)), manager=self.ui_manager, window_title="Export Options", 
            action_long_desc="", action_short_name="Export", blocking=True)
        self.export_window.rect.center = (config.SCREEN_WIDTH//2, config.SCREEN_HEIGHT//2)
        filename_input = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect(10, 10, 360, 30), manager=self.ui_manager, container=self.export_window)
        filename_input.set_text("kaleido_art_" + datetime.datetime.now().strftime("%H%M%S"))
        format_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=['PNG (Image)', 'GIF (Animation)'], starting_option='PNG (Image)', 
            relative_rect=pygame.Rect(10, 50, 360, 30), manager=self.ui_manager, container=self.export_window)
        self.export_window.filename_input, self.export_window.format_dropdown = filename_input, format_dropdown

    def _action_start_export(self):
        filename = self.export_window.filename_input.get_text()
        file_format = self.export_window.format_dropdown.selected_option
        
        if file_format == 'PNG (Image)':
            composite_image = drawing.get_composite_image(self.layers, self.num_slices, self.symmetry_mode, self.object_rotation_angle)
            final_image = drawing.apply_global_dynamics(composite_image, self.global_rotation_angle, self.pulsing_scale, self.trail_frames)
            self.export_manager.start_png_export(filename, final_image)
        
        elif file_format == 'GIF (Animation)':
            dynamics_params = {
                'enable_global_rotation': self.enable_global_rotation, 'global_rotation_angle': self.global_rotation_angle,
                'enable_object_rotation': self.enable_object_rotation, 'object_rotation_angle': self.object_rotation_angle,
                'enable_pulsing': self.enable_pulsing, 'enable_trails': self.enable_trails,
            }
            self.export_manager.start_gif_export(
                filename=filename, layers=self.layers, num_slices=self.num_slices,
                symmetry_mode=self.symmetry_mode, dynamics_params=dynamics_params,
                duration=3, rotation_cycles=0.1
            )
        self.export_window, self.ui_manager.set_focus_set(None)

    def _draw_export_status(self):
        message, progress = self.export_manager.get_status()
        if not message: return
        text_surf = self.status_font.render(message, True, config.STATUS_TEXT_COLOR)
        text_rect = text_surf.get_rect(center=(config.DRAW_AREA_WIDTH // 2, 40))
        bg_rect = text_rect.inflate(20,20)
        s = pygame.Surface(bg_rect.size, pygame.SRCALPHA); s.fill((0,0,0,180))
        self.screen.blit(s, bg_rect.topleft)
        self.screen.blit(text_surf, text_rect)
        if self.export_manager.state in ["rendering_gif", "saving_gif"]:
            bar_rect = pygame.Rect(0,0, bg_rect.width - 20, 10)
            bar_rect.center = (bg_rect.centerx, bg_rect.bottom + 10)
            pygame.draw.rect(self.screen, (80,80,80), bar_rect, border_radius=3)
            progress_width = bar_rect.width * progress
            pygame.draw.rect(self.screen, (100,200,100), (bar_rect.left, bar_rect.top, progress_width, bar_rect.height), border_radius=3)