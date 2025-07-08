# filepath: f:\X_code\Projects\25_summer_python\py_game_Kaleidoscope\utils.py
# utils.py
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

def load_icon(icon_name):
    """加载指定名称的图标。"""
    return pygame.image.load(f'assets/{icon_name}.svg').convert_alpha()

def create_tool_button(manager, position, icon_name, tool_name):
    """创建工具按钮，使用指定的图标和工具名称。"""
    button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(position, (50, 50)),
        text='',
        manager=manager,
        object_id=tool_name
    )
    button.set_image(load_icon(icon_name))
    return button

def create_slice_slider(manager, position):
    """创建切片数量滑块，允许选择4到16之间的偶数。"""
    slider = pygame_gui.elements.UIHorizontalSlider(
        relative_rect=pygame.Rect(position, (200, 20)),
        start_value=4,
        value_range=(4, 16),
        manager=manager
    )
    return slider
