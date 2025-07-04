# layer.py
import pygame

class Layer:
    _next_id = 1
    
    def __init__(self, size, name=None):
        self.id = Layer._next_id
        if name is None:
            self.name = f"Drawing {self.id}"
        else:
            self.name = name
        Layer._next_id += 1
        
        self.surface = pygame.Surface(size, pygame.SRCALPHA)
        self.is_visible = True