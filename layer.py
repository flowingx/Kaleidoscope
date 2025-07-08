"""
定义图层类（Layer）。
每个图层对象代表一个独立的绘图层面，它既可以包含像素数据（通过其 surface 属性），
也可以包含矢量形状对象列表。这种结构使得像素绘制和矢量图形可以共存于同一项目中，
并能独立控制它们的可见性和渲染顺序。
"""
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
        
        self.surface = pygame.Surface((DRAW_AREA_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.shapes = []
        self.is_visible = True