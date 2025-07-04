# main.py
from app import App

if __name__ == '__main__':
    from config import EXPORTS_DIR
    import os
    if not os.path.exists(EXPORTS_DIR):
        os.makedirs(EXPORTS_DIR)
        
    app = App()
    app.run()