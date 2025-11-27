import time
import threading
import mss
import pyautogui
import pyperclip
from pynput import keyboard
from typing import Callable

class ScreenService:
    """Servicio de captura de pantalla ultra-rápido usando MSS."""
    
    def __init__(self):
        self.sct = mss.mss()

    def get_color_at_cursor(self) -> tuple[int, int, int]:
        """
        Obtiene el color RGB bajo el cursor.
        Soporta monitores negativos (arriba/izquierda) correctamente.
        """
        x, y = pyautogui.position()
        
        # Definimos una región de 1x1 píxel en la posición del mouse
        monitor = {"top": y, "left": x, "width": 1, "height": 1}
        
        # Capturamos esa región
        sct_img = self.sct.grab(monitor)
        
        # MSS devuelve BGRA, necesitamos convertir a RGB
        # pixel(0, 0) devuelve (R, G, B) directamente en versiones modernas
        return sct_img.pixel(0, 0)

class ClipboardService:
    """Servicio para interactuar con el portapapeles."""
    
    def copy(self, text: str):
        pyperclip.copy(text)

class InputListener:
    """
    Escucha eventos de teclado en un hilo separado.
    """
    def __init__(self, on_trigger: Callable):
        self.on_trigger = on_trigger
        self.listener = None
        self.is_active = False

    def start(self):
        if not self.listener:
            self.is_active = True
            # Usamos INSERT como disparador
            self.listener = keyboard.GlobalHotKeys({
                '<insert>': self._on_activate
            })
            self.listener.start()

    def stop(self):
        self.is_active = False
        if self.listener:
            self.listener.stop()
            self.listener = None

    def _on_activate(self):
        if self.is_active:
            self.on_trigger()