# config.py
import os
import sys

def get_base_path():
    # If the application is run as a bundle, the PyInstaller bootloader
    # sets the sys._MEIPASS attribute to the path of the BUNDLE folder.
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    # Otherwise, we are running in a normal Python environment.
    return os.path.abspath(os.path.dirname(__file__))

# Define an absolute project root using our reliable function.
PROJECT_ROOT = get_base_path()

# --- Screen & Layout ---
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
UI_PANEL_WIDTH = 220
LAYER_PANEL_WIDTH = 180
DRAW_AREA_WIDTH = SCREEN_WIDTH - UI_PANEL_WIDTH - LAYER_PANEL_WIDTH
CENTER_X, CENTER_Y = DRAW_AREA_WIDTH // 2, SCREEN_HEIGHT // 2

# --- Performance ---
FPS = 60
GUIDE_LINE_COLOR = (80, 80, 80)

# --- File Paths ---
THEME_PATH = os.path.join(PROJECT_ROOT, 'theme.json')

if getattr(sys, 'frozen', False):
    # If we are running in a PyInstaller bundle
    application_path = os.path.dirname(sys.executable)
else:
    # If we are running in a normal Python environment
    application_path = os.path.dirname(os.path.abspath(__file__))

EXPORTS_DIR = os.path.join(application_path, 'exports')

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
STATUS_TEXT_COLOR = (255, 255, 0)
PREVIEW_LINE_COLOR = (200, 200, 200)
BACKGROUND_COLOR = (20, 20, 20)