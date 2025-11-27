import customtkinter as ctk
from PIL import Image, ImageTk
import pyautogui
from src.core.use_cases import capture_color_use_case
from src.infrastructure.services import ScreenService, ClipboardService, InputListener, SoundService
from src.infrastructure.repositories import JsonColorRepository

class ZoomWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True) 
        self.attributes("-topmost", True) 
        self.geometry("160x160") 
        
        self.canvas = ctk.CTkCanvas(self, width=160, height=160, 
                                    highlightthickness=2, highlightbackground="#00E5FF")
        self.canvas.pack(fill="both", expand=True)
        
    def update_image(self, pil_image):
        self.photo = ImageTk.PhotoImage(pil_image)
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
        
        # Ajuste de precisión
        zoom = 8
        pixel_start = 10 * zoom
        pixel_end = pixel_start + zoom
        
        self.canvas.delete("reticula")
        self.canvas.create_rectangle(
            pixel_start, pixel_start, 
            pixel_end, pixel_end, 
            outline="#FF0000", width=2,
            tags="reticula" 
        )

    def move_near_mouse(self):
        x, y = pyautogui.position()
        self.geometry(f"+{int(x) + 15}+{int(y) + 15}")

class ChromaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("ChromaGrab")
        self.geometry("520x650")
        ctk.set_appearance_mode("Dark")
        self.attributes("-topmost", True) 
        
        # Dependencias
        self.screen_svc = ScreenService()
        self.clip_svc = ClipboardService()
        self.sound_svc = SoundService() # <--- NUEVO
        self.repo = JsonColorRepository()
        
        # Estado
        self.zoom_active = False
        self.zoom_window = None
        self.history = []
        
        # Listener (Ahora pasamos dos funciones)
        self.listener = InputListener(
            on_capture=self.trigger_capture,
            on_toggle_zoom=self.trigger_zoom_toggle
        )
        self.listener.start()
        
        self._setup_ui()
        self.after(100, self.load_saved_history)

    def _setup_ui(self):
        # HEADER
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(self.header, text="ChromaGrab 2.3", font=("Segoe UI", 20, "bold")).pack(side="left")
        
        self.top_var = ctk.BooleanVar(value=True)
        self.switch_top = ctk.CTkSwitch(self.header, text="Fijar Ventana", 
                                    variable=self.top_var, command=self.toggle_top, font=("Segoe UI", 12))
        self.switch_top.pack(side="right")

        # CONTROLES
        self.controls = ctk.CTkFrame(self, fg_color="#2B2B2B")
        self.controls.pack(fill="x", padx=15, pady=10)
        
        self.zoom_var = ctk.BooleanVar(value=False)
        self.switch_zoom = ctk.CTkSwitch(self.controls, text="Lupa (Alt + Z)", 
                                         variable=self.zoom_var, command=self.toggle_zoom_ui,
                                         font=("Segoe UI", 13, "bold"), progress_color="#00E5FF")
        self.switch_zoom.pack(pady=10)
        
        ctk.CTkLabel(self.controls, text="[INSERT] para capturar", text_color="gray", font=("Arial", 11)).pack(pady=(0, 10))

        # LISTA
        self.list_header = ctk.CTkFrame(self, fg_color="transparent", height=20)
        self.list_header.pack(fill="x", padx=25)
        ctk.CTkLabel(self.list_header, text="Color", width=50, anchor="w").pack(side="left")
        ctk.CTkLabel(self.list_header, text="Hex", width=100, anchor="w").pack(side="left", padx=5)
        
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#1A1A1A")
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # FOOTER
        self.btn_clear = ctk.CTkButton(self, text="Borrar Todo", 
                                       fg_color="#333333", hover_color="#C62828",
                                       command=self.clear_all_history, height=30)
        self.btn_clear.pack(pady=15)

    def load_saved_history(self):
        self.history = self.repo.load_all()
        self.refresh_list_ui()

    def refresh_list_ui(self):
        for w in self.scroll_frame.winfo_children(): w.destroy()
        for index, color in enumerate(reversed(self.history)):
            real_index = len(self.history) - 1 - index
            self.draw_row(color, real_index)

    def draw_row(self, color, real_index):
        row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        row.pack(fill="x", pady=2)
        try:
            box = ctk.CTkLabel(row, text="", fg_color=color.hex_code, width=35, height=25, corner_radius=4)
        except:
            box = ctk.CTkLabel(row, text="?", width=35)
        box.pack(side="left", padx=5)
        ctk.CTkLabel(row, text=color.hex_code, font=("Consolas", 13, "bold"), width=80, anchor="w").pack(side="left", padx=5)
        
        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.pack(side="right")
        
        ctk.CTkButton(actions, text="HEX", width=40, height=22, font=("Arial", 10, "bold"),
                      fg_color="#222222", hover_color="#444444", border_width=1, border_color="gray",
                      command=lambda: self.clip_svc.copy(color.hex_code)).pack(side="left", padx=2)
        rgb_val = str(color.rgb_tuple)
        ctk.CTkButton(actions, text="RGB", width=40, height=22, font=("Arial", 10, "bold"),
                      fg_color="#222222", hover_color="#444444", border_width=1, border_color="gray",
                      command=lambda: self.clip_svc.copy(rgb_val)).pack(side="left", padx=2)
        ctk.CTkButton(actions, text="✕", width=25, height=22, font=("Arial", 12, "bold"),
                      fg_color="transparent", hover_color="#C62828", text_color="#FF5555",
                      command=lambda idx=real_index: self.delete_single_color(idx)).pack(side="left", padx=(5, 0))

    def delete_single_color(self, index):
        if 0 <= index < len(self.history):
            del self.history[index]
            self.repo.save_all(self.history)
            self.refresh_list_ui()

    def toggle_top(self):
        self.attributes("-topmost", self.top_var.get())

    # --- Lógica de Zoom mejorada ---
    def trigger_zoom_toggle(self):
        """Llamado por el atajo de teclado (Hilo secundario)."""
        self.after(0, self._sync_zoom_toggle)

    def _sync_zoom_toggle(self):
        """Sincroniza el switch de la UI y ejecuta la lógica."""
        # Invertimos el estado actual del switch
        current_state = self.zoom_var.get()
        self.zoom_var.set(not current_state)
        # Ejecutamos la lógica normal de toggle
        self.toggle_zoom_ui()

    def toggle_zoom_ui(self):
        """Llamado al hacer clic en el switch o por el atajo."""
        if self.zoom_var.get():
            self.zoom_active = True
            if not self.zoom_window:
                self.zoom_window = ZoomWindow(self)
            self._zoom_loop()
        else:
            self.zoom_active = False
            if self.zoom_window:
                self.zoom_window.destroy()
                self.zoom_window = None

    def _zoom_loop(self):
        if self.zoom_active and self.zoom_window:
            img = self.screen_svc.get_zoom_image(radius=10, zoom_factor=8)
            self.zoom_window.update_image(img)
            self.zoom_window.move_near_mouse()
            self.after(30, self._zoom_loop)

    # --- Captura ---
    def trigger_capture(self):
        self.after(0, self.process_capture)

    def process_capture(self):
        try:
            # 1. Sonido Nuevo
            self.sound_svc.play_capture()
            
            # 2. Captura
            color = capture_color_use_case(self.screen_svc)
            
            # 3. Guardar y Mostrar
            self.history.append(color)
            self.repo.save_all(self.history)
            self.refresh_list_ui()
            
            # 4. Copiar HEX
            self.clip_svc.copy(color.hex_code)
            
        except Exception as e:
            print(e)

    def clear_all_history(self):
        self.history.clear()
        self.repo.save_all([])
        self.refresh_list_ui()

    def on_close(self):
        self.zoom_active = False
        self.listener.stop()
        self.destroy()