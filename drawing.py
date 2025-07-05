# drawing.py
import pygame
import math
import random
from config import CENTER_X, CENTER_Y, DRAW_AREA_WIDTH, GUIDE_LINE_COLOR

def draw_dashed_line(surface, color, start_pos, end_pos, dash_length=10, gap_length=5):
    """在两点之间绘制一条虚线。"""
    start_vec = pygame.Vector2(start_pos)
    end_vec = pygame.Vector2(end_pos)
    direction = (end_vec - start_vec)
    distance = direction.length()
    if distance == 0: return
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

        # 将坐标原点移至画布中心
        pos.x -= CENTER_X
        pos.y -= CENTER_Y
        
        # 应用脉冲缩放
        pos *= pulsing_scale

        for i in range(num_slices):
            rotated_pos = pos.rotate(i * slice_angle)
            
            # 万花筒模式下，对奇数切片进行镜像反射
            if symmetry_mode == 'Kaleidoscope' and i % 2 == 1:
                rotated_pos.y = -rotated_pos.y
            
            # 将坐标转换回屏幕坐标
            draw_pos = (int(rotated_pos.x + CENTER_X), int(rotated_pos.y + CENTER_Y))

            if brush_type == 'Circle':
                pygame.draw.circle(surface, color, draw_pos, int(size))
            elif brush_type == 'Spray':
                for _ in range(10):
                    offset_x = random.randint(-size, size)
                    offset_y = random.randint(-size, size)
                    if offset_x**2 + offset_y**2 < size**2:
                        pygame.draw.circle(surface, color, (draw_pos[0] + offset_x, draw_pos[1] + offset_y), 1)

def get_composite_image(layers, apply_dynamics=False, angle=0, scale=1.0):
    """
    合成所有图层，并应用全局动态效果（旋转和缩放）。
    """
    if not layers:
        return pygame.Surface((DRAW_AREA_WIDTH, 800), pygame.SRCALPHA)

    base_surface = layers[0].surface.copy()
    for layer in layers[1:]:
        base_surface.blit(layer.surface, (0, 0))

    if not apply_dynamics:
        return base_surface

    # 应用全局旋转和缩放
    final_surface = base_surface
    if scale != 1.0:
        original_size = final_surface.get_size()
        scaled_size = (int(original_size[0] * scale), int(original_size[1] * scale))
        final_surface = pygame.transform.scale(final_surface, scaled_size)
    
    if angle != 0:
        final_surface = pygame.transform.rotate(final_surface, -angle) # Pygame的旋转是逆时针的

    # 创建一个正确尺寸的画布，将旋转/缩放后的图像居中放置
    final_canvas = pygame.Surface((DRAW_AREA_WIDTH, 800), pygame.SRCALPHA)
    final_rect = final_surface.get_rect(center=(CENTER_X, 400))
    final_canvas.blit(final_surface, final_rect)
    
    return final_canvas