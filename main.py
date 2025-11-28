import os
import sys
from src.interface.gui import ChromaApp

def resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso, funcione en dev o en PyInstaller."""
    try:
        # PyInstaller crea una carpeta temporal en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    app = ChromaApp()
    
    # Usamos la ruta inteligente
    icon_path = resource_path("icon.ico")
    
    if os.path.exists(icon_path):
        try:
            app.iconbitmap(icon_path)
        except:
            pass
            
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()