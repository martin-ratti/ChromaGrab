import customtkinter as ctk
from src.core.use_cases import capture_color_use_case
from src.infrastructure.services import ScreenService, ClipboardService, InputListener

class ChromaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuración Ventana
        self.title("ChromaGrab 🎨")
        self.geometry("400x500")
        self.attributes("-topmost", True) # Siempre visible por defecto
        ctk.set_appearance_mode("Dark")
        
        # Servicios
        self.screen_svc = ScreenService()
        self.clip_svc = ClipboardService()
        
        # Listener (Hilos)
        self.listener = InputListener(on_trigger=self.perform_capture)
        self.listener.start()
        
        self._setup_ui()

    def _setup_ui(self):
        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=15, padx=20, fill="x")
        
        ctk.CTkLabel(self.header_frame, text="Presiona [INSERT] para capturar", 
                     font=("Roboto", 14, "bold"), text_color="gray").pack()

        # Área de Historial
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Historial de Colores")
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # Botones Footer
        self.footer = ctk.CTkFrame(self, height=50)
        self.footer.pack(fill="x", side="bottom")
        
        self.btn_clear = ctk.CTkButton(self.footer, text="Limpiar Historial", 
                                       fg_color="#FF5555", hover_color="#CC0000",
                                       command=self.clear_history)
        self.btn_clear.pack(pady=10)

    def perform_capture(self):
        """Método llamado por el hilo del teclado."""
        try:
            # Ejecutar caso de uso
            color = capture_color_use_case(self.screen_svc, self.clip_svc)
            
            # Actualizar GUI (Debe hacerse en el hilo principal)
            # 'after' programa la ejecución en el main loop de Tkinter
            self.after(0, lambda: self.add_color_to_list(color))
            
        except Exception as e:
            print(f"Error: {e}")

    def add_color_to_list(self, color):
        # Crear tarjeta de color
        card = ctk.CTkFrame(self.scroll_frame)
        card.pack(fill="x", pady=5)
        
        # Muestra visual del color
        color_box = ctk.CTkLabel(card, text="   ", fg_color=color.hex_code, width=30, corner_radius=5)
        color_box.pack(side="left", padx=10, pady=5)
        
        # Texto Hex
        lbl = ctk.CTkLabel(card, text=f"{color.hex_code}", font=("Consolas", 14, "bold"))
        lbl.pack(side="left", padx=10)
        
        # Indicador de copiado
        ctk.CTkLabel(card, text="Copiado!", text_color="green", font=("Arial", 10)).pack(side="right", padx=10)

    def clear_history(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

    def on_close(self):
        self.listener.stop()
        self.destroy()