# filepath: f:\X_code\Projects\25_summer_python\py_game_Kaleidoscope\shapes.py
"""
定义所有可绘制的矢量形状对象。
包含一个基类 Shape 和具体的形状子类如 Triangle 和 Star。
"""
import pygame
import math

class Shape:
    """
    所有矢量形状的基类。
    定义了形状的通用属性，如位置、大小、颜色和旋转，以及通用方法。
    """
    _next_id = 1
    def __init__(self, pos, size, fill_color, rotation=0.0, stroke_width=0, stroke_color=(0,0,0)):
        self.id = Shape._next_id; Shape._next_id += 1
        self.pos = pygame.Vector2(pos)
        self.size = float(size)
        self.fill_color = fill_color
        self.stroke_color = stroke_color
        self.stroke_width = int(stroke_width)
        self.rotation = float(rotation)
        self.selected = False

    def get_points(self):
        """
        计算并返回构成形状的本地坐标顶点列表（围绕原点 0,0）。
        必须在子类中实现。
        """
        raise NotImplementedError

    def get_world_points(self):
        """
        计算并返回形状在世界空间中的最终顶点坐标。
        它将本地顶点应用旋转，然后平移到世界位置。
        """
        local_points = self.get_points()
        rotated_points = [p.rotate(self.rotation) for p in local_points]
        world_points = [(p + self.pos) for p in rotated_points]
        return world_points

    def draw(self, surface):
        """在给定的 surface 上直接绘制自身（无对称性）。"""
        points = self.get_world_points()
        if len(points) < 3: return

        pygame.draw.polygon(surface, self.fill_color, points)
        if self.stroke_width > 0:
            pygame.draw.polygon(surface, self.stroke_color, points, self.stroke_width)
    
    def get_bounding_box(self):
        """
        计算并返回能够完全包围该形状在世界空间中的所有顶点的矩形。
        用于碰撞检测（选择）和绘制选择框。
        """
        points = self.get_world_points()
        if not points: return pygame.Rect(self.pos, (0,0))
        min_x = min(p.x for p in points)
        max_x = max(p.x for p in points)
        min_y = min(p.y for p in points)
        max_y = max(p.y for p in points)
        return pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)

class Triangle(Shape):
    """三角形形状。"""
    def __init__(self, pos, size, fill_color, triangle_type='equilateral', **kwargs):
        super().__init__(pos, size, fill_color, **kwargs)
        self.type = triangle_type

    def get_points(self):
        """根据三角形类型（等边或直角）返回顶点。"""
        s = self.size
        if self.type == 'equilateral':
            h = s * math.sqrt(3) / 2
            return [pygame.Vector2(0, -h * 2/3), pygame.Vector2(-s/2, h * 1/3), pygame.Vector2(s/2, h * 1/3)]
        elif self.type == 'right':
            return [pygame.Vector2(-s/2, -s/2), pygame.Vector2(-s/2, s/2), pygame.Vector2(s/2, s/2)]
        return []

class Star(Shape):
    """五角星（或多角星）形状。"""
    def __init__(self, pos, size, fill_color, points=5, sharpness=0.5, **kwargs):
        super().__init__(pos, size, fill_color, **kwargs)
        self.points = points
        self.sharpness = sharpness

    def get_points(self):
        """根据角数和锐度计算星星的内外顶点。"""
        num_vertices = self.points * 2
        outer_radius = self.size / 2
        inner_radius = outer_radius * self.sharpness
        angle_step = 360 / num_vertices
        local_points = []
        for i in range(num_vertices):
            angle = i * angle_step - 90
            radius = outer_radius if i % 2 == 0 else inner_radius
            vec = pygame.Vector2(radius, 0).rotate(angle)
            local_points.append(vec)
        return local_points