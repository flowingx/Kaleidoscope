# config.py
import os

# --- [CRITICAL FIX] Define an absolute project root ---
# This ensures all file paths are relative to the project folder, not the current working directory.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# --- Screen & Layout ---
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
UI_PANEL_WIDTH = 220
LAYER_PANEL_WIDTH = 180
DRAW_AREA_WIDTH = SCREEN_WIDTH - UI_PANEL_WIDTH - LAYER_PANEL_WIDTH
CENTER_X, CENTER_Y = DRAW_AREA_WIDTH // 2, SCREEN_HEIGHT // 2

# --- Performance ---
FPS = 60

# --- File Paths (now based on the absolute project root) ---
THEME_PATH = os.path.join(PROJECT_ROOT, 'theme.json')
EXPORTS_DIR = os.path.join(PROJECT_ROOT, 'exports')

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
STATUS_TEXT_COLOR = (255, 255, 0)
PREVIEW_LINE_COLOR = (200, 200, 200)
BACKGROUND_COLOR = (20, 20, 20)