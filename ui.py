import customtkinter as ctk
import os
import threading
from config import *

class TargetRow(ctk.CTkFrame):
    def __init__(self, master, target_path, **kwargs):
        super().__init__(master, fg_color=COLOR_CARD, corner_radius=8, height=45, **kwargs)
        self.target_path = target_path
        self.grid_columnconfigure(1, weight=1)
        
        self.status_indicator = ctk.CTkLabel(self, text="●", font=("Arial", 16), text_color="gray40", width=30)
        self.status_indicator.grid(row=0, column=0, padx=(10, 5), pady=10)
        
        display_name = target_path
        if "%TEMP%" in target_path: display_name = "System Temp"
        elif "Prefetch" in target_path: display_name = "Prefetch Cache"
        elif "Recent" in target_path: display_name = "Recent Items"
        elif "Downloads" in target_path: display_name = "Downloads"
        elif "recycle" in target_path.lower(): display_name = "Recycle Bin"
        else:
             display_name = os.path.basename(target_path) if os.path.basename(target_path) else target_path

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

    def add_row(self, label_text, value_text, is_dynamic=False, value_id=None, distinct_style=False, copyable=False):
        lbl_clr = COLOR_NEON_BLUE if distinct_style else COLOR_TEXT_LABEL
        val_clr = COLOR_USAGE_HIGHLIGHT if distinct_style else COLOR_TEXT_MAIN
        font_style = ("Segoe UI", 12, "bold") if distinct_style else ("Segoe UI", 11)
        
        l = ctk.CTkLabel(self.stats_frame, text=label_text, font=font_style, text_color=lbl_clr, anchor="w")
        l.grid(row=self.row_idx, column=0, sticky="w", pady=1, padx=(0, 10))
        
        v = ctk.CTkLabel(self.stats_frame, text=value_text, font=("Segoe UI", 12), text_color=val_clr, anchor="w", wraplength=350)
        v.grid(row=self.row_idx, column=1, sticky="w", pady=1)
        
        if copyable:
            v.configure(cursor="hand2")
            v.bind("<Button-1>", lambda e, label=v: self.copy_to_clipboard(label))
            ctk.CTkLabel(self.stats_frame, text="(Copy)", font=("Arial", 9), text_color="gray40").grid(row=self.row_idx, column=2, sticky="e", padx=5)

        if is_dynamic and value_id:
            self.fields[value_id] = v
        
        self.row_idx += 1

    def copy_to_clipboard(self, label_widget):
        text = label_widget.cget("text")
        if not text or text == "Searching...": return
        
        self.master.clipboard_clear()
        self.master.clipboard_append(text)
        self.master.update()
        
        original_color = label_widget.cget("text_color")
        label_widget.configure(text_color=COLOR_SUCCESS, text="Copied! ✓")
        
        def restore():
            label_widget.configure(text_color=original_color, text=text)
        self.after(1000, restore)

    def update_field(self, value_id, new_text, color=None):
        if value_id in self.fields:
            if self.fields[value_id].cget("text") == "Copied! ✓": return
            if color:
                self.fields[value_id].configure(text=new_text, text_color=color)
            else:
                self.fields[value_id].configure(text=new_text)

class AppUI(ctk.CTk):
    def __init__(self, engine, monitor, game_mgr):
        super().__init__()
        self.engine = engine
        self.monitor = monitor
        self.game_mgr = game_mgr
        
        self.title("System Optimizer")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.configure(fg_color=COLOR_BG_MAIN)
        self.resizable(False, False)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.target_rows = {}
        
        self._build_header()
        self._build_tabs()

        # Connect Engine Callbacks
        self.engine_targets = self.engine.load_targets()
        self._populate_targets()
        
    def _build_header(self):
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 5))
        
        title = ctk.CTkLabel(self.header_frame, text=APP_NAME, font=("Roboto Medium", 22, "bold"), text_color="white")
        title.pack(side="left")
        
        ver = ctk.CTkLabel(self.header_frame, text=f"v{VERSION}", font=("Segoe UI", 12), text_color="gray60")
        ver.pack(side="left", padx=10, pady=(10, 0))

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
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        self.checklist_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent", label_text="")
        self.checklist_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.btn_clean = ctk.CTkButton(
            tab, text="CLEAN SYSTEM", height=50, corner_radius=8,
            font=("Roboto Medium", 15), fg_color=COLOR_ACCENT, hover_color="#327ab3",
            command=self.start_cleaning_process
        )
        self.btn_clean.grid(row=1, column=0, sticky="ew", padx=15, pady=15)
        self.clean_status = ctk.CTkLabel(tab, text="Ready", font=("Segoe UI", 11), text_color="gray50")
        self.clean_status.grid(row=2, column=0, pady=(0, 10))

    def _setup_performance_tab(self):
        tab = self.tab_view.tab("Performance")
        tab.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(tab, text="REAL-TIME MONITOR", font=("Roboto Medium", 14), text_color="gray60").pack(pady=(20, 10))
        
        self.lbl_ram_usage = ctk.CTkLabel(tab, text="RAM: --%", font=("Segoe UI", 32, "bold"), text_color=COLOR_ACCENT)
        self.lbl_ram_usage.pack(pady=10)
        self.lbl_cpu_usage = ctk.CTkLabel(tab, text="CPU: --%", font=("Segoe UI", 14), text_color="gray70")
        self.lbl_cpu_usage.pack(pady=(0, 20))
        
        self.perf_log = ctk.CTkTextbox(tab, height=150, fg_color="#151515", text_color="gray80", font=("Consolas", 11))
        self.perf_log.pack(fill="x", padx=15, pady=10)
        self.perf_log.insert("end", "System Monitor Active...\n")
        self.perf_log.configure(state="disabled")
        
        self.btn_boost = ctk.CTkButton(
            tab, text="BOOST NOW", height=45, corner_radius=8,
            font=("Roboto Medium", 14), fg_color="#2b2b2b", border_width=1, border_color=COLOR_ACCENT,
            hover_color="#333333", command=self.boost_system
        )
        self.btn_boost.pack(side="bottom", fill="x", padx=15, pady=20)

    def _setup_gamemode_tab(self):
        tab = self.tab_view.tab("Game Mode")
        tab.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(tab, text="🎮", font=("Arial", 64)).pack(pady=(40, 10))
        ctk.CTkLabel(tab, text="GAME MODE", font=("Roboto Medium", 20, "bold")).pack(pady=5)
        ctk.CTkLabel(tab, text="Stops background services for performance.", font=("Segoe UI", 12), text_color="gray70").pack(pady=20)
        
        self.game_switch = ctk.CTkSwitch(
            tab, text="ENABLE GAME MODE", font=("Roboto Medium", 14), progress_color=COLOR_SUCCESS,
            command=self.toggle_game_mode
        )
        self.game_switch.pack(pady=20)
        self.game_status = ctk.CTkLabel(tab, text="Mode: OFF", font=("Segoe UI", 12, "bold"), text_color="gray50")
        self.game_status.pack(pady=10)

    def _setup_monitor_tab(self):
        tab = self.tab_view.tab("Monitor")
        self.monitor_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent", label_text="")
        self.monitor_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # CPU
        self.card_cpu = DetailedMonitorCard(self.monitor_frame, "PROCESSOR (CPU)", "💻")
        self.card_cpu.pack(fill="x", pady=5)
        self.card_cpu.add_row("Model:", "Searching...", is_dynamic=True, value_id="cpu_name", copyable=True)
        self.card_cpu.add_row("Clock Speed:", "-- GHz", is_dynamic=True, value_id="cpu_speed")
        self.card_cpu.add_row("Load:", "--%", is_dynamic=True, value_id="cpu_load", distinct_style=True)
        
        # GPU
        self.card_gpu = DetailedMonitorCard(self.monitor_frame, "GRAPHICS (GPU)", "🎮")
        self.card_gpu.pack(fill="x", pady=5)
        self.card_gpu.add_row("Model:", "Searching...", is_dynamic=True, value_id="gpu_name", copyable=True)
        self.card_gpu.add_row("VRAM:", "-- / -- GB", is_dynamic=True, value_id="gpu_vram")
        self.card_gpu.add_row("Load:", "--%", is_dynamic=True, value_id="gpu_load", distinct_style=True)
        
        # Mobo
        self.card_mobo = DetailedMonitorCard(self.monitor_frame, "MOTHERBOARD", "🔌")
        self.card_mobo.pack(fill="x", pady=5)
        self.card_mobo.add_row("Model:", "Searching...", is_dynamic=True, value_id="mobo_model", copyable=True)
        self.card_mobo.add_row("Manufacturer:", "--", is_dynamic=True, value_id="mobo_man")
        
        # RAM
        self.card_ram = DetailedMonitorCard(self.monitor_frame, "MEMORY (RAM)", "🧠")
        self.card_ram.pack(fill="x", pady=5)
        self.card_ram.add_row("Total Size:", "-- GB", is_dynamic=True, value_id="ram_total")
        self.card_ram.add_row("Used:", "--%", is_dynamic=True, value_id="ram_load", distinct_style=True)
        
        # Disk
        self.card_disk = DetailedMonitorCard(self.monitor_frame, "STORAGE", "💾")
        self.card_disk.pack(fill="x", pady=5)
        self.card_disk.add_row("Physical Drive:", "Searching...", is_dynamic=True, value_id="disk_model", copyable=True)
        self.card_disk.add_row("Partitions:", "--", is_dynamic=True, value_id="disk_parts")

    def _populate_targets(self):
        for target in self.engine_targets:
            row = TargetRow(self.checklist_frame, target_path=target)
            row.pack(fill="x", pady=4, padx=5)
            self.target_rows[target] = row

    # --- Actions ---
    def start_cleaning_process(self):
        if self.engine.running: return
        self.btn_clean.configure(state="disabled", text="CLEANING...", fg_color="gray30")
        self.clean_status.configure(text="Cleaning in progress...", text_color="white")
        for row in self.target_rows.values(): row.set_status('waiting')
        
        self.engine.start_cleaning(
            update_callback=lambda: None, 
            complete_callback=self.on_clean_complete, 
            target_status_callback=self.on_target_update
        )

    def on_target_update(self, target, status, message):
         self.after(0, lambda: self._update_row(target, status, message))
    
    def _update_row(self, target, status, message):
        if target in self.target_rows:
            self.target_rows[target].set_status(status, message)

    def on_clean_complete(self, deleted, errors, bytes_freed):
        self.after(0, lambda: self._finish_clean(bytes_freed))

    def _finish_clean(self, bytes_freed):
        self.btn_clean.configure(state="normal", text="CLEAN SYSTEM", fg_color=COLOR_SUCCESS)
        
        # Simple bytes formatter logic inline
        power = 2**10
        n = 0
        power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
        size = bytes_freed
        while size > power:
            size /= power
            n += 1
        saved_str = f"{size:.2f} {power_labels[n]}B"
        
        self.clean_status.configure(text=f"Check finished! Freed {saved_str}", text_color=COLOR_SUCCESS)

    def toggle_game_mode(self):
        state = self.game_switch.get()
        self.game_mgr.toggle_mode(state == 1)
        if state == 1: self.game_status.configure(text="Mode: ON", text_color=COLOR_SUCCESS)
        else: self.game_status.configure(text="Mode: OFF", text_color="gray50")

    def boost_system(self):
        # Quick boost simulation/action
        self.btn_boost.configure(state="disabled", text="BOOSTING...")
        self.perf_log.configure(state="normal")
        self.perf_log.insert("end", "> Optimizing RAM and Network...\n")
        self.perf_log.configure(state="disabled")
        self.after(1000, lambda: self.btn_boost.configure(state="normal", text="BOOST NOW"))

    def update_monitor_ui(self, static_info, dynamic_stats):
        # Static Info (Run once ideally, but checking if empty is fine)
        if self.card_cpu.fields['cpu_name'].cget("text") == "Searching..." and 'cpu_name' in static_info:
            self.card_cpu.update_field("cpu_name", static_info.get('cpu_name', 'Unknown'))
            self.card_gpu.update_field("gpu_name", static_info.get('gpu_name', 'Unknown'))
            self.card_mobo.update_field("mobo_model", static_info.get('mobo_model', 'Unknown'))
            self.card_mobo.update_field("mobo_man", static_info.get('mobo_man', 'Unknown'))
            self.card_disk.update_field("disk_model", static_info.get('disk_model', 'Unknown'))
            self.card_ram.update_field("ram_total", static_info.get('ram_total', '-- GB'))

        # Dynamic Stats
        if 'cpu_pct' in dynamic_stats:
            self.card_cpu.update_field("cpu_load", f"Usage: {dynamic_stats['cpu_pct']}%", COLOR_USAGE_HIGHLIGHT)
            self.card_cpu.update_field("cpu_speed", f"{dynamic_stats.get('cpu_freq','--')} GHz")
            
            self.lbl_cpu_usage.configure(text=f"CPU: {dynamic_stats['cpu_pct']}%")
            self.lbl_ram_usage.configure(text=f"RAM: {dynamic_stats.get('ram_pct', 0)}%")
            
            # RAM
            if 'ram_pct' in dynamic_stats:
                self.card_ram.update_field("ram_load", f"{dynamic_stats['ram_pct']}% Used", COLOR_USAGE_HIGHLIGHT)

            # GPU
            g_load = dynamic_stats.get('gpu_load', 0)
            g_used = dynamic_stats.get('gpu_vram_used', 0)
            g_total = dynamic_stats.get('gpu_vram_total', 0)
            
            vram_str = f"{g_used/1024:.1f} / {g_total/1024:.1f} GB" if g_total > 0 else "N/A"
            self.card_gpu.update_field("gpu_load", f"Usage: {int(g_load)}%", COLOR_USAGE_HIGHLIGHT)
            self.card_gpu.update_field("gpu_vram", vram_str)
            
            # Disk Parts
            self.card_disk.update_field("disk_parts", dynamic_stats.get('disk_parts', '--'))
