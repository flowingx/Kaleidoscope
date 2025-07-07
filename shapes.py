import pygame
import math

class Shape:
    """所有矢量对象的基类"""
    def __init__(self, pos, size, fill_color, rotation=0.0, stroke_width=0, stroke_color=(0,0,0)):
        self.pos = pygame.Vector2(pos)
        self.size = size
        self.fill_color = fill_color
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.rotation = rotation  # 对象自身的旋转角度（用于固定位置自转）

    def get_points(self):
        """计算并返回构成形状的顶点列表（相对于对象中心）"""
        raise NotImplementedError

    def draw(self, surface):
        """在给定的 surface 上绘制自己（无对称性）"""
        points = self.get_points()
        if not points: return

        # 应用对象自身的旋转
        rotated_points = [p.rotate(self.rotation) for p in points]
        # 将点平移到最终位置
        final_points = [(p.x + self.pos.x, p.y + self.pos.y) for p in rotated_points]

        # 绘制填充和描边
        pygame.draw.polygon(surface, self.fill_color, final_points)
        if self.stroke_width > 0:
            pygame.draw.polygon(surface, self.stroke_color, final_points, self.stroke_width)

class Triangle(Shape):
    def __init__(self, pos, size, fill_color, **kwargs):
        super().__init__(pos, size, fill_color, **kwargs)
        self.type = 'equilateral' # 可扩展为 'right'

    def get_points(self):
        s = self.size
        h = s * math.sqrt(3) / 2
        # 顶点围绕(0,0)中心
        return [pygame.Vector2(0, -h * 2/3), pygame.Vector2(-s/2, h * 1/3), pygame.Vector2(s/2, h * 1/3)]

class Star(Shape):
    def __init__(self, pos, size, fill_color, sharpness=0.5, **kwargs):
        super().__init__(pos, size, fill_color, **kwargs)
        self.sharpness = sharpness # 0.0 (钝) to 1.0 (尖)

    def get_points(self):
        points = []
        outer_radius = self.size / 2
        inner_radius = outer_radius * (1 - self.sharpness)
        for i in range(10):
            angle = math.pi / 5 * i - math.pi / 2
            radius = outer_radius if i % 2 == 0 else inner_radius
            points.append(pygame.Vector2(radius * math.cos(angle), radius * math.sin(angle)))
        return points