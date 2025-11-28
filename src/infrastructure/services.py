import mss
import pyautogui
import pyperclip
import winsound
from pynput import keyboard
from typing import Callable
from PIL import Image
import platform
import ctypes

if platform.system() == "Windows":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1) 
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

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
        x, y = pyautogui.position()
        monitor = {
            "top": int(y - radius), 
            "left": int(x - radius), 
            "width": int(radius * 2), 
            "height": int(radius * 2)
        }
        try:
            sct_img = self.sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            new_size = (img.width * zoom_factor, img.height * zoom_factor)
            return img.resize(new_size, resample=Image.Resampling.NEAREST)
        except Exception:
            return Image.new("RGB", (radius*2*zoom_factor, radius*2*zoom_factor), "black")

class ClipboardService:
    def copy(self, text: str):
        pyperclip.copy(text)

class SoundService:
    def play_capture(self):
        winsound.Beep(1000, 100) 

class InputListener:
    def __init__(self, on_capture: Callable, on_toggle_zoom: Callable):
        self.on_capture = on_capture
        self.on_toggle_zoom = on_toggle_zoom
        self.listener = None
        self.is_active = False

    def start(self):
        if not self.listener:
            self.is_active = True
            self.listener = keyboard.GlobalHotKeys({
                '<insert>': self._on_capture_trigger,
                '<alt>+z': self._on_zoom_trigger
            })
            self.listener.start()

    def stop(self):
        self.is_active = False
        if self.listener:
            self.listener.stop()
            self.listener = None

    def _on_capture_trigger(self):
        if self.is_active: self.on_capture()

    def _on_zoom_trigger(self):
        if self.is_active: self.on_toggle_zoom()