"""
管理 PNG 和 GIF 文件的导出过程。
这是一个状态机，负责在后台逐帧渲染动画并最终保存文件。
"""
import pygame
import imageio
import numpy as np
import os
import math
from collections import deque
import drawing
import config

class ExportManager:
    """
    处理所有导出逻辑，包括状态管理、逐帧渲染和文件保存。
    """
    def __init__(self):
        self.state = "idle"
        self.filename = ""
        self.progress = 0.0
        self.gif_frames = []
        self.status_timer = 0
        
        self.layers_to_render = []
        self.num_slices = 12
        self.symmetry_mode = 'Kaleidoscope'
        self.dynamics_params = {}
        self.total_frames = 0
        self.fps = 30
        self.trail_frames_for_gif = deque(maxlen=15)
        
    def start_png_export(self, filename, image_surface):
        """启动单张 PNG 图片的导出。"""
        self.state = "exporting_png"
        try:
            save_path = os.path.join(config.EXPORTS_DIR, f"{filename}.png")
            pygame.image.save(image_surface, save_path)
            print(f"Image saved to {save_path}")
            self.state = "finished"
        except Exception as e:
            print(f"[EXPORT PNG ERROR] {e}")
            self.state = "failed"
        self.status_timer = 3000

    def cancel_export(self):
        """当用户取消导出时调用此方法。"""
        if self.state != 'idle':
            print("Export cancelled by user.")
            self.state = 'idle'
            self.status_timer = 0

    def start_gif_export(self, filename, layers, num_slices, symmetry_mode, dynamics_params, duration=5, rotation_cycles=0.5):
        """
        启动 GIF 动画的导出过程。
        它会存储所有必要的渲染参数，并准备开始逐帧渲染。
        """
        if self.state != 'idle':
            print("Cannot start new export while another is in progress.")
            return
            
        self.state = "rendering_gif"
        self.filename = filename
        self.progress = 0
        self.gif_frames.clear()
        self.trail_frames_for_gif.clear()
        
        self.layers_to_render = layers
        self.num_slices = num_slices
        self.symmetry_mode = symmetry_mode
        self.dynamics_params = dynamics_params
        self.total_frames = int(duration * self.fps)
        
        print(f"Starting GIF frame rendering ({self.total_frames} frames)...")

    def update(self):
        """在主循环中调用，以驱动 GIF 帧的渲染。"""
        if self.state == "rendering_gif":
            self._render_one_gif_frame()
        
    def _render_one_gif_frame(self):
        """
        渲染 GIF 动画的单帧。
        此方法模拟 App 的主绘制循环，计算当前帧的动态效果并渲染图像。
        """
        if self.progress >= self.total_frames:
            print("Frame rendering complete. Starting file save...")
            self.state = "saving_gif"
            self._save_gif_file()
            return

        frame_progress_ratio = self.progress / self.total_frames
        
        cycles = self.dynamics_params.get('rotation_cycles', 0.5)
        total_rotation_angle = 360 * cycles

        current_global_angle = self.dynamics_params.get('global_rotation_angle', 0.0)
        if self.dynamics_params.get('enable_global_rotation'):
            current_global_angle -= (total_rotation_angle * frame_progress_ratio)

        current_object_angle = self.dynamics_params.get('object_rotation_angle', 0.0)
        if self.dynamics_params.get('enable_object_rotation'):
            current_object_angle += (total_rotation_angle * frame_progress_ratio)

        current_pulsing_scale = 1.0
        if self.dynamics_params.get('enable_pulsing'):
            current_pulsing_scale = 1.0 + 0.05 * math.sin(frame_progress_ratio * 2 * math.pi * 3)

        composite_image = drawing.get_composite_image(self.layers_to_render, self.num_slices, self.symmetry_mode, current_object_angle)
        
        if self.dynamics_params.get('enable_trails'):
            trail_copy = composite_image.copy()
            alpha = int(255 * (0.85 ** (len(self.trail_frames_for_gif) + 1)))
            self.trail_frames_for_gif.append((trail_copy, alpha))
        
        frame_surface = drawing.apply_global_dynamics(composite_image, current_global_angle, current_pulsing_scale, self.trail_frames_for_gif)
        background_color = self.dynamics_params.get('background_color')
        if background_color is not None:
            background_surface = pygame.Surface(frame_surface.get_size())
            background_surface.fill(background_color)
            background_surface.blit(frame_surface, (0, 0))
            frame_surface = background_surface
        
        frame_data = pygame.surfarray.array3d(frame_surface)
        frame_data = np.transpose(frame_data, (1, 0, 2))
        self.gif_frames.append(frame_data)
        self.progress += 1

    def _save_gif_file(self):
        """使用 imageio 库将所有渲染好的帧保存为 GIF 文件。"""
        try:
            save_path = os.path.join(config.EXPORTS_DIR, f"{self.filename}.gif")
            imageio.mimsave(save_path, self.gif_frames, fps=self.fps, loop=0, **{"quantizer": "nq"})
            print(f"Animation saved to {save_path}")
            self.state = "finished"
        except Exception as e:
            print(f"[SAVE GIF ERROR] {e}")
            self.state = "failed"
        self.gif_frames.clear()
        self.status_timer = 3000

    def get_status(self):
        """返回当前的导出状态和进度，用于在 UI 中显示。"""
        if self.state == "rendering_gif":
            progress_percent = (self.progress / self.total_frames) if self.total_frames > 0 else 0
            return f"Generating GIF... {int(progress_percent * 100)}%", progress_percent
        elif self.state == "saving_gif":
            return "Saving GIF file...", 1.0
        elif self.state == "finished":
            return "Export Complete!", 1.0
        elif self.state == "failed":
            return "Export Failed! (Check Console)", 1.0
        return None, 0.0

    def is_active(self):
        """检查当前是否有导出任务正在进行。"""
        return self.state not in ["idle", "finished", "failed"]

    def update_timer(self, time_delta_ms):
        """更新状态消息的计时器，使其在完成后能自动消失。"""
        if self.state in ["finished", "failed"]:
            self.status_timer -= time_delta_ms
            if self.status_timer <= 0:
                self.state = "idle"
