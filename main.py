import os
import sys
from src.interface.gui import ChromaApp

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    app = ChromaApp()
    
    icon_path = resource_path("icon.ico")
    if os.path.exists(icon_path):
        try:
            app.iconbitmap(icon_path)
        except:
            pass
            
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()