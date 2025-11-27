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
        self.geometry(f"+{int(x) + 20}+{int(y) + 20}")

class ChromaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("ChromaGrab")
        self.geometry("520x650")
        ctk.set_appearance_mode("Dark")
        self.attributes("-topmost", True) 
        
        self.screen_svc = ScreenService()
        self.clip_svc = ClipboardService()
        self.sound_svc = SoundService()
        self.repo = JsonColorRepository()
        
        self.zoom_active = False
        self.zoom_window = None
        self.history = []
        self.is_compact = False
        self.last_capture = None 
        
        self.listener = InputListener(
            on_capture=self.trigger_capture,
            on_toggle_zoom=self.trigger_zoom_toggle
        )
        self.listener.start()
        
        self._setup_ui()
        self.after(100, self.load_saved_history)

    def _setup_ui(self):
        # === MODO EXPANDIDO ===
        self.expanded_container = ctk.CTkFrame(self, fg_color="transparent")
        self.expanded_container.pack(fill="both", expand=True)

        self.header = ctk.CTkFrame(self.expanded_container, fg_color="transparent")
        self.header.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(self.header, text="ChromaGrab 2.6", font=("Segoe UI", 20, "bold")).pack(side="left")
        
        self.btn_compact = ctk.CTkButton(self.header, text="Modo Barra ↗", width=90, height=25, 
                                         fg_color="#333", command=self.toggle_compact_mode)
        self.btn_compact.pack(side="right")

        self.controls = ctk.CTkFrame(self.expanded_container, fg_color="#2B2B2B")
        self.controls.pack(fill="x", padx=15, pady=10)
        
        self.zoom_var = ctk.BooleanVar(value=False)
        self.switch_zoom = ctk.CTkSwitch(self.controls, text="Lupa (Alt + Z)", 
                                         variable=self.zoom_var, command=self.toggle_zoom_ui,
                                         font=("Segoe UI", 13, "bold"), progress_color="#00E5FF")
        self.switch_zoom.pack(pady=10)
        
        ctk.CTkLabel(self.controls, text="[INSERT] para capturar", text_color="gray").pack(pady=(0, 10))

        self.scroll_frame = ctk.CTkScrollableFrame(self.expanded_container, fg_color="#1A1A1A")
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=5)

        self.footer_frame = ctk.CTkFrame(self.expanded_container, fg_color="transparent")
        self.footer_frame.pack(fill="x", pady=10)
        self.btn_clear = ctk.CTkButton(self.footer_frame, text="Borrar Todo", 
                                       fg_color="#333333", hover_color="#C62828",
                                       command=self.clear_all_history)
        self.btn_clear.pack()

        # === MODO COMPACTO ===
        self.compact_container = ctk.CTkFrame(self, fg_color="#1A1A1A", corner_radius=0)
        
        self.compact_color_box = ctk.CTkLabel(self.compact_container, text="", width=40, height=40, bg_color="gray", corner_radius=5)
        self.compact_color_box.pack(side="left", padx=(15, 10), pady=10)
        
        self.compact_center = ctk.CTkFrame(self.compact_container, fg_color="transparent")
        self.compact_center.pack(side="left", fill="y", pady=5)
        
        self.compact_hex_lbl = ctk.CTkLabel(self.compact_center, text="#------", font=("Consolas", 14, "bold"))
        self.compact_hex_lbl.pack(anchor="w")
        
        self.compact_btns = ctk.CTkFrame(self.compact_center, fg_color="transparent")
        self.compact_btns.pack(anchor="w")
        
        # Botones Compactos
        self.btn_comp_hex = ctk.CTkButton(self.compact_btns, text="HEX", width=40, height=20, 
                                          font=("Arial", 9, "bold"), fg_color="#222", hover_color="#444")
        # Usamos lambda tardío para pasar el propio botón
        self.btn_comp_hex.configure(command=lambda: self.copy_last_hex(self.btn_comp_hex))
        self.btn_comp_hex.pack(side="left", padx=(0, 5))
        
        self.btn_comp_rgb = ctk.CTkButton(self.compact_btns, text="RGB", width=40, height=20, 
                                          font=("Arial", 9, "bold"), fg_color="#222", hover_color="#444")
        self.btn_comp_rgb.configure(command=lambda: self.copy_last_rgb(self.btn_comp_rgb))
        self.btn_comp_rgb.pack(side="left")

        self.btn_expand = ctk.CTkButton(self.compact_container, text="⬜", width=30, height=30, 
                                        fg_color="#333", command=self.toggle_compact_mode)
        self.btn_expand.pack(side="right", padx=15)

    # --- Lógica de Copiado Unificada ---
    def copy_with_feedback(self, text, button_widget, original_text):
        """Copia al portapapeles y hace parpadear el botón visualmente."""
        if not text: return
        
        # 1. Copiar
        self.clip_svc.copy(text)
        
        # 2. Flash Visual (Sin sonido)
        self._flash_button(button_widget, original_text)

    def _flash_button(self, button, original_text):
        if not button.winfo_exists(): return
        
        original_fg = "#222"
        original_hover = "#444"
        
        # Estado "Éxito"
        button.configure(text="✔", fg_color="#2E7D32", hover_color="#1B5E20")
        
        def revert():
            try:
                if button.winfo_exists():
                    button.configure(text=original_text, fg_color=original_fg, hover_color=original_hover)
            except: pass
        
        self.after(1000, revert)

    def copy_last_hex(self, btn_widget):
        if self.last_capture:
            self.copy_with_feedback(self.last_capture.hex_code, btn_widget, "HEX")

    def copy_last_rgb(self, btn_widget):
        if self.last_capture:
            self.copy_with_feedback(str(self.last_capture.rgb_tuple), btn_widget, "RGB")

    def toggle_compact_mode(self):
        self.is_compact = not self.is_compact
        if self.is_compact:
            self.expanded_container.pack_forget()
            self.compact_container.pack(fill="both", expand=True)
            self.geometry("320x65") 
            self.attributes("-topmost", True)
            if self.history:
                self.update_compact_ui(self.history[-1])
        else:
            self.compact_container.pack_forget()
            self.expanded_container.pack(fill="both", expand=True)
            self.geometry("520x650")
            self.refresh_list_ui()

    def update_compact_ui(self, color):
        self.last_capture = color
        if self.is_compact:
            try:
                self.compact_color_box.configure(fg_color=color.hex_code)
            except: pass
            self.compact_hex_lbl.configure(text=color.hex_code)

    def show_toast(self, message, color_hex):
        if self.is_compact: return

        toast = ctk.CTkFrame(self, fg_color="#333333", corner_radius=20, border_width=1, border_color="#555")
        toast.place(relx=0.5, rely=0.85, anchor="center")
        try:
            dot = ctk.CTkLabel(toast, text="●", font=("Arial", 20), text_color=color_hex)
        except:
            dot = ctk.CTkLabel(toast, text="●", font=("Arial", 20), text_color="white")
        dot.pack(side="left", padx=(15, 5), pady=5)
        lbl = ctk.CTkLabel(toast, text=message, font=("Segoe UI", 12, "bold"), text_color="white")
        lbl.pack(side="left", padx=(0, 15), pady=5)
        
        # IMPORTANTE: Eliminada la llamada a sound_svc aquí para evitar sonido doble
        self.after(2000, toast.destroy)

    def process_capture(self):
        try:
            # ÚNICO lugar donde suena el sonido de captura
            self.sound_svc.play_capture()
            
            color = capture_color_use_case(self.screen_svc)
            
            self.history.append(color)
            self.repo.save_all(self.history)
            
            if self.is_compact:
                self.update_compact_ui(color)
                # Flash visual en el botón HEX (formato default)
                self._flash_button(self.btn_comp_hex, "HEX")
            else:
                self.refresh_list_ui()
            
            self.clip_svc.copy(color.hex_code)
            self.show_toast(f"Copiado: {color.hex_code}", color.hex_code)
            
        except Exception as e:
            print(e)

    def _zoom_loop(self):
        if self.zoom_active and self.zoom_window:
            img = self.screen_svc.get_zoom_image(radius=10, zoom_factor=8)
            self.zoom_window.update_image(img)
            self.zoom_window.move_near_mouse()
            self.after(30, self._zoom_loop)

    def load_saved_history(self):
        self.history = self.repo.load_all()
        if self.history:
            self.last_capture = self.history[-1]
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
        
        # Botones de la lista con Feedback Visual
        btn_hex = ctk.CTkButton(actions, text="HEX", width=40, height=22, font=("Arial", 10, "bold"),
                      fg_color="#222222", hover_color="#444444", border_width=1, border_color="gray")
        btn_hex.configure(command=lambda b=btn_hex: self.copy_with_feedback(color.hex_code, b, "HEX"))
        btn_hex.pack(side="left", padx=2)
        
        rgb_val = str(color.rgb_tuple)
        btn_rgb = ctk.CTkButton(actions, text="RGB", width=40, height=22, font=("Arial", 10, "bold"),
                      fg_color="#222222", hover_color="#444444", border_width=1, border_color="gray")
        btn_rgb.configure(command=lambda b=btn_rgb: self.copy_with_feedback(rgb_val, b, "RGB"))
        btn_rgb.pack(side="left", padx=2)
        
        ctk.CTkButton(actions, text="✕", width=25, height=22, font=("Arial", 12, "bold"),
                      fg_color="transparent", hover_color="#C62828", text_color="#FF5555",
                      command=lambda idx=real_index: self.delete_single_color(idx)).pack(side="left", padx=(5, 0))

    def delete_single_color(self, index):
        if 0 <= index < len(self.history):
            del self.history[index]
            self.repo.save_all(self.history)
            self.refresh_list_ui()

    def trigger_zoom_toggle(self):
        self.after(0, self._sync_zoom_toggle)

    def _sync_zoom_toggle(self):
        current = self.zoom_var.get()
        self.zoom_var.set(not current)
        self.toggle_zoom_ui()

    def toggle_zoom_ui(self):
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

    def trigger_capture(self):
        self.after(0, self.process_capture)

    def clear_all_history(self):
        self.history.clear()
        self.repo.save_all([])
        self.refresh_list_ui()

    def on_close(self):
        self.zoom_active = False
        self.listener.stop()
        self.destroy()