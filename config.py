# config.py
import os
import pygame

# --- Screen & Layout ---
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
UI_PANEL_WIDTH = 220
LAYER_PANEL_WIDTH = 180
DRAW_AREA_WIDTH = SCREEN_WIDTH - UI_PANEL_WIDTH - LAYER_PANEL_WIDTH
CENTER_X, CENTER_Y = DRAW_AREA_WIDTH // 2, SCREEN_HEIGHT // 2

# --- Performance ---
FPS = 60

# --- File Paths ---
SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
THEME_PATH = os.path.join(SCRIPT_DIRECTORY, 'theme.json')
EXPORTS_DIR = 'exports'

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
STATUS_TEXT_COLOR = (255, 255, 0)
PREVIEW_LINE_COLOR = (200, 200, 200)
BACKGROUND_COLOR = (20, 20, 20)