# utils.py
import pygame

def lerp_color(c1, c2, t):
    t = max(0, min(1, t))
    return tuple(int(a * (1 - t) + b * t) for a, b in zip(c1, c2))

def create_color_spectrum(size):
    """Creates a color spectrum surface of a given size."""
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