import mss
import pyautogui
import pyperclip
from pynput import keyboard
from PIL import Image
from typing import Callable
import platform
import ctypes

# Fix DPI para Windows (Alta resolución / Múltiples monitores)
if platform.system() == "Windows":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        ctypes.windll.user32.SetProcessDPIAware()

class ScreenService:
    def __init__(self):
        self.sct = mss.mss()

    def get_color_at_cursor(self) -> tuple[int, int, int]:
        x, y = pyautogui.position()
        monitor = {"top": int(y), "left": int(x), "width": 1, "height": 1}
        try:
            sct_img = self.sct.grab(monitor)
            return sct_img.pixel(0, 0)
        except Exception:
            return (0, 0, 0)

    def get_zoom_image(self, radius: int = 10, zoom_factor: int = 8) -> Image.Image:
        """
        Captura un área alrededor del mouse y la escala para efecto lupa.
        radius: Cuántos píxeles capturar hacia cada lado (10 = área de 20x20)
        zoom_factor: Cuánto agrandar cada píxel.
        """
        x, y = pyautogui.position()
        
        # Definir el cuadro a capturar (centrado en el mouse)
        # MSS maneja coordenadas negativas automáticamente
        monitor = {
            "top": int(y - radius), 
            "left": int(x - radius), 
            "width": int(radius * 2), 
            "height": int(radius * 2)
        }
        
        try:
            sct_img = self.sct.grab(monitor)
            
            # Convertir a PIL Image
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            
            # Escalar imagen (Algoritmo NEAREST para mantener los píxeles cuadrados)
            new_size = (img.width * zoom_factor, img.height * zoom_factor)
            return img.resize(new_size, resample=Image.Resampling.NEAREST)
            
        except Exception:
            # Retorna una imagen negra si falla (ej. bordes de pantalla extremos)
            return Image.new("RGB", (radius*2*zoom_factor, radius*2*zoom_factor), "black")

class ClipboardService:
    def copy(self, text: str):
        pyperclip.copy(text)

class InputListener:
    def __init__(self, on_trigger: Callable):
        self.on_trigger = on_trigger
        self.listener = None
        self.is_active = False

    def start(self):
        if not self.listener:
            self.is_active = True
            self.listener = keyboard.GlobalHotKeys({'<insert>': self._on_activate})
            self.listener.start()

    def stop(self):
        self.is_active = False
        if self.listener:
            self.listener.stop()
            self.listener = None

    def _on_activate(self):
        if self.is_active:
            self.on_trigger()