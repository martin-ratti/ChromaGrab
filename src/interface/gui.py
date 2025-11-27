import customtkinter as ctk
from src.core.use_cases import capture_color_use_case
from src.infrastructure.services import ScreenService, ClipboardService, InputListener

class ChromaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("ChromaGrab")
        self.geometry("480x600")
        ctk.set_appearance_mode("Dark")
        self.attributes("-topmost", True) 
        
        # Inyección de dependencias
        self.screen_svc = ScreenService()
        self.clip_svc = ClipboardService()
        
        # Hilo de escucha
        self.listener = InputListener(on_trigger=self.trigger_capture)
        self.listener.start()
        
        self._setup_ui()

    def _setup_ui(self):
        # --- HEADER ---
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(self.header, text="Capturador de Color", 
                     font=("Segoe UI", 20, "bold")).pack(side="left")
        
        # Switch Siempre Visible
        self.top_var = ctk.BooleanVar(value=True)
        self.switch = ctk.CTkSwitch(self.header, text="Siempre Visible", 
                                    variable=self.top_var, command=self.toggle_top,
                                    font=("Segoe UI", 12))
        self.switch.pack(side="right")

        # Instrucción
        ctk.CTkLabel(self, text="Mueve el mouse y presiona [INSERT]", 
                     text_color="gray").pack(pady=(0, 10))

        # --- LISTA ---
        # Encabezados de la lista
        self.list_header = ctk.CTkFrame(self, fg_color="transparent", height=30)
        self.list_header.pack(fill="x", padx=25)
        ctk.CTkLabel(self.list_header, text="Color", width=60, anchor="w").pack(side="left")
        ctk.CTkLabel(self.list_header, text="Código", width=120, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(self.list_header, text="Copiar Formato", width=100, anchor="e").pack(side="right")

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#2B2B2B")
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # --- FOOTER ---
        self.btn_clear = ctk.CTkButton(self, text="Limpiar Historial", 
                                       fg_color="#333333", hover_color="#C62828",
                                       command=self.clear_history)
        self.btn_clear.pack(pady=15)

    def toggle_top(self):
        self.attributes("-topmost", self.top_var.get())

    def trigger_capture(self):
        self.after(0, self.process_capture)

    def process_capture(self):
        try:
            # 1. Capturar (Use Case Puro)
            color = capture_color_use_case(self.screen_svc)
            
            # 2. Agregar a la UI
            self.add_color_row(color)
            
            # 3. Copiar HEX por defecto (feedback inmediato)
            self.copy_to_clip(color.hex_code)
            
        except Exception as e:
            print(f"Error: {e}")

    def add_color_row(self, color):
        # Contenedor de la fila
        row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        row.pack(fill="x", pady=5)
        
        # 1. Muestra de Color
        try:
            box = ctk.CTkLabel(row, text="", fg_color=color.hex_code, 
                               width=40, height=30, corner_radius=6)
        except:
            box = ctk.CTkLabel(row, text="?", width=40)
        box.pack(side="left", padx=(5, 10))
        
        # 2. Código Visual (Solo informativo)
        code_lbl = ctk.CTkLabel(row, text=color.hex_code, 
                                font=("Consolas", 14, "bold"))
        code_lbl.pack(side="left")

        # 3. Botones de Acción (Derecha)
        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.pack(side="right")

        # Botón HEX
        btn_hex = ctk.CTkButton(actions, text="HEX", width=50, height=25,
                                font=("Segoe UI", 11, "bold"),
                                fg_color="#1E88E5", hover_color="#1565C0",
                                command=lambda: self.copy_to_clip(color.hex_code))
        btn_hex.pack(side="left", padx=2)

        # Botón RGB
        rgb_str = f"{color.rgb_tuple}"
        btn_rgb = ctk.CTkButton(actions, text="RGB", width=50, height=25,
                                font=("Segoe UI", 11, "bold"),
                                fg_color="#43A047", hover_color="#2E7D32",
                                command=lambda: self.copy_to_clip(rgb_str))
        btn_rgb.pack(side="left", padx=2)

    def copy_to_clip(self, text):
        self.clip_svc.copy(text)
        # Podríamos poner un toast notification aquí en el futuro
        # Por ahora, sabemos que funciona.

    def clear_history(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

    def on_close(self):
        self.listener.stop()
        self.destroy()