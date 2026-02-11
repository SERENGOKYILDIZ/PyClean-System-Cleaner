import customtkinter as ctk
import os
import sys
import tkinter as tk
from config import *

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class TargetRow(ctk.CTkFrame):
    def __init__(self, master, target_path, **kwargs):
        super().__init__(master, fg_color=COLOR_CARD, corner_radius=8, height=45, **kwargs)
        self.target_path = target_path
        self.grid_columnconfigure(1, weight=1)
        
        self.status_indicator = ctk.CTkLabel(self, text="●", font=("Arial", 16), text_color="gray40", width=30)
        self.status_indicator.grid(row=0, column=0, padx=(10, 5), pady=10)
        
        display_name = target_path
        if "Temp" in target_path: display_name = "System Temp"
        elif "Prefetch" in target_path: display_name = "Prefetch Cache"
        else: display_name = os.path.basename(target_path) if os.path.basename(target_path) else target_path

        self.name_label = ctk.CTkLabel(self, text=display_name, font=("Roboto Medium", 13), text_color=COLOR_TEXT_MAIN, anchor="w")
        self.name_label.grid(row=0, column=1, sticky="w", padx=5)
        
        self.status_text = ctk.CTkLabel(self, text="Wait", font=("Segoe UI", 11), text_color=COLOR_TEXT_SEC, anchor="e", width=60)
        self.status_text.grid(row=0, column=2, padx=(5, 10))

    def set_status(self, status, message=None):
        if status == 'waiting':
            self.status_indicator.configure(text="●", text_color="gray40")
            self.status_text.configure(text="Wait", text_color=COLOR_TEXT_SEC)
        elif status == 'running':
            self.status_indicator.configure(text="🔄", text_color=COLOR_ACCENT) 
            self.status_text.configure(text="...", text_color=COLOR_ACCENT)
        elif status == 'done':
            self.status_indicator.configure(text="✔", text_color=COLOR_SUCCESS)
            self.status_text.configure(text="Done", text_color=COLOR_SUCCESS)
        elif status == 'error':
            self.status_indicator.configure(text="✕", text_color=COLOR_ERROR)
            self.status_text.configure(text="Err", text_color=COLOR_ERROR)

class DetailedMonitorCard(ctk.CTkFrame):
    def __init__(self, master, title, icon_text="📊", **kwargs):
        super().__init__(master, fg_color=COLOR_CARD, corner_radius=10, **kwargs)
        self.grid_columnconfigure(1, weight=1)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(header, text=icon_text, font=("Arial", 20)).pack(side="left", padx=(0, 10))
        self.title_label = ctk.CTkLabel(header, text=title, font=("Roboto Medium", 13, "bold"), text_color="gray90")
        self.title_label.pack(side="left")
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=15, pady=(0, 15))
        self.stats_frame.grid_columnconfigure(1, weight=1)
        self.row_idx = 0
        self.fields = {} 

    def add_row(self, label_text, value_text, is_dynamic=False, value_id=None, distinct_style=False):
        l = ctk.CTkLabel(self.stats_frame, text=label_text, font=("Segoe UI", 11), text_color=COLOR_TEXT_LABEL, anchor="w")
        l.grid(row=self.row_idx, column=0, sticky="w", pady=1, padx=(0, 10))
        v = ctk.CTkLabel(self.stats_frame, text=value_text, font=("Segoe UI", 12), text_color=COLOR_TEXT_MAIN, anchor="w")
        v.grid(row=self.row_idx, column=1, sticky="w", pady=1)
        if is_dynamic and value_id: self.fields[value_id] = v
        self.row_idx += 1

    def update_field(self, value_id, new_text, color=None):
        if value_id in self.fields:
            self.fields[value_id].configure(text=new_text)
            if color: self.fields[value_id].configure(text_color=color)

class AppUI(ctk.CTk):
    def __init__(self, engine, monitor, game_mgr):
        super().__init__()
        self.engine = engine
        self.monitor = monitor
        self.game_mgr = game_mgr
        
        self.title(f"System Optimizer v{VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(False, False)
        
        icon_path = resource_path(os.path.join("assets", "icon.ico"))
        if os.path.exists(icon_path): self.iconbitmap(icon_path)
            
        self.configure(fg_color=COLOR_BG_MAIN)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.target_rows = {}
        self._build_header()
        self._build_tabs()
        self._create_menu()
        self._populate_targets_list(self.engine.target_dirs)

    def _build_header(self):
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 5))
        ctk.CTkLabel(self.header_frame, text=APP_NAME, font=("Roboto Medium", 22, "bold"), text_color="white").pack(side="left")

    def _build_tabs(self):
        self.tab_view = ctk.CTkTabview(self, corner_radius=10, fg_color="transparent")
        self.tab_view.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.tab_view.add("Cleaner")
        self.tab_view.add("Performance")
        self.tab_view.add("Game Mode")
        self.tab_view.add("Monitor")
        self._setup_cleaner_tab()
        self._setup_performance_tab()
        self._setup_gamemode_tab()
        self._setup_monitor_tab()

    def _setup_cleaner_tab(self):
        tab = self.tab_view.tab("Cleaner")
        self.checklist_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent", label_text="Active Targets", height=200)
        self.checklist_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.btn_clean = ctk.CTkButton(tab, text="CLEAN SYSTEM", height=50, corner_radius=8, fg_color=COLOR_ACCENT, command=self.start_cleaning_process)
        self.btn_clean.pack(fill="x", padx=15, pady=15)
        self.clean_status = ctk.CTkLabel(tab, text="Ready", font=("Segoe UI", 11), text_color="gray50")
        self.clean_status.pack(pady=(0, 10))

    def _populate_targets_list(self, targets):
        # KRİTİK: Eski widgetları temizle
        for widget in self.checklist_frame.winfo_children():
            widget.destroy()
        self.target_rows = {}

        for target in targets:
            if target.strip():
                row = TargetRow(self.checklist_frame, target_path=target)
                row.pack(fill="x", pady=4, padx=5)
                self.target_rows[target] = row

    def _create_menu(self):
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)
        settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Edit Cleaning Paths", command=self.open_manage_targets)

    def open_manage_targets(self):
        self.target_window = ctk.CTkToplevel(self)
        self.target_window.title("Manage Targets")
        self.target_window.geometry("400x350")
        self.target_window.grab_set()
        
        self.targets_text = ctk.CTkTextbox(self.target_window, height=200)
        self.targets_text.pack(pady=10, padx=10, fill="both", expand=True)
        self.targets_text.insert("0.0", "\n".join(self.engine.target_dirs))
        
        btn_frame = ctk.CTkFrame(self.target_window, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkButton(btn_frame, text="SAVE & APPLY", fg_color="#2ECC71", command=self._save_targets).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text="CANCEL", fg_color="#E74C3C", command=self.target_window.destroy).pack(side="right", expand=True, padx=5)

    def _save_targets(self):
        raw_list = self.targets_text.get("1.0", "end").strip().split('\n')
        new_paths = self.engine.update_paths(raw_list)
        self._populate_targets_list(new_paths)
        self.target_window.destroy()

    def start_cleaning_process(self):
        if self.engine.running: return
        self.btn_clean.configure(state="disabled", text="CLEANING...")
        for row in self.target_rows.values(): row.set_status('waiting')
        
        self.engine.start_cleaning(
            update_callback=lambda: None,
            complete_callback=self.on_clean_complete,
            target_status_callback=self.on_target_update
        )

    def on_target_update(self, target, status, message):
        self.after(0, lambda: self.target_rows[target].set_status(status) if target in self.target_rows else None)

    def on_clean_complete(self, d, e, bytes_freed):
        self.after(0, lambda: self.clean_status.configure(text=f"Done! Freed {bytes_freed/1024/1024:.2f} MB", text_color=COLOR_SUCCESS))
        self.after(0, lambda: self.btn_clean.configure(state="normal", text="CLEAN SYSTEM"))

    # Diger tablar (setup_monitor_tab vb.) ve monitor guncelleme ayni kalacak...
    def _setup_performance_tab(self): pass
    def _setup_gamemode_tab(self): pass
    def _setup_monitor_tab(self): pass
    def update_monitor_ui(self, s, d): 
        if hasattr(self, 'lbl_cpu_usage'):
            self.lbl_cpu_usage.configure(text=f"CPU: {d.get('cpu_pct', 0)}%")