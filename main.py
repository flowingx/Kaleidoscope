# main.py
import os
from app import App

from config import EXPORTS_DIR

if __name__ == '__main__':
    # Use the absolute path to check for and create the exports directory
    if not os.path.exists(EXPORTS_DIR):
        os.makedirs(EXPORTS_DIR)
        
    app = App()
    app.run()