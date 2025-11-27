import customtkinter as ctk
from PIL import Image, ImageTk
import pyautogui
from src.core.use_cases import capture_color_use_case
from src.infrastructure.services import ScreenService, ClipboardService, InputListener
from src.infrastructure.repositories import JsonColorRepository # <--- NUEVO

class ZoomWindow(ctk.CTkToplevel):
    """Ventana flotante que muestra el zoom."""
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
        
        zoom = 8
        pixel_start = 10 * zoom  # 80
        pixel_end = pixel_start + zoom # 88
        
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
        self.geometry("480x650")
        ctk.set_appearance_mode("Dark")
        self.attributes("-topmost", True) 
        
        # Dependencias
        self.screen_svc = ScreenService()
        self.clip_svc = ClipboardService()
        self.repo = JsonColorRepository() # <--- NUEVO: Repositorio
        
        # Estado
        self.zoom_active = False
        self.zoom_window = None
        self.history = [] # <--- NUEVO: Estado en memoria
        
        # Listener
        self.listener = InputListener(on_trigger=self.trigger_capture)
        self.listener.start()
        
        self._setup_ui()
        
        # Cargar datos guardados al iniciar
        self.after(100, self.load_saved_history)

    def _setup_ui(self):
        # HEADER
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(self.header, text="ChromaGrab 2.1", font=("Segoe UI", 20, "bold")).pack(side="left")
        
        self.top_var = ctk.BooleanVar(value=True)
        self.switch_top = ctk.CTkSwitch(self.header, text="Fijar Ventana", 
                                    variable=self.top_var, command=self.toggle_top, font=("Segoe UI", 12))
        self.switch_top.pack(side="right")

        # CONTROLES
        self.controls = ctk.CTkFrame(self, fg_color="#2B2B2B")
        self.controls.pack(fill="x", padx=15, pady=10)
        
        self.zoom_var = ctk.BooleanVar(value=False)
        self.switch_zoom = ctk.CTkSwitch(self.controls, text="Activar Lupa (Live Zoom)", 
                                         variable=self.zoom_var, command=self.toggle_zoom,
                                         font=("Segoe UI", 13, "bold"), progress_color="#00E5FF")
        self.switch_zoom.pack(pady=15)
        
        ctk.CTkLabel(self.controls, text="[INSERT] para capturar", text_color="gray").pack(pady=(0, 10))

        # LISTA
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

    def load_saved_history(self):
        """Carga los colores del JSON y rellena la UI."""
        saved_colors = self.repo.load_all()
        self.history = saved_colors # Sincronizar estado
        
        # Renderizar en orden inverso (nuevos arriba) si prefieres, 
        # o normal. Aquí cargamos normal.
        for color in saved_colors:
            self.add_color_row_ui(color)

    def toggle_top(self):
        self.attributes("-topmost", self.top_var.get())

    def toggle_zoom(self):
        if self.zoom_var.get():
            self.zoom_active = True
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

    def trigger_capture(self):
        self.after(0, self.process_capture)

    def process_capture(self):
        try:
            # 1. Capturar
            color = capture_color_use_case(self.screen_svc)
            
            # 2. Actualizar Estado (Memoria)
            # Insertamos al principio para que sea LIFO (Last In First Out) visualmente? 
            # Mejor append normal y scroll, o insert(0). Usaremos append normal.
            self.history.append(color)
            
            # 3. Guardar en Disco (Persistencia)
            self.repo.save_all(self.history)
            
            # 4. Actualizar UI
            self.add_color_row_ui(color)
            
            # 5. Copiar (Feedback)
            self.clip_svc.copy(color.hex_code)
            
        except Exception as e:
            print(e)

    def add_color_row_ui(self, color):
        """Solo dibuja la fila en la GUI (separado de la lógica de datos)."""
        row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        row.pack(fill="x", pady=2)
        
        try:
            box = ctk.CTkLabel(row, text="", fg_color=color.hex_code, width=40, height=25, corner_radius=4)
        except:
            box = ctk.CTkLabel(row, text="?", width=40)
        box.pack(side="left", padx=5)
        
        ctk.CTkLabel(row, text=color.hex_code, font=("Consolas", 13, "bold")).pack(side="left", padx=5)
        
        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.pack(side="right")
        
        ctk.CTkButton(actions, text="HEX", width=40, height=20, font=("Arial", 10, "bold"),
                      fg_color="#222222", hover_color="#444444", border_width=1, border_color="gray",
                      command=lambda: self.clip_svc.copy(color.hex_code)).pack(side="left", padx=2)
                      
        rgb_val = str(color.rgb_tuple)
        ctk.CTkButton(actions, text="RGB", width=40, height=20, font=("Arial", 10, "bold"),
                      fg_color="#222222", hover_color="#444444", border_width=1, border_color="gray",
                      command=lambda: self.clip_svc.copy(rgb_val)).pack(side="left", padx=2)
        
        # Auto-scroll hacia abajo para ver el nuevo
        # self.scroll_frame._parent_canvas.yview_moveto(1.0) 

    def clear_history(self):
        # 1. Limpiar UI
        for w in self.scroll_frame.winfo_children(): w.destroy()
        # 2. Limpiar Estado
        self.history.clear()
        # 3. Limpiar Disco
        self.repo.save_all([])

    def on_close(self):
        self.zoom_active = False
        self.listener.stop()
        self.destroy()