# drawing.py
from config import CENTER_X, CENTER_Y, GUIDE_LINE_COLOR, DRAW_AREA_WIDTH
import random
import pygame
import math

def draw_dashed_line(surface, color, start_pos, end_pos, dash_length=10, gap_length=5):
    """在两点之间绘制一条虚线。"""
    start_vec = pygame.Vector2(start_pos)
    end_vec = pygame.Vector2(end_pos)
    direction = (end_vec - start_vec)
    distance = direction.length()
    direction.normalize_ip()
    
    current_pos = start_vec
    current_distance = 0
    
    while current_distance < distance:
        dash_end_pos = current_pos + direction * dash_length
        if (dash_end_pos - start_vec).length() > distance:
            dash_end_pos = end_vec
        
        pygame.draw.line(surface, color, current_pos, dash_end_pos, 1)
        
        current_pos += direction * (dash_length + gap_length)
        current_distance += dash_length + gap_length

def draw_guide_lines(surface, num_slices):
    """在给定的surface上从中心绘制辐射状的引导线。"""
    if num_slices <= 0:
        return
        
    slice_angle_rad = 2 * math.pi / num_slices
    
    for i in range(num_slices):
        angle = i * slice_angle_rad
        
        # 计算从中心点到画布边缘的终点
        end_x = CENTER_X + DRAW_AREA_WIDTH * math.cos(angle)
        end_y = CENTER_Y + DRAW_AREA_WIDTH * math.sin(angle)
        
        draw_dashed_line(surface, GUIDE_LINE_COLOR, (CENTER_X, CENTER_Y), (end_x, end_y))

def draw_on_surface(surface, elements, num_slices, symmetry_mode, global_rotation_angle, pulsing_scale):
    """
    Draws a list of elements onto a surface with specified symmetry.
    as it's applied globally later in get_composite_image.
    """
    slice_angle = 360 / num_slices
    
    for element in elements:
        pos = pygame.Vector2(element['pos'])
        size = element['size']
        color = element['color']
        brush_type = element['type']

        # Center the drawing coordinates
        pos.x -= CENTER_X
        pos.y -= CENTER_Y
        
        # Apply pulsing scale
        pos *= pulsing_scale

        for i in range(num_slices):
            rotated_pos = pos.rotate(i * slice_angle)
            
            # For kaleidoscope mode, reflect every other slice
            if symmetry_mode == 'Kaleidoscope' and i % 2 == 1:
                rotated_pos = pos.rotate(i * slice_angle)
                rotated_pos.y = -rotated_pos.y # Reflect across the slice's central axis
            else:
                rotated_pos = pos.rotate(i * slice_angle)

            # Convert back to screen coordinates
            draw_pos = (int(rotated_pos.x + CENTER_X), int(rotated_pos.y + CENTER_Y))

            if brush_type == 'Circle':
                pygame.draw.circle(surface, color, draw_pos, int(size))
            elif brush_type == 'Spray':
                for _ in range(10):
                    offset_x = random.randint(-size, size)
                    offset_y = random.randint(-size, size)
                    if offset_x**2 + offset_y**2 < size**2:
                        pygame.draw.circle(surface, color, (draw_pos[0] + offset_x, draw_pos[1] + offset_y), 1)

def get_composite_image(layers, apply_dynamics=False, angle=0, scale=1.0, dynamics_params=None):
    from config import DRAW_AREA_WIDTH, SCREEN_HEIGHT, CENTER_X, CENTER_Y
    composite = pygame.Surface((DRAW_AREA_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    
    if dynamics_params is None:
        dynamics_params = {'angle': angle, 'scale': scale}
    
    current_angle = dynamics_params.get('angle', 0)
    current_scale = dynamics_params.get('scale', 1.0)

    for layer in reversed(layers):
        if layer.is_visible:
            if apply_dynamics:
                transformed_layer = pygame.transform.rotozoom(layer.surface, math.degrees(-current_angle), current_scale)
                rect = transformed_layer.get_rect(center=(CENTER_X, CENTER_Y))
                composite.blit(transformed_layer, rect)
            else:
                composite.blit(layer.surface, (0,0))
    return composite