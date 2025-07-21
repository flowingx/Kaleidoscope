"""
包含通用的辅助函数，如颜色插值和图像创建。
"""
import pygame

def lerp_color(c1, c2, t):
    """
    在两个 RGB 颜色之间进行线性插值。
    t=0.0 返回 c1, t=1.0 返回 c2。
    """
    t = max(0, min(1, t))
    return tuple(int(a * (1 - t) + b * t) for a, b in zip(c1, c2))

def create_color_spectrum(size):
    """
    创建一个指定大小的颜色光谱图像（Surface）。
    用于 UI 中的颜色选择器。
    """
    spectrum = pygame.Surface(size)
    width, height = size
    for y in range(height):
        for x in range(width):
            hue = int((x / width) * 360)
            saturation = 1.0
            value = 1.0 - (y / height)
            color = pygame.Color(0)
            color.hsva = (hue, saturation * 100, value * 100, 100)
            spectrum.set_at((x, y), color)
    return spectrum