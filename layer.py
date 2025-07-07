# layer.py
import pygame
from config import DRAW_AREA_WIDTH, SCREEN_HEIGHT

class Layer:
    _next_id = 1
    
    def __init__(self, name=None):
        self.id = Layer._next_id
        if name is None:
            self.name = f"Layer {self.id}"
        else:
            self.name = name
        Layer._next_id += 1
        
        # [MODIFIED] Each layer has BOTH a pixel surface AND a list of vector shapes
        self.surface = pygame.Surface((DRAW_AREA_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.shapes = []
        
        self.is_visible = True