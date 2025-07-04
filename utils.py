# utils.py
import pygame

def lerp_color(c1, c2, t):
    t = max(0, min(1, t))
    return tuple(int(a * (1 - t) + b * t) for a, b in zip(c1, c2))

def create_color_spectrum(rect):
    spectrum = pygame.Surface((rect.width, rect.height))
    for y in range(rect.height):
        for x in range(rect.width):
            hue = int((x / rect.width) * 360)
            saturation = 1.0 - (y / rect.height)
            value = 1.0
            color = pygame.Color(0)
            color.hsva = (hue, saturation * 100, value * 100, 100)
            spectrum.set_at((x, y), color)
    return spectrum