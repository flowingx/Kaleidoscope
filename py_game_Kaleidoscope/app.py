# filepath: f:\X_code\Projects\25_summer_python\py_game_Kaleidoscope\app.py
"""
主应用程序类。
负责管理游戏循环、事件处理、状态更新和屏幕绘制。
这是整个项目的核心协调器。
"""
from collections import deque
import pygame
import config
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
        self.user_path, self.is_drawing = None, False
        self.elements_to_animate = []
        self.is_animating, self.skip_animation = False, False
        self.animation_index, self.animation_delay, self.last_animation_time = 0, 0, 0
        
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
        self.num_slices = 4
        self.symmetry_mode = 'Kaleidoscope'
        self.start_color, self.end_color = (255, 0, 0), (0, 0, 255)
        self.active_color_selection = 'start'
        
        # 动态效果状态
        self.enable_global_rotation, self.global_rotation_angle = False, 0.0
        self.enable_object_rotation, self.object_rotation_angle = False, 0.0
        self.enable_pulsing, self.pulsing_scale = False, 1.0
        self.enable_trails, self.trail_frames = False, []
        self.guide_line_slices = 0

        # 图层管理
        self.layers = [Layer(name="Background")]
        self.active_layer_index = 0
        
        # --- 管理器 ---
        self.export_manager = ExportManager()
        self.export_window = None
        self.history_manager = HistoryManager(self)

    def run(self):
        """主循环，处理事件和更新状态。"""
        while self.is_running:
            time_delta_seconds = self.clock.tick(config.FPS) / 1000.0
            self._handle_events()
            self._update(time_delta_seconds)
            self._draw()

    def _handle_events(self):
        """处理所有事件。"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            # 处理其他事件...

    def _update(self, time_delta_seconds):
        """更新应用程序状态。"""
        # 更新逻辑...

    def _draw(self):
        """绘制所有内容到屏幕。"""
        self.screen.fill(config.BACKGROUND_COLOR)
        # 绘制逻辑...
        pygame.display.flip()

    # --- Tool and Action Methods ---
    def _set_active_tool(self, tool_name):
        """设置当前活动工具并更新UI。"""
        self.active_tool = tool_name
        # 更新工具箱按钮图标...

    # --- Slider for Slices ---
    def _update_slice_count(self, value):
        """更新切片数量，确保为偶数。"""
        self.num_slices = max(4, min(16, value)) if value % 2 == 0 else value - 1 if value > 4 else 4