import time
import threading
from PIL import ImageGrab
import pyautogui
import pyperclip
from pynput import keyboard
from typing import Callable

class ScreenService:
    """Servicio para leer píxeles de la pantalla."""
    
    def get_color_at_cursor(self) -> tuple[int, int, int]:
        """Obtiene el color RGB bajo el cursor del mouse."""
        x, y = pyautogui.position()
        # Capturamos solo 1 pixel para máxima eficiencia
        # bbox = (left, top, right, bottom)
        image = ImageGrab.grab(bbox=(x, y, x+1, y+1))
        return image.getpixel((0, 0))

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
        """Inicia la escucha no bloqueante."""
        if not self.listener:
            self.is_active = True
            # Usamos la tecla 'INSERT' (o 'INS') como disparador
            self.listener = keyboard.GlobalHotKeys({
                '<insert>': self._on_activate
            })
            self.listener.start()

    def stop(self):
        """Detiene la escucha."""
        self.is_active = False
        if self.listener:
            self.listener.stop()
            self.listener = None

    def _on_activate(self):
        if self.is_active:
            self.on_trigger()