import customtkinter as ctk
from PIL import Image, ImageTk
import pyautogui
from src.core.use_cases import capture_color_use_case
from src.infrastructure.services import ScreenService, ClipboardService, InputListener

class ZoomWindow(ctk.CTkToplevel):
    """Ventana flotante que muestra el zoom."""
    def __init__(self, master):
        super().__init__(master)
        
        # Configuración "Fantasma"
        self.overrideredirect(True) # Quitar bordes y título
        self.attributes("-topmost", True) # Siempre encima
        self.geometry("160x160") # Tamaño fijo
        
        # Canvas para dibujar la imagen y la retícula
        self.canvas = ctk.CTkCanvas(self, width=160, height=160, 
                                    highlightthickness=2, highlightbackground="#00E5FF")
        self.canvas.pack(fill="both", expand=True)
        
        # Cruz central (Retícula) para apuntar
        # El centro es 80,80. Dibujamos una cruz.
        self.crosshair_color = "#00E5FF" # Cyan Neon
        
    def update_image(self, pil_image):
        # Convertir a formato compatible con Canvas
        self.photo = ImageTk.PhotoImage(pil_image)
        
        # Dibujar imagen
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
        
        # --- CORRECCIÓN DE PRECISIÓN ---
        # El área es de 20x20 píxeles originales.
        # El píxel central (el del mouse) es el que está en (10, 10).
        # Con zoom x8, ese píxel empieza en 10*8 = 80 y termina en 88.
        
        zoom = 8
        pixel_start = 10 * zoom  # 80
        pixel_end = pixel_start + zoom # 88
        
        # Dibujamos el rectángulo ROJO bordeando exactamente ese píxel gigante
        # create_rectangle(x1, y1, x2, y2)
        
        # Borramos retículas anteriores para no acumular basura en el canvas
        self.canvas.delete("reticula")
        
        self.canvas.create_rectangle(
            pixel_start, pixel_start, 
            pixel_end, pixel_end, 
            outline="#FF0000", width=2,
            tags="reticula" # Tag para poder borrarlo luego
        )

    def move_near_mouse(self):
        """Mueve la ventana cerca del mouse pero sin taparlo."""
        x, y = pyautogui.position()
        # Offset ajustado: +15 píxeles para estar más cerca
        self.geometry(f"+{int(x) + 15}+{int(y) + 15}")

class ChromaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("ChromaGrab")
        self.geometry("480x650")
        ctk.set_appearance_mode("Dark")
        self.attributes("-topmost", True) 
        
        # Dependencias
        self.screen_svc = ScreenService()
        self.clip_svc = ClipboardService()
        
        # Estado
        self.zoom_active = False
        self.zoom_window = None
        
        # Listener
        self.listener = InputListener(on_trigger=self.trigger_capture)
        self.listener.start()
        
        self._setup_ui()

    def _setup_ui(self):
        # HEADER
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(self.header, text="ChromaGrab 2.0", font=("Segoe UI", 20, "bold")).pack(side="left")
        
        # Switch Fijar
        self.top_var = ctk.BooleanVar(value=True)
        self.switch_top = ctk.CTkSwitch(self.header, text="Fijar Ventana", 
                                    variable=self.top_var, command=self.toggle_top, font=("Segoe UI", 12))
        self.switch_top.pack(side="right")

        # CONTROLES PRINCIPALES
        self.controls = ctk.CTkFrame(self, fg_color="#2B2B2B")
        self.controls.pack(fill="x", padx=15, pady=10)
        
        # Switch Lupa
        self.zoom_var = ctk.BooleanVar(value=False)
        self.switch_zoom = ctk.CTkSwitch(self.controls, text="Activar Lupa (Live Zoom)", 
                                         variable=self.zoom_var, command=self.toggle_zoom,
                                         font=("Segoe UI", 13, "bold"), progress_color="#00E5FF")
        self.switch_zoom.pack(pady=15)
        
        ctk.CTkLabel(self.controls, text="[INSERT] para capturar", text_color="gray").pack(pady=(0, 10))

        # LISTA HISTORIAL
        self.list_header = ctk.CTkFrame(self, fg_color="transparent", height=20)
        self.list_header.pack(fill="x", padx=25)
        ctk.CTkLabel(self.list_header, text="Color", width=60, anchor="w").pack(side="left")
        ctk.CTkLabel(self.list_header, text="Hex", width=120, anchor="w").pack(side="left", padx=10)
        
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#1A1A1A")
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # FOOTER
        self.btn_clear = ctk.CTkButton(self, text="Limpiar Historial", 
                                       fg_color="#333333", hover_color="#C62828",
                                       command=self.clear_history)
        self.btn_clear.pack(pady=15)

    def toggle_top(self):
        self.attributes("-topmost", self.top_var.get())

    def toggle_zoom(self):
        """Activa o desactiva la ventana flotante de zoom."""
        if self.zoom_var.get():
            self.zoom_active = True
            self.zoom_window = ZoomWindow(self)
            self._zoom_loop() # Iniciar el bucle de actualización
        else:
            self.zoom_active = False
            if self.zoom_window:
                self.zoom_window.destroy()
                self.zoom_window = None

    def _zoom_loop(self):
        """Bucle infinito (mientras esté activo) para actualizar la lupa."""
        if self.zoom_active and self.zoom_window:
            # 1. Obtener imagen ampliada
            img = self.screen_svc.get_zoom_image(radius=10, zoom_factor=8)
            
            # 2. Actualizar ventana
            self.zoom_window.update_image(img)
            self.zoom_window.move_near_mouse()
            
            # 3. Repetir en 30ms (~30 FPS)
            self.after(30, self._zoom_loop)

    def trigger_capture(self):
        self.after(0, self.process_capture)

    def process_capture(self):
        # Desactivar lupa momentáneamente para que no moleste en la captura (opcional) o dejarla
        try:
            color = capture_color_use_case(self.screen_svc)
            self.add_color_row(color)
            self.clip_svc.copy(color.hex_code)
        except Exception as e:
            print(e)

    def add_color_row(self, color):
        row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        row.pack(fill="x", pady=2)
        
        # Color Box
        try:
            box = ctk.CTkLabel(row, text="", fg_color=color.hex_code, width=40, height=25, corner_radius=4)
        except:
            box = ctk.CTkLabel(row, text="?", width=40)
        box.pack(side="left", padx=5)
        
        # Hex Code
        ctk.CTkLabel(row, text=color.hex_code, font=("Consolas", 13, "bold")).pack(side="left", padx=5)
        
        # Botones
        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.pack(side="right")
        
        ctk.CTkButton(actions, text="HEX", width=40, height=20, font=("Arial", 10, "bold"),
                      fg_color="#222222", hover_color="#444444", border_width=1, border_color="gray",
                      command=lambda: self.clip_svc.copy(color.hex_code)).pack(side="left", padx=2)
                      
        rgb_val = str(color.rgb_tuple)
        ctk.CTkButton(actions, text="RGB", width=40, height=20, font=("Arial", 10, "bold"),
                      fg_color="#222222", hover_color="#444444", border_width=1, border_color="gray",
                      command=lambda: self.clip_svc.copy(rgb_val)).pack(side="left", padx=2)

    def clear_history(self):
        for w in self.scroll_frame.winfo_children(): w.destroy()

    def on_close(self):
        self.zoom_active = False
        self.listener.stop()
        self.destroy()