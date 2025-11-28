import customtkinter as ctk
from PIL import Image, ImageTk
import pyautogui
import winsound
import threading
from src.core.use_cases import capture_color_use_case
from src.infrastructure.services import ScreenService, ClipboardService, InputListener, SoundService
from src.infrastructure.repositories import JsonColorRepository

THEME = {
    "bg_main": "#121212",
    "bg_card": "#1E1E1E",
    "primary": "#7C4DFF",
    "primary_hover": "#651FFF",
    "cyan": "#00E5FF",
    "text_main": "#FFFFFF",
    "danger": "#CF6679",
    "success": "#00E676"
}

HISTORY_LIMIT = 50 

class ZoomWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True) 
        self.attributes("-topmost", True) 
        self.geometry("160x160") 
        
        self.canvas = ctk.CTkCanvas(self, width=160, height=160, 
                                    highlightthickness=2, highlightbackground=THEME["cyan"],
                                    bg="black")
        self.canvas.pack(fill="both", expand=True)
        
        self.image_obj = self.canvas.create_image(0, 0, anchor="nw")
        
        center = 80
        zoom = 8
        self.rect_obj = self.canvas.create_rectangle(
            center, center, center + zoom, center + zoom, 
            outline=THEME["danger"], width=2
        )
        
    def update_image(self, pil_image):
        self.photo = ImageTk.PhotoImage(pil_image)
        self.canvas.itemconfig(self.image_obj, image=self.photo)
        self.canvas.tag_raise(self.rect_obj)

    def move_near_mouse(self):
        x, y = pyautogui.position()
        self.geometry(f"+{int(x) + 25}+{int(y) + 25}")

class ChromaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("ChromaGrab")
        self.geometry("540x680")
        ctk.set_appearance_mode("Dark")
        self.configure(fg_color=THEME["bg_main"])
        self.attributes("-topmost", True) 
        
        self.screen_svc = ScreenService()
        self.clip_svc = ClipboardService()
        self.sound_svc = SoundService()
        self.repo = JsonColorRepository()
        
        self.zoom_active = False
        self.zoom_window = None
        self.history = []
        self.widget_map = {}
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
        self.expanded_container = ctk.CTkFrame(self, fg_color="transparent")
        self.expanded_container.pack(fill="both", expand=True)

        self.header = ctk.CTkFrame(self.expanded_container, fg_color="transparent")
        self.header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(self.header, text="Chroma", font=("Impact", 26), text_color=THEME["text_main"]).pack(side="left")
        ctk.CTkLabel(self.header, text="Grab", font=("Impact", 26), text_color=THEME["primary"]).pack(side="left")
        
        self.btn_compact = ctk.CTkButton(self.header, text="Modo Barra ↗", width=100, height=28, 
                                         fg_color=THEME["bg_card"], hover_color="#333", 
                                         font=("Segoe UI", 11, "bold"), command=self.toggle_compact_mode)
        self.btn_compact.pack(side="right")

        self.controls = ctk.CTkFrame(self.expanded_container, fg_color=THEME["bg_card"], corner_radius=10)
        self.controls.pack(fill="x", padx=20, pady=10)
        
        self.zoom_var = ctk.BooleanVar(value=False)
        self.switch_zoom = ctk.CTkSwitch(self.controls, text="Lupa (Alt + Z)", 
                                         variable=self.zoom_var, command=self.toggle_zoom_ui,
                                         font=("Segoe UI", 13, "bold"), 
                                         progress_color=THEME["primary"])
        self.switch_zoom.pack(pady=15)
        
        ctk.CTkLabel(self.controls, text="[INSERT] para capturar", text_color="gray").pack(pady=(0, 15))

        self.list_header = ctk.CTkFrame(self.expanded_container, fg_color="transparent", height=20)
        self.list_header.pack(fill="x", padx=30)
        ctk.CTkLabel(self.list_header, text="Color", width=50, anchor="w", text_color="gray").pack(side="left")
        ctk.CTkLabel(self.list_header, text="Código", width=100, anchor="w", text_color="gray").pack(side="left", padx=5)
        ctk.CTkLabel(self.list_header, text="Copiar", width=100, anchor="e", text_color="gray").pack(side="right")

        self.scroll_frame = ctk.CTkScrollableFrame(self.expanded_container, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.footer_frame = ctk.CTkFrame(self.expanded_container, fg_color="transparent")
        self.footer_frame.pack(fill="x", pady=20)
        self.btn_clear = ctk.CTkButton(self.footer_frame, text="Borrar Todo", 
                                       fg_color=THEME["bg_card"], text_color=THEME["danger"],
                                       hover_color="#2A2A2A", border_width=1, border_color=THEME["danger"],
                                       command=self.clear_all_history)
        self.btn_clear.pack()

        self.compact_container = ctk.CTkFrame(self, fg_color=THEME["bg_main"], corner_radius=0)
        
        self.compact_color_box = ctk.CTkLabel(self.compact_container, text="", width=40, height=40, bg_color="gray", corner_radius=5)
        self.compact_color_box.pack(side="left", padx=(15, 10), pady=10)
        
        self.compact_center = ctk.CTkFrame(self.compact_container, fg_color="transparent")
        self.compact_center.pack(side="left", fill="y", pady=5)
        
        self.compact_hex_lbl = ctk.CTkLabel(self.compact_center, text="#------", font=("Consolas", 15, "bold"), text_color=THEME["text_main"])
        self.compact_hex_lbl.pack(anchor="w")
        
        self.compact_btns = ctk.CTkFrame(self.compact_center, fg_color="transparent")
        self.compact_btns.pack(anchor="w")
        
        self.btn_comp_hex = ctk.CTkButton(self.compact_btns, text="HEX", width=45, height=22, 
                                          font=("Arial", 10, "bold"), fg_color=THEME["bg_card"], hover_color="#333")
        self.btn_comp_hex.configure(command=lambda: self.copy_last_hex(self.btn_comp_hex))
        self.btn_comp_hex.pack(side="left", padx=(0, 5))
        
        self.btn_comp_rgb = ctk.CTkButton(self.compact_btns, text="RGB", width=45, height=22, 
                                          font=("Arial", 10, "bold"), fg_color=THEME["bg_card"], hover_color="#333")
        self.btn_comp_rgb.configure(command=lambda: self.copy_last_rgb(self.btn_comp_rgb))
        self.btn_comp_rgb.pack(side="left")

        self.btn_expand = ctk.CTkButton(self.compact_container, text="Expandir ↙", width=80, height=28, 
                                        fg_color=THEME["bg_card"], hover_color="#333", 
                                        text_color=THEME["primary"], font=("Segoe UI", 11, "bold"),
                                        command=self.toggle_compact_mode)
        self.btn_expand.pack(side="right", padx=15)

    def process_capture(self):
        try:
            self.sound_svc.play_capture()
            color = capture_color_use_case(self.screen_svc)
            
            self.history.insert(0, color)
            if len(self.history) > HISTORY_LIMIT:
                removed = self.history.pop()
                # Borramos visualmente si existe (aunque con refresh_list no es critico, ahorra memoria)
                if removed.id in self.widget_map:
                    self.widget_map[removed.id].destroy()
                    del self.widget_map[removed.id]

            self._save_history_async()
            
            if self.is_compact:
                self.update_compact_ui(color)
                self._flash_button(self.btn_comp_hex, "HEX")
            else:
                self.refresh_list_ui()
            
            self.clip_svc.copy(color.hex_code)
            self.show_toast(f"Copiado: {color.hex_code}", color.hex_code)
            
        except Exception as e:
            print(f"Error: {e}")

    def load_saved_history(self):
        self.history = self.repo.load_all()
        if self.history: self.last_capture = self.history[0]
        self.refresh_list_ui()

    def refresh_list_ui(self):
        self.widget_map = {}
        for w in self.scroll_frame.winfo_children(): w.destroy()
        for color in self.history:
            self.create_row_widget(color)

    def create_row_widget(self, color):
        row = ctk.CTkFrame(self.scroll_frame, fg_color=THEME["bg_card"], corner_radius=8)
        row.pack(fill="x", pady=4)
        self.widget_map[color.id] = row 
        
        try:
            box = ctk.CTkLabel(row, text="", fg_color=color.hex_code, width=45, height=35, corner_radius=6)
        except:
            box = ctk.CTkLabel(row, text="?", width=45)
        box.pack(side="left", padx=10, pady=8)
        
        ctk.CTkLabel(row, text=color.hex_code, font=("Consolas", 16, "bold"), text_color=THEME["text_main"]).pack(side="left", padx=10)
        
        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.pack(side="right", padx=10)
        
        btn_hex = ctk.CTkButton(actions, text="HEX", width=50, height=24, font=("Arial", 11, "bold"),
                      fg_color=THEME["primary"], hover_color=THEME["primary_hover"])
        btn_hex.configure(command=lambda b=btn_hex: self.copy_with_feedback(color.hex_code, b, "HEX"))
        btn_hex.pack(side="left", padx=3)
        
        rgb_str = str(color.rgb_tuple)
        btn_rgb = ctk.CTkButton(actions, text="RGB", width=50, height=24, font=("Arial", 11, "bold"),
                      fg_color="#333", hover_color="#444", border_width=1, border_color=THEME["primary"])
        btn_rgb.configure(command=lambda b=btn_rgb: self.copy_with_feedback(rgb_str, b, "RGB"))
        btn_rgb.pack(side="left", padx=3)
        
        ctk.CTkButton(actions, text="×", width=25, height=24, font=("Arial", 16),
                      fg_color="transparent", hover_color=THEME["bg_main"], text_color="#666",
                      command=lambda c_id=color.id: self.delete_by_id(c_id)).pack(side="left", padx=(5, 0))

    def delete_by_id(self, color_id):
        # 1. Borrado Visual Quirúrgico (Instantáneo)
        if color_id in self.widget_map:
            self.widget_map[color_id].destroy()
            del self.widget_map[color_id]
        
        # 2. Actualización de Datos
        self.history = [c for c in self.history if c.id != color_id]
        
        # 3. Guardado Async (No bloquea UI)
        self._save_history_async()

    def _save_history_async(self):
        threading.Thread(target=self.repo.save_all, args=(self.history,), daemon=True).start()

    def copy_with_feedback(self, text, button_widget, original_text):
        if not text: return
        self.clip_svc.copy(text)
        self._flash_button(button_widget, original_text)

    def _flash_button(self, button, original_text):
        if not button.winfo_exists(): return
        original_fg = button.cget("fg_color")
        original_hover = button.cget("hover_color")
        button.configure(text="✔", fg_color=THEME["success"], hover_color=THEME["success"], text_color="black")
        
        def revert():
            try:
                if button.winfo_exists():
                    button.configure(text=original_text, fg_color=original_fg, hover_color=original_hover, text_color="white")
            except: pass
        self.after(1000, revert)

    def copy_last_hex(self, btn):
        if self.last_capture: self.copy_with_feedback(self.last_capture.hex_code, btn, "HEX")

    def copy_last_rgb(self, btn):
        if self.last_capture: self.copy_with_feedback(str(self.last_capture.rgb_tuple), btn, "RGB")

    def toggle_compact_mode(self):
        self.is_compact = not self.is_compact
        if self.is_compact:
            self.expanded_container.pack_forget()
            self.compact_container.pack(fill="both", expand=True)
            self.geometry("340x65") 
            self.attributes("-topmost", True)
            if self.history: self.update_compact_ui(self.history[0])
        else:
            self.compact_container.pack_forget()
            self.expanded_container.pack(fill="both", expand=True)
            self.geometry("540x680")
            self.refresh_list_ui()

    def update_compact_ui(self, color):
        self.last_capture = color
        if self.is_compact:
            try: self.compact_color_box.configure(fg_color=color.hex_code)
            except: pass
            self.compact_hex_lbl.configure(text=color.hex_code)

    def show_toast(self, message, color_hex):
        if self.is_compact: return
        toast = ctk.CTkFrame(self, fg_color="#333333", corner_radius=20, border_width=1, border_color="#555")
        toast.place(relx=0.5, rely=0.90, anchor="center")
        try: dot = ctk.CTkLabel(toast, text="●", font=("Arial", 20), text_color=color_hex)
        except: dot = ctk.CTkLabel(toast, text="●", font=("Arial", 20), text_color="white")
        dot.pack(side="left", padx=(15, 5), pady=5)
        lbl = ctk.CTkLabel(toast, text=message, font=("Segoe UI", 12, "bold"), text_color="white")
        lbl.pack(side="left", padx=(0, 15), pady=5)
        self.after(2000, toast.destroy)

    def clear_all_history(self):
        for w in self.scroll_frame.winfo_children(): w.destroy()
        self.widget_map.clear()
        self.history.clear()
        self._save_history_async()

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

    def _zoom_loop(self):
        if self.zoom_active and self.zoom_window:
            img = self.screen_svc.get_zoom_image(radius=10, zoom_factor=8)
            self.zoom_window.update_image(img)
            self.zoom_window.move_near_mouse()
            self.after(30, self._zoom_loop)

    def on_close(self):
        self.zoom_active = False
        self.listener.stop()
        self.destroy()