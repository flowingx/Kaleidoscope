# app.py
import pygame, math, datetime, pygame_gui
import config, utils, drawing
from layer import Layer
from ui_handler import UIHandler
from export_manager import ExportManager
from history_manager import HistoryManager, AddLayerAction, DeleteLayerAction, ClearAllAction

class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption("Kaleidoscope - Global Undo/Redo")
        self.clock = pygame.time.Clock()
        self.is_running = True
        self.num_slices, self.symmetry_mode, self.brush_type = 12, 'Kaleidoscope', 'Line'
        self.brush_size = 1.0
        self.enable_rotation, self.enable_pulsing, self.global_rotation_angle, self.pulsing_scale = False, False, 0.0, 1.0
        self.start_color, self.end_color = (255, 0, 255), (0, 255, 255)
        self.active_color_selection = 'start'
        self.layers = [Layer((config.DRAW_AREA_WIDTH, config.SCREEN_HEIGHT), name="Background")]
        self.active_layer_index = 0
        self.user_path, self.elements_to_animate, self.is_drawing = [], [], False
        self.is_animating, self.skip_animation = False, False
        self.animation_index, self.animation_delay, self.last_animation_time = 0, 1, 0
        self.export_manager = ExportManager()
        self.export_window = None
        self.history_manager = HistoryManager(self)
        try:
            self.ui_manager = pygame_gui.UIManager((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), config.THEME_PATH)
        except (FileNotFoundError, pygame.error):
            print("Warning: theme.json not found."); self.ui_manager = pygame_gui.UIManager((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.ui_handler = UIHandler(self.ui_manager)
        self._initialize_ui_state()
        self.start_color_rect = pygame.Rect(config.DRAW_AREA_WIDTH + 10, 390, 95, 40)
        self.end_color_rect = pygame.Rect(config.DRAW_AREA_WIDTH + 115, 390, 95, 40)
        self.spectrum_rect = pygame.Rect(config.DRAW_AREA_WIDTH + 10, 440, 200, 150)
        self.spectrum_surface = utils.create_color_spectrum(pygame.Rect(0,0,self.spectrum_rect.width, self.spectrum_rect.height))
        self.brush_preview_pos = (config.DRAW_AREA_WIDTH + config.UI_PANEL_WIDTH - 45, 295)
        self.brush_preview_max_radius = 15
        self.status_font = pygame.font.Font(None, 40)

    def _initialize_ui_state(self):
        # ... (same as before)
        self.ui_handler.elements['slice_input'].set_text(str(self.num_slices))
        self.ui_handler.elements['kaleido_btn'].select()
        initial_slider_value = 5
        self.ui_handler.elements['brush_size_slider'].set_current_value(initial_slider_value)
        self.brush_size = self._calculate_and_update_brush_size(initial_slider_value)
        self._update_layer_list_ui()


    def _calculate_and_update_brush_size(self, slider_value):
        # ... (same as before)
        min_ui_val, max_ui_val = 1, 15; normalized_value = (slider_value - min_ui_val) / (max_ui_val - min_ui_val)
        exponent = 2.0; eased_value = math.pow(normalized_value, exponent)
        target_min_size, target_max_size = 1, 10
        final_brush_size = target_min_size + eased_value * (target_max_size - target_min_size)
        value_text = f"{final_brush_size:.1f}"; self.ui_handler.elements['brush_size_value_label'].set_text(value_text)
        return final_brush_size


    def _update_layer_list_ui(self):
        # ... (same as before)
        if 'layer_list' in self.ui_handler.elements and self.ui_handler.elements['layer_list'] is not None:
            old_list_rect = self.ui_handler.elements['layer_list'].relative_rect
            container = self.ui_handler.elements['layer_list'].ui_container; self.ui_handler.elements['layer_list'].kill()
        else:
            old_list_rect = pygame.Rect(10, 30, 160, config.SCREEN_HEIGHT - 80)
            for element in self.ui_manager.get_root_container().elements:
                if isinstance(element, pygame_gui.elements.UIPanel) and element.relative_rect.left > config.DRAW_AREA_WIDTH: container = element; break
        item_list = [l.name for l in self.layers]
        selected_item = self.layers[self.active_layer_index].name if self.layers and self.active_layer_index < len(self.layers) else None
        self.ui_handler.elements['layer_list'] = pygame_gui.elements.UISelectionList(
            relative_rect=old_list_rect, item_list=item_list, manager=self.ui_manager, container=container)
        if selected_item and selected_item in item_list:
            try: self.ui_handler.elements['layer_list'].set_selection(selected_item)
            except AttributeError:
                try: self.ui_handler.elements['layer_list'].set_single_selection(selected_item)
                except AttributeError: pass
    
    def run(self):
        while self.is_running:
            time_delta_ms = self.clock.tick(config.FPS); time_delta_seconds = time_delta_ms / 1000.0
            self._handle_events(); self._update(time_delta_seconds, time_delta_ms); self._draw()

    def _handle_events(self):
        # ... (same as before)
        is_input_blocked = self.export_manager.is_active() or self.export_window is not None
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.is_running = False
            if not is_input_blocked: self._handle_drawing_events(event)
            self._handle_gui_events(event)
            self.ui_manager.process_events(event)


    def _handle_drawing_events(self, event):
        # ... (same as before)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if pygame.Rect(0, 0, config.DRAW_AREA_WIDTH, config.SCREEN_HEIGHT).collidepoint(event.pos):
                self.is_drawing = True; self.user_path = [{'pos': event.pos, 'size': self.brush_size}]
            elif self.start_color_rect.collidepoint(event.pos): self.active_color_selection = 'start'
            elif self.end_color_rect.collidepoint(event.pos): self.active_color_selection = 'end'
            elif self.spectrum_rect.collidepoint(event.pos):
                picked_color = self.spectrum_surface.get_at((event.pos[0] - self.spectrum_rect.left, event.pos[1] - self.spectrum_rect.top))
                if self.active_color_selection == 'start': self.start_color = picked_color
                else: self.end_color = picked_color
        if event.type == pygame.MOUSEMOTION and self.is_drawing:
            if pygame.Rect(0, 0, config.DRAW_AREA_WIDTH, config.SCREEN_HEIGHT).collidepoint(event.pos):
                self.user_path.append({'pos': event.pos, 'size': self.brush_size})
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1: self.is_drawing = False


    def _handle_gui_events(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            ui_element = event.ui_element
            if ui_element == self.ui_handler.elements['generate_btn']: self._action_generate()
            elif ui_element == self.ui_handler.elements['clear_all_btn']: self._action_clear_all()
            elif ui_element == self.ui_handler.elements['undo_btn']: self.history_manager.undo()
            elif ui_element == self.ui_handler.elements['redo_btn']: self.history_manager.redo()
            elif ui_element == self.ui_handler.elements['skip_animation_btn']: self.skip_animation = True
            elif ui_element == self.ui_handler.elements['delete_layer_btn']: self._action_delete_layer()
            elif ui_element == self.ui_handler.elements['kaleido_btn']: self.symmetry_mode = 'Kaleidoscope'; ui_element.select(); self.ui_handler.elements['rotate_btn'].unselect()
            elif ui_element == self.ui_handler.elements['rotate_btn']: self.symmetry_mode = 'Rotation Only'; ui_element.select(); self.ui_handler.elements['kaleido_btn'].unselect()
            elif ui_element == self.ui_handler.elements['rotate_toggle']: self.enable_rotation = not self.enable_rotation; ui_element.select() if self.enable_rotation else ui_element.unselect()
            elif ui_element == self.ui_handler.elements['pulse_toggle']: self.enable_pulsing = not self.enable_pulsing; ui_element.select() if self.enable_pulsing else ui_element.unselect()
            elif ui_element == self.ui_handler.elements['export_btn'] and self.export_window is None: self._action_open_export_dialog()
        if event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED and event.ui_element == self.export_window: self._action_start_export()
        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED and event.ui_element == self.ui_handler.elements['brush_dropdown']: self.brush_type = event.text
        if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED and event.ui_element == self.ui_handler.elements['brush_size_slider']:
            self.brush_size = self._calculate_and_update_brush_size(event.value)
        if event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED and event.ui_element == self.ui_handler.elements['slice_input']:
            try: self.num_slices = max(2, min(60, int(event.text)))
            except ValueError: pass
            self.ui_handler.elements['slice_input'].set_text(str(self.num_slices))
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION and event.ui_element == self.ui_handler.elements['layer_list']:
            for i, layer in enumerate(self.layers):
                if layer.name == event.text: self.active_layer_index = i; break

    def _update(self, time_delta_seconds, time_delta_ms):
        self.ui_manager.update(time_delta_seconds)
        if self.enable_rotation: self.global_rotation_angle += 0.001
        if self.enable_pulsing: self.pulsing_scale = 1.0 + 0.05 * math.sin(pygame.time.get_ticks() * 0.002)
        else: self.pulsing_scale = 1.0
        
        # UI Visibility Logic
        if self.is_animating:
            self.ui_handler.elements['generate_btn'].hide(); self.ui_handler.elements['skip_animation_btn'].show()
        else:
            self.ui_handler.elements['generate_btn'].show(); self.ui_handler.elements['skip_animation_btn'].hide()
        
        if self.history_manager.can_undo(): self.ui_handler.elements['undo_btn'].show()
        else: self.ui_handler.elements['undo_btn'].hide()
        
        if self.history_manager.can_redo(): self.ui_handler.elements['redo_btn'].show()
        else: self.ui_handler.elements['redo_btn'].hide()

        # Animation Logic
        if self.is_animating:
            if self.skip_animation:
                self._finish_current_animation(); self.skip_animation = False
            else:
                current_time = pygame.time.get_ticks()
                if current_time - self.last_animation_time > self.animation_delay:
                    self.last_animation_time = current_time
                    if self.animation_index < len(self.elements_to_animate):
                        element_to_draw = self.elements_to_animate[self.animation_index]
                        element_to_draw['size'] = int(element_to_draw['size'])
                        drawing.draw_on_surface(self.layers[0].surface, [element_to_draw], self.num_slices, self.symmetry_mode, 0, 1.0)
                        self.animation_index += 1
                    else: self.is_animating = False
        
        self.export_manager.update(); self.export_manager.update_timer(time_delta_ms)

    def _draw(self):
        # ... (same as before)
        self.screen.fill(config.BACKGROUND_COLOR)
        composite_image = drawing.get_composite_image(self.layers, apply_dynamics=True, angle=self.global_rotation_angle, scale=self.pulsing_scale)
        self.screen.blit(composite_image, (0, 0))
        if len(self.user_path) > 1:
            if self.brush_type == 'Line': pygame.draw.lines(self.screen, config.PREVIEW_LINE_COLOR, False, [p['pos'] for p in self.user_path], 2)
            else:
                for p in self.user_path: pygame.draw.circle(self.screen, config.PREVIEW_LINE_COLOR, p['pos'], int(p['size']/2)+1, 1)
        self.ui_manager.draw_ui(self.screen)
        pygame.draw.rect(self.screen, self.start_color, self.start_color_rect); pygame.draw.rect(self.screen, self.end_color, self.end_color_rect)
        if self.active_color_selection == 'start': pygame.draw.rect(self.screen, config.WHITE, self.start_color_rect, 2)
        else: pygame.draw.rect(self.screen, config.WHITE, self.end_color_rect, 2)
        self.screen.blit(self.spectrum_surface, self.spectrum_rect.topleft)
        current_radius = 1 + ((self.brush_size - 1) / (10 - 1)) * (self.brush_preview_max_radius - 1)
        pygame.draw.circle(self.screen, config.WHITE, self.brush_preview_pos, max(1, int(current_radius)))
        self._draw_export_status()
        pygame.display.flip()

    def _finish_current_animation(self):
        if not self.is_animating or not self.elements_to_animate: return
        remaining_elements = self.elements_to_animate[self.animation_index:]
        for element_to_draw in remaining_elements:
            element_to_draw['size'] = int(element_to_draw['size'])
            drawing.draw_on_surface(self.layers[0].surface, [element_to_draw], self.num_slices, self.symmetry_mode, 0, 1.0)
        self.is_animating = False; self.animation_index = 0
        self.elements_to_animate.clear()

    def _action_generate(self):
        if self.is_animating: self._finish_current_animation()
        if len(self.user_path) > 1:
            self.is_drawing = False
            new_layer = Layer((config.DRAW_AREA_WIDTH, config.SCREEN_HEIGHT))
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
                        step_t = j / steps; pos = pygame.Vector2(p1['pos']).lerp(p2['pos'], step_t)
                        size = p1['size'] * (1-step_t) + p2['size'] * step_t
                        color_t = (current_dist + dist * step_t) / total_dist; color = utils.lerp_color(self.start_color, self.end_color, color_t)
                        self.elements_to_animate.append({'pos': pos, 'color': color, 'size': size, 'type': 'Circle' if self.brush_type == 'Line' else self.brush_type})
                    current_dist += dist
            self.user_path.clear()

    def _action_clear_all(self):
        if self.is_animating: self._finish_current_animation()
        self.is_drawing = False; self.user_path.clear()
        if len(self.layers) > 1:
            cleared = self.layers[:-1]
            action = ClearAllAction(self, cleared)
            self.history_manager.execute_action(action)
    
    def _action_delete_layer(self):
        if len(self.layers) > 1 and self.layers[self.active_layer_index].name != "Background":
            layer_to_delete = self.layers[self.active_layer_index]
            index = self.active_layer_index
            action = DeleteLayerAction(self, layer_to_delete, index)
            self.history_manager.execute_action(action)
            
    def _action_open_export_dialog(self):
        # ... (same as before)
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
        # ... (same as before)
        filename = self.export_window.filename_input.get_text()
        file_format = self.export_window.format_dropdown.selected_option
        if file_format == 'PNG (Image)':
            image_to_save = drawing.get_composite_image(self.layers, apply_dynamics=True, angle=self.global_rotation_angle, scale=self.pulsing_scale)
            self.export_manager.start_png_export(filename, image_to_save)
        elif file_format == 'GIF (Animation)':
            dynamics_params = { 'angle': self.global_rotation_angle, 'enable_rotation': self.enable_rotation, 'enable_pulsing': self.enable_pulsing }
            self.export_manager.start_gif_export(filename, self.layers, **dynamics_params)
        self.export_window = None

    def _draw_export_status(self):
        # ... (same as before)
        message, progress = self.export_manager.get_status()
        if not message: return
        text_surf = self.status_font.render(message, True, config.STATUS_TEXT_COLOR)
        text_rect = text_surf.get_rect(center=(config.DRAW_AREA_WIDTH // 2, 40))
        bg_rect = text_rect.inflate(20,20)
        pygame.draw.rect(self.screen, (0,0,0,180), bg_rect, border_radius=5)
        self.screen.blit(text_surf, text_rect)
        if self.export_manager.state == "rendering_gif" or self.export_manager.state == "saving_gif":
            bar_rect = pygame.Rect(0,0, bg_rect.width - 20, 10)
            bar_rect.center = (bg_rect.centerx, bg_rect.bottom + 10)
            pygame.draw.rect(self.screen, (80,80,80), bar_rect, border_radius=3)
            progress_width = bar_rect.width * progress
            pygame.draw.rect(self.screen, (100,200,100), (bar_rect.left, bar_rect.top, progress_width, bar_rect.height), border_radius=3)