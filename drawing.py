# drawing.py
import pygame
import math
import random
from config import CENTER_X, CENTER_Y

def draw_on_surface(surface, elements, num_slices, symmetry_mode, global_rotation_angle, pulsing_scale):
    # [FIXED] This function now correctly loops through all slices internally
    slice_angle = 2 * math.pi / num_slices
    
    for i in range(num_slices):
        rot_angle = i * slice_angle + global_rotation_angle
        
        for element in elements:
            scaled_pos = (pygame.Vector2(element['pos']) - (CENTER_X, CENTER_Y)) * pulsing_scale + (CENTER_X, CENTER_Y)
            pos_vec = pygame.Vector2(scaled_pos) - (CENTER_X, CENTER_Y)
            
            # Draw original
            rotated_pos = pos_vec.rotate_rad(rot_angle) + (CENTER_X, CENTER_Y)
            if element['type'] == 'Circle':
                pygame.draw.circle(surface, element['color'], rotated_pos, element['size'])
            elif element['type'] == 'Spray':
                for _ in range(3):
                    offset = (random.randint(-element['size'], element['size']), random.randint(-element['size'], element['size']))
                    pygame.draw.circle(surface, element['color'], rotated_pos + offset, 1)

            # Draw mirror if in kaleidoscope mode
            if symmetry_mode == 'Kaleidoscope':
                mirrored_pos_vec = pygame.Vector2(pos_vec.x, -pos_vec.y)
                rotated_mirrored_pos = mirrored_pos_vec.rotate_rad(rot_angle) + (CENTER_X, CENTER_Y)
                if element['type'] == 'Circle':
                    pygame.draw.circle(surface, element['color'], rotated_mirrored_pos, element['size'])
                elif element['type'] == 'Spray':
                    for _ in range(3):
                        offset = (random.randint(-element['size'], element['size']), random.randint(-element['size'], element['size']))
                        pygame.draw.circle(surface, element['color'], rotated_mirrored_pos + offset, 1)

def get_composite_image(layers, apply_dynamics=False, **dynamics_params):
    from config import DRAW_AREA_WIDTH, SCREEN_HEIGHT, CENTER_X, CENTER_Y
    composite = pygame.Surface((DRAW_AREA_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    
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