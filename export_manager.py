# export_manager.py
import pygame
import imageio
import numpy as np
import os
import math

import drawing
import config

class ExportManager:
    def __init__(self):
        self.state = "idle"  # "idle", "rendering_gif", "saving_gif", "finished", "failed"
        self.filename = ""
        self.progress = 0.0
        self.gif_frames = []
        self.status_timer = 0
        
        # Parameters for GIF generation
        self.layers_to_render = []
        self.dynamics_params = {}
        self.total_frames = 0
        self.fps = 24

    def start_png_export(self, filename, image_surface):
        """Starts a simple, blocking PNG export."""
        try:
            save_path = os.path.join(config.EXPORTS_DIR, f"{filename}.png")
            pygame.image.save(image_surface, save_path)
            print(f"Image saved to {save_path}")
            self.state = "finished"
        except Exception as e:
            print(f"[EXPORT PNG ERROR] {e}")
            self.state = "failed"
        self.status_timer = 3000 # Show status for 3 seconds

    def start_gif_export(self, filename, layers, **dynamics_params):
        """Initializes the non-blocking GIF export process."""
        self.state = "rendering_gif"
        self.filename = filename
        self.progress = 0
        self.gif_frames.clear()
        
        self.layers_to_render = [layer.surface.copy() for layer in layers] # Take a snapshot of layers
        self.dynamics_params = dynamics_params
        self.total_frames = 5 * self.fps # 5 seconds animation
        print("Starting GIF frame rendering...")

    def update(self):
        """This method should be called every frame from the main loop."""
        if self.state == "rendering_gif":
            self._render_one_gif_frame()
        elif self.state == "saving_gif":
            self._save_gif_file()

    def _render_one_gif_frame(self):
        if self.progress < self.total_frames:
            # Calculate dynamics for the current frame
            dynamics = self.dynamics_params.copy()
            angle = dynamics.get('angle', 0)
            scale = dynamics.get('scale', 1.0)
            enable_rotation = dynamics.get('enable_rotation', False)
            enable_pulsing = dynamics.get('enable_pulsing', False)

            current_angle = angle + (0.01 * self.progress) if enable_rotation else angle
            current_scale = 1.0 + 0.05 * math.sin(self.progress / self.fps * math.pi) if enable_pulsing else 1.0

            # Create a fake Layer list with copied surfaces for rendering
            fake_layers = [type('obj', (object,), {'surface': s, 'is_visible': True})() for s in self.layers_to_render]
            
            frame_surface = drawing.get_composite_image(
                fake_layers, 
                apply_dynamics=True, 
                angle=current_angle, 
                scale=current_scale
            )
            
            # Convert and store the frame
            frame_data = pygame.surfarray.array3d(frame_surface)
            frame_data = np.transpose(frame_data, (1, 0, 2))
            self.gif_frames.append(frame_data)
            self.progress += 1
        else:
            print("Frame rendering complete. Starting file save...")
            self.state = "saving_gif"

    def _save_gif_file(self):
        try:
            save_path = os.path.join(config.EXPORTS_DIR, f"{self.filename}.gif")
            imageio.mimsave(save_path, self.gif_frames, fps=self.fps, loop=0)
            print(f"Animation saved to {save_path}")
            self.state = "finished"
        except Exception as e:
            print(f"[SAVE GIF ERROR] {e}")
            self.state = "failed"
        self.gif_frames.clear() # Free up memory
        self.status_timer = 3000

    def get_status_message(self):
        if self.state == "rendering_gif":
            return f"Generating GIF... {int((self.progress / self.total_frames) * 100)}%"
        elif self.state == "saving_gif":
            return "Saving GIF file..."
        elif self.state == "finished":
            return "Export Complete!"
        elif self.state == "failed":
            return "Export Failed! (Check Console)"
        return ""

    def is_active(self):
        return self.state not in ["idle", "finished", "failed"]