"""
包含所有核心的绘图和渲染函数。
负责处理对称性渲染、动态效果（旋转、轨迹等）和辅助线绘制。
"""
import pygame
import math
from config import CENTER_X, CENTER_Y, DRAW_AREA_WIDTH, GUIDE_LINE_COLOR

def draw_dashed_line(surface, color, start_pos, end_pos, dash_length=10, gap_length=5):
    """在两个点之间绘制一条虚线。"""
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
        if (dash_end_pos - start_vec).length() > distance: dash_end_pos = end_vec
        pygame.draw.line(surface, color, current_pos, dash_end_pos, 1)
        current_pos += direction * (dash_length + gap_length)
        current_distance += dash_length + gap_length

def draw_guide_lines(surface, num_slices, color=GUIDE_LINE_COLOR):
    """根据切片数绘制万花筒的辅助参考线。"""
    if num_slices <= 0: return
    slice_angle_rad = 2 * math.pi / num_slices
    for i in range(num_slices):
        angle = i * slice_angle_rad
        end_x = CENTER_X + DRAW_AREA_WIDTH * math.cos(angle)
        end_y = CENTER_Y + DRAW_AREA_WIDTH * math.sin(angle)
        draw_dashed_line(surface, color, (CENTER_X, CENTER_Y), (end_x, end_y))

def draw_on_surface(surface, elements, num_slices, symmetry_mode):
    """
    根据对称性在表面上绘制已生成的像素笔刷元素。
    只负责绘制，不负责生成效果。
    """
    slice_angle = 360 / num_slices
    for element in elements:
        if element['type'] == 'Circle':
            pos = pygame.Vector2(element['pos']) - (CENTER_X, CENTER_Y)
            for i in range(num_slices):
                rotated_pos = pos.rotate(i * slice_angle)
                if symmetry_mode == 'Kaleidoscope' and i % 2 == 1:
                    rotated_pos.y = -rotated_pos.y
                draw_pos = (int(rotated_pos.x + CENTER_X), int(rotated_pos.y + CENTER_Y))
                pygame.draw.circle(surface, element['color'], draw_pos, int(element['size']))
        elif element['type'] == 'Spray':
            for spray_point in element['points']:
                pos = pygame.Vector2(spray_point) - (CENTER_X, CENTER_Y)
                for i in range(num_slices):
                    rotated_pos = pos.rotate(i * slice_angle)
                    if symmetry_mode == 'Kaleidoscope' and i % 2 == 1:
                        rotated_pos.y = -rotated_pos.y
                    draw_pos = (int(rotated_pos.x + CENTER_X), int(rotated_pos.y + CENTER_Y))
                    pygame.draw.circle(surface, element['color'], draw_pos, int(element['size']))

def get_composite_image(layers, num_slices, symmetry_mode, object_rotation_angle):
    """
    将所有图层合成为一张最终的对称图像。
    它会先渲染每个图层的像素笔触，然后渲染该图层上的所有矢量形状，并应用对称性。
    """
    base_surface = pygame.Surface((DRAW_AREA_WIDTH, 800), pygame.SRCALPHA)
    center_vector = pygame.Vector2(CENTER_X, CENTER_Y)

    for layer in reversed(layers):
        if not layer.is_visible:
            continue
            
        base_surface.blit(layer.surface, (0, 0))

        slice_angle_deg = 360 / num_slices
        for shape in layer.shapes:
            current_shape_rotation = shape.rotation + object_rotation_angle
            repeat_count = num_slices if getattr(shape, 'repeat_enabled', True) else 1
            
            for i in range(repeat_count):
                slice_rotation_angle = i * slice_angle_deg
                
                pos_relative_to_center = shape.pos - center_vector
                rotated_pos = pos_relative_to_center.rotate(slice_rotation_angle)
                
                if symmetry_mode == 'Kaleidoscope' and i % 2 == 1:
                    rotated_pos.y *= -1
                    
                final_pos = rotated_pos + center_vector
                
                final_rotation = current_shape_rotation
                if symmetry_mode == 'Kaleidoscope' and i % 2 == 1:
                    final_rotation *= -1
                final_rotation += slice_rotation_angle

                points = [p.rotate(final_rotation) + final_pos for p in shape.get_points()]
                
                if len(points) >= 3:
                    if shape.stroke_width > 0:
                        pygame.draw.polygon(base_surface, shape.stroke_color, points, int(shape.stroke_width))
                        
    return base_surface

def apply_global_dynamics(surface, global_angle, pulsing_scale, trail_frames):
    """
    对合成后的图像应用最终的全局动态效果。
    包括历史轨迹、全局旋转和脉冲缩放。
    """
    final_canvas = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    
    for i, (frame, alpha) in enumerate(trail_frames):
        trail_surface = frame.copy()
        trail_surface.set_alpha(alpha)
        final_canvas.blit(trail_surface, (0, 0))

    final_canvas.blit(surface, (0, 0))

    if global_angle != 0 or pulsing_scale != 1.0:
        rotated_surface = pygame.transform.rotozoom(final_canvas, global_angle, pulsing_scale)
        rect = rotated_surface.get_rect(center=(CENTER_X, CENTER_Y))
        
        output_canvas = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        output_canvas.blit(rotated_surface, rect)
        return output_canvas
        
    return final_canvas
