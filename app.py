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
        self.elements_to_animate = []
        self.is_animating, self.skip_animation = False, False
        self.animation_index, self.animation_delay, self.last_animation_time = 0, 1, 0
        
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
        self.layers = [Layer(name="Background")]
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
        # [FIX] 确保在启动时调用一次，以设置正确的初始图标
        self.ui_handler.update_tool_buttons(self.active_tool)
        self.ui_handler.show_brush_properties()

    def _calculate_and_update_brush_size(self, slider_value):
        # Your easing function for brush size
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
            return # Should not happen after init

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
        """启动并维持应用程序的主循环。"""
        while self.is_running:
            time_delta_seconds = self.clock.tick(config.FPS) / 1000.0
            
            self._handle_events()
            self._update(time_delta_seconds)
            self._draw()

    def _handle_events(self):
        """处理一帧内的所有事件，包括退出、键盘和鼠标事件。"""
        is_input_blocked = self.export_manager.is_active() or self.export_window is not None
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            
            # --- Keyboard Shortcuts ---
            if event.type == pygame.KEYDOWN and not is_input_blocked:
                if event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                    if self.selected_shape: self._action_delete_selected_shape()
                
                if event.mod & pygame.KMOD_CTRL:
                    if event.key == pygame.K_z: self.history_manager.undo()
                    if event.key == pygame.K_y: self.history_manager.redo()

            # --- Mouse Events ---
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
                    # If a shape is selected, change its color
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
            if self.is_drawing:
                if pygame.Rect(0, 0, config.DRAW_AREA_WIDTH, config.SCREEN_HEIGHT).collidepoint(event.pos):
                    self.user_path.append({'pos': event.pos, 'size': self.brush_size})
            elif self.is_creating_shape:
                self._update_shape_creation(event.pos)
            elif self.selected_shape and event.buttons[0]:
                self._drag_selected_shape(event.pos)
            elif self.is_rotating_shape:
                # 处理形状旋转
                self._update_shape_rotation(event.pos)
        
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_drawing: self.is_drawing = False
            elif self.is_creating_shape: self._finish_shape_creation()
            elif self.shape_drag_offset: self._finish_shape_drag()
            elif self.is_rotating_shape: self._finish_shape_rotation()
    
    def _handle_gui_events(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            el = event.ui_element
            # [FIX] Centralize tool selection logic
            if el == self.ui_handler.elements['brush_tool_btn']: self._set_active_tool('brush')
            elif el == self.ui_handler.elements['select_tool_btn']: self._set_active_tool('select')
            elif el == self.ui_handler.elements['triangle_tool_btn']: self._set_active_tool('triangle')
            elif el == self.ui_handler.elements['star_tool_btn']: self._set_active_tool('star')
            
            elif el == self.ui_handler.elements['generate_btn']: self._action_generate()
            elif el == self.ui_handler.elements['skip_animation_btn']: self.skip_animation = True
            elif el == self.ui_handler.elements['clear_all_btn']: self._action_clear_all()
            elif el == self.ui_handler.elements['delete_layer_btn']: self._action_delete_layer()
            elif el == self.ui_handler.elements['delete_shape_btn']: self._action_delete_selected_shape()
            elif el == self.ui_handler.elements['undo_btn']: self.history_manager.undo()
            elif el == self.ui_handler.elements['redo_btn']: self.history_manager.redo()
            elif el == self.ui_handler.elements['export_btn']: self._action_open_export_window()
            elif el == self.ui_handler.elements['kaleido_btn']: self.symmetry_mode = 'Kaleidoscope'; self.ui_handler.elements['rotate_btn'].unselect()
            elif el == self.ui_handler.elements['rotate_btn']: self.symmetry_mode = 'Rotate'; self.ui_handler.elements['kaleido_btn'].unselect()
            # [FIX] 添加按钮状态切换逻辑
            elif el == self.ui_handler.elements['global_rotate_toggle']:
                self.enable_global_rotation = not self.enable_global_rotation
                if self.enable_global_rotation: el.select()
                else: el.unselect()
            elif el == self.ui_handler.elements['object_rotate_toggle']:
                self.enable_object_rotation = not self.enable_object_rotation
                if self.enable_object_rotation: el.select()
                else: el.unselect()
            elif el == self.ui_handler.elements['pulse_toggle']:
                self.enable_pulsing = not self.enable_pulsing
                if self.enable_pulsing: el.select()
                else: el.unselect()
            elif el == self.ui_handler.elements['trail_toggle']:
                self.enable_trails = not self.enable_trails
                if self.enable_trails: el.select()
                else: el.unselect()
        
        if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            el = event.ui_element
            if el == self.ui_handler.elements['brush_size_slider']:
                self.brush_size = self._calculate_and_update_brush_size(event.value)
            elif el == self.ui_handler.elements['slice_slider']:
                # 确保值为偶数
                value = int(event.value)
                self.num_slices = value if value % 2 == 0 else value - 1
                if self.num_slices < 4: self.num_slices = 4 # 确保最小值
                self.ui_handler.elements['slice_slider'].set_current_value(self.num_slices) # 更新滑块到有效值
                self.ui_handler.elements['slice_value_label'].set_text(str(self.num_slices))
            elif el == self.ui_handler.elements['guides_slider']:
                self.guide_line_slices = {0:0, 1:8, 2:12, 3:16}.get(int(event.value),0)
                self.ui_handler.elements['guides_value_label'].set_text(f"Guides: {self.guide_line_slices if self.guide_line_slices > 0 else 'Off'}")
            elif el == self.ui_handler.elements['shape_size_slider']:
                if self.selected_shape: self._action_modify_selected_shape({'size': event.value})
            elif el == self.ui_handler.elements['shape_rot_slider']:
                 if self.selected_shape: self._action_modify_selected_shape({'rotation': event.value})

        if event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
            pass # 旧的 slice_input 逻辑不再需要

        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED and event.ui_element == self.ui_handler.elements['brush_dropdown']:
            self.brush_type = event.text

        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION and event.ui_element == self.ui_handler.elements['layer_list']:
            for i, layer in enumerate(self.layers):
                if layer.name == event.text: self.active_layer_index = i; break

        if event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED and event.ui_element == self.export_window:
            self._action_start_export()
    
    def _update(self, time_delta_seconds):
        """
        更新所有需要随时间变化的状态。
        包括 UI 管理器、动态效果的角度和缩放、以及导出过程。
        """
        self.ui_manager.update(time_delta_seconds)

        if self.enable_global_rotation: self.global_rotation_angle = (self.global_rotation_angle - 0.5) % 360 # Pygame rotate is counter-clockwise
        if self.enable_object_rotation: self.object_rotation_angle = (self.object_rotation_angle + 1.0) % 360
        if self.enable_pulsing: self.pulsing_scale = 1.0 + 0.05 * math.sin(pygame.time.get_ticks() * 0.002)
        else: self.pulsing_scale = 1.0
        
        if self.history_manager.can_undo():
            self.ui_handler.elements['undo_btn'].show()
        else:
            self.ui_handler.elements['undo_btn'].hide()

        if self.history_manager.can_redo():
            self.ui_handler.elements['redo_btn'].show()
        else:
            self.ui_handler.elements['redo_btn'].hide()

        if not self.is_animating:
            self.ui_handler.elements['generate_btn'].show()
            self.ui_handler.elements['skip_animation_btn'].hide()
        else:
            self.ui_handler.elements['generate_btn'].hide()
            self.ui_handler.elements['skip_animation_btn'].show()

        if self.is_animating:
            if self.skip_animation:
                self._finish_current_animation(); self.skip_animation = False
            else:
                current_time = pygame.time.get_ticks()
                if current_time - self.last_animation_time > self.animation_delay:
                    self.last_animation_time = current_time
                    if self.animation_index < len(self.elements_to_animate):
                        el = self.elements_to_animate[self.animation_index]
                        drawing.draw_on_surface(self.layers[0].surface, [el], self.num_slices, self.symmetry_mode)
                        self.animation_index += 1
                    else: self.is_animating = False

        self.export_manager.update()
        self.export_manager.update_timer(time_delta_seconds * 1000)

    def _draw(self):
        """
        将所有内容绘制到屏幕上。
        这是一个分层的过程，确保动态效果、引导线和 UI 元素按正确顺序绘制。
        """
        self.screen.fill(config.BACKGROUND_COLOR)
        
        # 1. Render base symmetrical image of all layers
        composite_image = drawing.get_composite_image(self.layers, self.num_slices, self.symmetry_mode, self.object_rotation_angle)
        
        # 2. Capture a frame for trail effect if enabled
        if self.enable_trails:
            trail_copy = composite_image.copy()
            alpha = int(255 * (0.85 ** (len(self.trail_frames) + 1)))
            self.trail_frames.append((trail_copy, alpha))
        else:
            self.trail_frames.clear()

        # 3. Apply final global dynamics
        final_image = drawing.apply_global_dynamics(composite_image, self.global_rotation_angle, self.pulsing_scale, self.trail_frames)
        
        # 4. Draw guide lines on top of the dynamics-applied image
        if self.guide_line_slices > 0:
            drawing.draw_guide_lines(final_image, self.guide_line_slices)

        self.screen.blit(final_image, (0, 0))

        # 5. Draw non-symmetrical overlays (previews, selection boxes)
        if self.preview_shape: self.preview_shape.draw(self.screen)
        if self.selected_shape:
            pygame.draw.rect(self.screen, (0, 150, 255), self.selected_shape.get_bounding_box(), 2)
        if self.user_path:
            if self.brush_type == 'Line' and len(self.user_path) > 1:
                pygame.draw.lines(self.screen, config.PREVIEW_LINE_COLOR, False, [p['pos'] for p in self.user_path], 2)

        # 6. Draw UI
        self.ui_manager.draw_ui(self.screen)
        self.ui_handler.draw_custom_ui(self.screen, self.start_color, self.end_color, self.active_color_selection, self.brush_size)
        self._draw_export_status()
        
        pygame.display.flip()
    
    # --- Tool and Action Methods ---
    def _set_active_tool(self, tool_name):
        """设置当前激活的工具，并立即更新所有工具按钮的UI状态。"""
        if self.active_tool == tool_name:
            return # Avoid redundant updates

        self.active_tool = tool_name
        
        # Deselect any vector shape when changing tools
        if self.selected_shape:
            self.selected_shape = None
        
        # Show/hide relevant property panels
        if tool_name == 'brush':
            self.ui_handler.show_brush_properties()
        elif tool_name in ['select', 'triangle', 'star']:
            # For shape tools, initially hide props until a shape is selected/created
            self.ui_handler.hide_all_tool_properties()
        
        # [FIX] Immediately update all tool buttons' visual state
        self.ui_handler.update_tool_buttons(self.active_tool)

    # --- Shape Creation ---
    def _start_shape_creation(self, pos):
        self.is_creating_shape = True
        self.creation_start_pos = pos
        
        # 形状 描边
        # 描边颜色来自 start_color，粗细来自 brush_size
        stroke_color = self.start_color
        stroke_width = self.brush_size
        fill_color = (0, 0, 0, 0) # 设置为完全透明的填充色

        if self.active_tool == 'triangle': 
            self.preview_shape = Triangle(pos, 1, fill_color, stroke_width=stroke_width, stroke_color=stroke_color)
        elif self.active_tool == 'star': 
            self.preview_shape = Star(pos, 1, fill_color, stroke_width=stroke_width, stroke_color=stroke_color)

    def _update_shape_creation(self, pos):
        if not self.preview_shape: return
        size = pygame.Vector2(pos).distance_to(self.creation_start_pos)
        self.preview_shape.size = size
        self.preview_shape.pos = self.creation_start_pos

    def _finish_shape_creation(self):
        if not self.preview_shape or self.preview_shape.size < 5:
            self.is_creating_shape = False; self.preview_shape = None; return
        action = AddShapeAction(self.layers[self.active_layer_index], self.preview_shape)
        self.history_manager.execute_action(action)
        self.is_creating_shape = False
        self.preview_shape = None

    # --- Shape Selection & Modification ---
    def _handle_selection(self, pos):
        if self.selected_shape: self.selected_shape.selected = False
        self.selected_shape = None
        self.ui_handler.hide_all_tool_properties()
        
        for layer in [self.layers[self.active_layer_index]]: # Only select on active layer
            if not layer.is_visible: continue
            for shape in reversed(layer.shapes):
                if shape.get_bounding_box().collidepoint(pos):
                    self.selected_shape = shape
                    shape.selected = True
                    self.shape_drag_offset = pygame.Vector2(pos) - shape.pos
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
        self.shape_drag_offset = None
        self.shape_pre_drag_attrs = None

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
    
    # --- Pixel Brush Actions ---
    def _action_generate(self):
        if len(self.user_path) > 1:
            self.is_drawing = False
            new_layer = Layer()
            action = AddLayerAction(self, new_layer)
            self.history_manager.execute_action(action)
            
            self.is_animating = True; self.animation_index = 0; self.elements_to_animate.clear()
            total_dist = sum(pygame.Vector2(self.user_path[i+1]['pos']).distance_to(self.user_path[i]['pos']) for i in range(len(self.user_path)-1))
            current_dist = 0
            if total_dist > 0:
                for i in range(len(self.user_path)-1):
                    p1, p2 = self.user_path[i], self.user_path[i+1]; dist = pygame.Vector2(p2['pos']).distance_to(p1['pos'])
                    steps = max(1, int(dist))
                    for j in range(steps):
                        t = j / steps
                        pos = pygame.Vector2(p1['pos']).lerp(p2['pos'], t)
                        size = p1['size'] * (1-t) + p2['size'] * t
                        color = utils.lerp_color(self.start_color, self.end_color, (current_dist + dist*t)/total_dist)
                        self.elements_to_animate.append({'pos': pos, 'color': color, 'size': int(size), 'type': 'Circle' if self.brush_type == 'Line' else self.brush_type})
                    current_dist += dist
            self.user_path.clear()
    
    def _finish_current_animation(self):
        if not self.is_animating or not self.elements_to_animate: return
        remaining = self.elements_to_animate[self.animation_index:]
        drawing.draw_on_surface(self.layers[0].surface, remaining, self.num_slices, self.symmetry_mode)
        self.is_animating = False
        self.animation_index = 0
        self.elements_to_animate.clear()
        
    # --- Other Actions ---
    def _action_clear_all(self):
        if self.is_animating: self._finish_current_animation()
        self.is_drawing = False; self.user_path.clear()
        if len(self.layers) > 1:
            cleared_layers = self.layers[:-1]
            action = ClearAllAction(self, cleared_layers)
            self.history_manager.execute_action(action)

    def _action_delete_layer(self):
        if len(self.layers) > 1 and self.layers[self.active_layer_index].name != "Background":
            layer_to_delete = self.layers[self.active_layer_index]
            index = self.active_layer_index
            action = DeleteLayerAction(self, layer_to_delete, index)
            self.history_manager.execute_action(action)

    def _action_open_export_dialog(self):
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
            # 渲染单帧图像用于PNG导出
            composite_image = drawing.get_composite_image(self.layers, self.num_slices, self.symmetry_mode, self.object_rotation_angle)
            final_image = drawing.apply_global_dynamics(composite_image, self.global_rotation_angle, self.pulsing_scale, self.trail_frames)
            self.export_manager.start_png_export(filename, final_image)
        
        elif file_format == 'GIF (Animation)':
            # 收集所有动态效果的当前状态
            dynamics_params = {
                'enable_global_rotation': self.enable_global_rotation,
                'global_rotation_angle': self.global_rotation_angle,
                'enable_object_rotation': self.enable_object_rotation,
                'object_rotation_angle': self.object_rotation_angle,
                'enable_pulsing': self.enable_pulsing,
                'enable_trails': self.enable_trails,
            }
            
            # 启动导出
            self.export_manager.start_gif_export(
                filename=filename,
                layers=self.layers,
                num_slices=self.num_slices,
                symmetry_mode=self.symmetry_mode,
                dynamics_params=dynamics_params,
                duration=3,         
                rotation_cycles=0.1
            )

        self.export_window = None
        self.ui_manager.set_focus_set(None)

    def _draw_export_status(self):
        message, progress = self.export_manager.get_status()
        if not message: return
        text_surf = self.status_font.render(message, True, config.STATUS_TEXT_COLOR)
        text_rect = text_surf.get_rect(center=(config.DRAW_AREA_WIDTH // 2, 40))
        bg_rect = text_rect.inflate(20,20)
        s = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        s.fill((0,0,0,180))
        self.screen.blit(s, bg_rect.topleft)
        self.screen.blit(text_surf, text_rect)
        if self.export_manager.state == "rendering_gif" or self.export_manager.state == "saving_gif":
            bar_rect = pygame.Rect(0,0, bg_rect.width - 20, 10)
            bar_rect.center = (bg_rect.centerx, bg_rect.bottom + 10)
            pygame.draw.rect(self.screen, (80,80,80), bar_rect, border_radius=3)
            progress_width = bar_rect.width * progress
            pygame.draw.rect(self.screen, (100,200,100), (bar_rect.left, bar_rect.top, progress_width, bar_rect.height), border_radius=3)

    def _action_finish_drawing(self):
        if not self.user_path:
            return
        
        active_layer = self.layers[self.active_layer_index]
        
        # 创建一个包含完整绘制路径的副本，以便撤销/重做
        path_to_add = list(self.user_path)
        brush_type_to_add = self.brush_type
        
        # 定义一个绘制函数，以便在执行和撤销时使用
        def draw_path(surface, path, brush_type):
            for i, point in enumerate(path):
                start_color = self.start_color
                end_color = self.end_color
                t = i / len(path) if len(path) > 1 else 1.0
                color = utils.lerp_color(start_color, end_color, t)
                
                if brush_type == 'Line':
                    if i > 0:
                        pygame.draw.line(surface, color, path[i-1]['pos'], point['pos'], int(point['size']))
                elif brush_type == 'Circle':
                    pygame.draw.circle(surface, color, point['pos'], int(point['size']))
                elif brush_type == 'Spray':
                    for _ in range(10): # 喷射密度
                        offset_x = random.randint(-int(point['size']*2), int(point['size']*2))
                        offset_y = random.randint(-int(point['size']*2), int(point['size']*2))
                        spray_pos = (point['pos'][0] + offset_x, point['pos'][1] + offset_y)
                        pygame.draw.circle(surface, color, spray_pos, 1)

        # 创建一个 AddPixelAction 来记录这次绘制
        action = AddPixelAction(active_layer, path_to_add, brush_type_to_add, draw_path)
        self.history_manager.execute_action(action)
        # 重置绘制状态
        self.is_drawing = False
        self.user_path.clear()

    def _action_place_shape(self, pos):
        active_layer = self.layers[self.active_layer_index]
        if self.selected_shape:
            # 如果有选中的形状，修改其位置
            self._action_modify_selected_shape({'pos': pos})
        else:
            # 否则创建新形状
            color = self.start_color if self.active_tool == 'triangle' else self.end_color
            if self.active_tool == 'triangle': shape = Triangle(pos, 1, color)
            elif self.active_tool == 'star': shape = Star(pos, 1, color)
            else: return # 不支持的形状类型
            
            action = AddShapeAction(active_layer, shape)
            self.history_manager.execute_action(action)