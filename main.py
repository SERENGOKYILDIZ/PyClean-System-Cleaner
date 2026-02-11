if __name__ == "__main__":
    import ctypes
    import sys
    import os

    # TIP: Save this file as 'main.pyw' to run without a console window.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")

    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    if not is_admin():
        executable = sys.executable
        if executable.endswith("python.exe"):
            pythonw = executable.replace("python.exe", "pythonw.exe")
            if os.path.exists(pythonw):
                executable = pythonw

        script_path = os.path.abspath(sys.argv[0])
        params = f'"{script_path}"'
        if len(sys.argv) > 1:
            params += " " + " ".join([f'"{arg}"' for arg in sys.argv[1:]])
            
        ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, None, 1)
        sys.exit()

import customtkinter as ctk
import threading
import os
import shutil
import subprocess
import time
import winshell
import platform
import winreg
try:
    import psutil
except ImportError:
    pass
    
from cleaner import CleanManager
from config import APP_NAME, VERSION, THEME_COLOR, APPEARANCE_MODE

# Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme(THEME_COLOR)

# Dimensions
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 720 # Adjusted for header

# Colors
COLOR_BG_MAIN = "#1a1a1a"
COLOR_CARD = "#2b2b2b"
COLOR_ACCENT = "#3B8ED0"     
COLOR_NEON_BLUE = "#33C9FF"  
COLOR_USAGE_HIGHLIGHT = "#00E5FF" # distinct bright accent for usage
COLOR_SUCCESS = "#2CC985"
COLOR_WARNING = "#f1c40f"
COLOR_ERROR = "#e74c3c"
COLOR_TEXT_MAIN = "#FFFFFF"
COLOR_TEXT_SEC = "#A0A0A0"
COLOR_TEXT_LABEL = "#909090"

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
        
        # Header (Icon + Title)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 5))
        
        ctk.CTkLabel(header, text=icon_text, font=("Arial", 20)).pack(side="left", padx=(0, 10))
        self.title_label = ctk.CTkLabel(header, text=title, font=("Roboto Medium", 13, "bold"), text_color="gray90")
        self.title_label.pack(side="left")
        
        # Grid for stats
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=15, pady=(0, 15))
        self.stats_frame.grid_columnconfigure(1, weight=1)
        
        self.row_idx = 0
        self.fields = {} 

    def add_row(self, label_text, value_text, is_dynamic=False, value_id=None, distinct_style=False, copyable=False):
        # Optional distinct styling for bottom usage row
        lbl_clr = COLOR_NEON_BLUE if distinct_style else COLOR_TEXT_LABEL
        val_clr = COLOR_USAGE_HIGHLIGHT if distinct_style else COLOR_TEXT_MAIN
        font_style = ("Segoe UI", 12, "bold") if distinct_style else ("Segoe UI", 11)
        
        l = ctk.CTkLabel(self.stats_frame, text=label_text, font=font_style, text_color=lbl_clr, anchor="w")
        l.grid(row=self.row_idx, column=0, sticky="w", pady=1, padx=(0, 10))
        
        v = ctk.CTkLabel(self.stats_frame, text=value_text, font=("Segoe UI", 12), text_color=val_clr, anchor="w", wraplength=350)
        v.grid(row=self.row_idx, column=1, sticky="w", pady=1)
        
        if copyable:
            v.configure(cursor="hand2")
            # Bind click to copy
            v.bind("<Button-1>", lambda e, label=v: self.copy_to_clipboard(label))
             # Add a tooltip-like hint (optional, but good for UX)
            ctk.CTkLabel(self.stats_frame, text="(Copy)", font=("Arial", 9), text_color="gray40").grid(row=self.row_idx, column=2, sticky="e", padx=5)

        if is_dynamic and value_id:
            self.fields[value_id] = v
        
        self.row_idx += 1

    def copy_to_clipboard(self, label_widget):
        text = label_widget.cget("text")
        if not text or text == "Searching...": return
        
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update() # Required to finalize clipboard
        
        # Visual feedback
        original_color = label_widget.cget("text_color")
        label_widget.configure(text_color=COLOR_SUCCESS, text="Copied! ✓")
        
        def restore():
            label_widget.configure(text_color=original_color, text=text)
            
        self.after(1000, restore)

    def update_field(self, value_id, new_text, color=None):
        if value_id in self.fields:
            # If currently showing "Copied!", don't overwrite immediately if it's a dynamic update collision
            # But usually model names are static after fetch.
            # However, for safety, we just update. The restore() might overwrite this if timing is bad, 
            # but since model names are static, it shouldn't matter.
            # If it's a dynamic field we are copying (like usage), it might flicker.
            # But user asked for Model Names specifically.
            if self.fields[value_id].cget("text") == "Copied! ✓":
                # We skip update if it is currently showing the copied message to avoid confusion
                return 

            if color:
                self.fields[value_id].configure(text=new_text, text_color=color)
            else:
                self.fields[value_id].configure(text=new_text)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("System Optimizer")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.configure(fg_color=COLOR_BG_MAIN)
        self.resizable(False, False)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Row 1 has tabs
        
        self.cleaner = CleanManager()
        self.is_cleaning = False
        self.target_rows = {} 
        self.targets = self.cleaner.load_targets()

        self._build_header()
        self._build_tabs()
        
        self.running = True
        
        # Threads
        threading.Thread(target=self._fetch_rich_hardware_info, daemon=True).start()
        threading.Thread(target=self._monitor_loop, daemon=True).start()
        
        # GPU Extended Thread
        self.gpu_data = {"load": 0.0, "vram_total": 0, "vram_used": 0}
        threading.Thread(target=self._monitor_gpu_usage, daemon=True).start()

        self.after(1000, self.update_dynamic_hardware_stats)

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
        
        self._populate_targets()
        
        self.btn_clean = ctk.CTkButton(
            tab, 
            text="CLEAN SYSTEM", 
            height=50, 
            corner_radius=8,
            font=("Roboto Medium", 15), 
            fg_color=COLOR_ACCENT,
            hover_color="#327ab3",
            command=self.start_cleaning
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
            tab, 
            text="BOOST NOW", 
            height=45, 
            corner_radius=8,
            font=("Roboto Medium", 14), 
            fg_color="#2b2b2b", 
            border_width=1, 
            border_color=COLOR_ACCENT,
            hover_color="#333333",
            command=self.boost_system
        )
        self.btn_boost.pack(side="bottom", fill="x", padx=15, pady=20)

    def _setup_gamemode_tab(self):
        tab = self.tab_view.tab("Game Mode")
        tab.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(tab, text="🎮", font=("Arial", 64)).pack(pady=(40, 10))
        ctk.CTkLabel(tab, text="GAME MODE", font=("Roboto Medium", 20, "bold")).pack(pady=5)
        
        desc = "Maximizes gaming performance by temporarily stopping\nnon-essential background services."
        ctk.CTkLabel(tab, text=desc, font=("Segoe UI", 12), text_color="gray70", justify="center").pack(pady=20)
        
        self.game_switch = ctk.CTkSwitch(
            tab, 
            text="ENABLE GAME MODE", 
            font=("Roboto Medium", 14), 
            progress_color=COLOR_SUCCESS,
            command=self.toggle_game_mode
        )
        self.game_switch.pack(pady=20)
        
        self.game_status = ctk.CTkLabel(tab, text="Mode: OFF", font=("Segoe UI", 12, "bold"), text_color="gray50")
        self.game_status.pack(pady=10)

    def _setup_monitor_tab(self):
        tab = self.tab_view.tab("Monitor")
        self.monitor_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent", label_text="")
        self.monitor_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 1. CPU
        self.card_cpu = DetailedMonitorCard(self.monitor_frame, "PROCESSOR (CPU)", "💻")
        self.card_cpu.pack(fill="x", pady=5)
        self.card_cpu.add_row("Model:", "Searching...", is_dynamic=True, value_id="cpu_name", copyable=True)
        self.card_cpu.add_row("Clock Speed:", "-- GHz", is_dynamic=True, value_id="cpu_speed")
        self.card_cpu.add_row("Load:", "--%", is_dynamic=True, value_id="cpu_load", distinct_style=True)
        
        # 2. GPU
        self.card_gpu = DetailedMonitorCard(self.monitor_frame, "GRAPHICS (GPU)", "🎮")
        self.card_gpu.pack(fill="x", pady=5)
        self.card_gpu.add_row("Model:", "Searching...", is_dynamic=True, value_id="gpu_name", copyable=True)
        self.card_gpu.add_row("VRAM:", "-- / -- GB", is_dynamic=True, value_id="gpu_vram")
        self.card_gpu.add_row("Load:", "--%", is_dynamic=True, value_id="gpu_load", distinct_style=True)
        
        # 3. Motherboard
        self.card_mobo = DetailedMonitorCard(self.monitor_frame, "MOTHERBOARD", "🔌")
        self.card_mobo.pack(fill="x", pady=5)
        self.card_mobo.add_row("Model:", "Searching...", is_dynamic=True, value_id="mobo_model", copyable=True)
        self.card_mobo.add_row("Manufacturer:", "--", is_dynamic=True, value_id="mobo_man")
        
        # 4. RAM
        self.card_ram = DetailedMonitorCard(self.monitor_frame, "MEMORY (RAM)", "🧠")
        self.card_ram.pack(fill="x", pady=5)
        self.card_ram.add_row("Total Size:", "-- GB", is_dynamic=True, value_id="ram_total")
        self.card_ram.add_row("Used:", "--%", is_dynamic=True, value_id="ram_load", distinct_style=True)
        
        # 5. Disk
        self.card_disk = DetailedMonitorCard(self.monitor_frame, "STORAGE", "💾")
        self.card_disk.pack(fill="x", pady=5)
        self.card_disk.add_row("Physical Drive:", "Searching...", is_dynamic=True, value_id="disk_model", copyable=True)
        self.card_disk.add_row("Partitions:", "--", is_dynamic=True, value_id="disk_parts")

    def _fetch_rich_hardware_info(self):
        """Fetches static hardware info ONCE"""
        
        def run_ps(cmd):
            try:
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                full = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd]
                return subprocess.run(full, capture_output=True, text=True, startupinfo=si).stdout.strip()
            except: return ""

        # --- CPU Name ---
        cpu_name = ""
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            cpu_name = winreg.QueryValueEx(key, "ProcessorNameString")[0]
            winreg.CloseKey(key)
        except: pass
        if not cpu_name: cpu_name = platform.processor()
        self.after(0, lambda: self.card_cpu.update_field("cpu_name", cpu_name.strip()))
        
        # --- GPU Name ---
        gpu_name = run_ps("""Get-PnpDevice -Class Display -Status OK | Select-Object -First 1 -ExpandProperty FriendlyName""")
        if not gpu_name: gpu_name = "Generic Graphics"
        self.after(0, lambda: self.card_gpu.update_field("gpu_name", gpu_name))

        # --- Motherboard ---
        prod = run_ps("Get-WmiObject -Class Win32_BaseBoard | Select-Object -ExpandProperty Product")
        man = run_ps("Get-WmiObject -Class Win32_BaseBoard | Select-Object -ExpandProperty Manufacturer")
        self.after(0, lambda: self.card_mobo.update_field("mobo_model", prod))
        self.after(0, lambda: self.card_mobo.update_field("mobo_man", man))
        
        # --- Physical Disk Model ---
        disk_model = run_ps("Get-PhysicalDisk | Select-Object -First 1 -ExpandProperty FriendlyName")
        if not disk_model: disk_model = "Standard Disk Drive"
        self.after(0, lambda: self.card_disk.update_field("disk_model", disk_model))
        
        # --- RAM Check (Total) ---
        try:
            mem = psutil.virtual_memory()
            total_gb = mem.total / (1024**3)
            self.after(0, lambda: self.card_ram.update_field("ram_total", f"{total_gb:.1f} GB"))
        except: pass

    def _monitor_gpu_usage(self):
        """Thread for GPU VRAM and Load"""
        while self.running:
            load = 0.0
            total = 0
            used = 0
            
            # NVIDIA SMI
            try:
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                out = subprocess.check_output(
                    ['nvidia-smi', '--query-gpu=utilization.gpu,memory.total,memory.used', '--format=csv,noheader,nounits'],
                    startupinfo=si
                ).decode().strip()
                # Format: "45, 8192, 400"
                parts = [x.strip() for x in out.split(',')]
                if len(parts) >= 3:
                    load = float(parts[0])
                    total = float(parts[1])
                    used = float(parts[2])
            except:
                # FALLBACK: WMIC if nvidia-smi failed
                try:
                    # Get detected VRAM from WMI for first adapter
                    si2 = subprocess.STARTUPINFO()
                    si2.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    ram_out = subprocess.check_output(
                        "wmic path win32_VideoController get AdapterRAM", shell=True, startupinfo=si2
                    ).decode().strip()
                    # Output: AdapterRAM \n 4294967296
                    lines = ram_out.split()
                    if len(lines) > 1 and lines[1].isdigit():
                        bytes_ram = int(lines[1])
                        total = bytes_ram / (1024**2) # MB
                        # We cannot get live used memory easily via generic wmi, 
                        # so we leave used as 0 or estimated.
                except: pass
            
            self.gpu_data = {"load": load, "vram_total": total, "vram_used": used}
            time.sleep(1.5)

    def update_dynamic_hardware_stats(self):
        if self.tab_view.get() == "Monitor":
            try:
                # CPU
                cpu_pct = psutil.cpu_percent(interval=None)
                freq = psutil.cpu_freq()
                freq_str = f"{freq.current/1000:.2f}" if freq else "--"
                self.card_cpu.update_field("cpu_load", f"Usage: {cpu_pct}%", COLOR_USAGE_HIGHLIGHT)
                self.card_cpu.update_field("cpu_speed", f"{freq_str} GHz")
                
                # GPU
                g = self.gpu_data
                if g["vram_total"] > 0:
                    vram_str = f"{g['vram_used']/1024:.1f} / {g['vram_total']/1024:.1f} GB"
                    load_str = f"Usage: {int(g['load'])}%"
                else:
                    vram_str = "N/A"
                    load_str = "N/A"
                
                self.card_gpu.update_field("gpu_load", load_str, COLOR_USAGE_HIGHLIGHT)
                self.card_gpu.update_field("gpu_vram", vram_str)
                
                # RAM
                mem = psutil.virtual_memory()
                self.card_ram.update_field("ram_load", f"{mem.percent}% ({mem.used/(1024**3):.1f} GB)", COLOR_USAGE_HIGHLIGHT)
                
                # Disk Partitions
                parts_str = ""
                for part in psutil.disk_partitions():
                    if 'cdrom' in part.opts or part.fstype == '': continue
                    try:
                        usage = shutil.disk_usage(part.mountpoint)
                        free_gb = usage.free / (1024**3)
                        parts_str += f"{part.device}  {free_gb:.1f} GB Free\n"
                    except: pass
                self.card_disk.update_field("disk_parts", parts_str.strip())
                
            except: pass
            
        self.after(1000, self.update_dynamic_hardware_stats)

    def _populate_targets(self):
        for target in self.targets:
            row = TargetRow(self.checklist_frame, target_path=target)
            row.pack(fill="x", pady=4, padx=5)
            self.target_rows[target] = row

    def _monitor_loop(self):
        while self.running:
            try:
                if 'psutil' in sys.modules:
                    cpu = psutil.cpu_percent(interval=None)
                    ram = psutil.virtual_memory().percent
                    self.after(0, lambda c=cpu, r=ram: self._update_monitor_labels(c, r))
            except: pass
            time.sleep(2)

    def _update_monitor_labels(self, cpu, ram):
        self.lbl_ram_usage.configure(text=f"RAM: {ram}%")
        self.lbl_cpu_usage.configure(text=f"CPU: {cpu}%")
        if ram > 85: self.lbl_ram_usage.configure(text_color=COLOR_ERROR)
        else: self.lbl_ram_usage.configure(text_color=COLOR_ACCENT)

    def log_perf(self, msg):
        self.perf_log.configure(state="normal")
        self.perf_log.insert("end", f"> {msg}\n")
        self.perf_log.see("end")
        self.perf_log.configure(state="disabled")

    def toggle_game_mode(self):
        state = self.game_switch.get()
        if state == 1:
            self.game_status.configure(text="Mode: ON", text_color=COLOR_SUCCESS)
            threading.Thread(target=self._run_game_mode, args=(True,), daemon=True).start()
        else:
            self.game_status.configure(text="Mode: OFF", text_color="gray50")
            threading.Thread(target=self._run_game_mode, args=(False,), daemon=True).start()

    def _run_game_mode(self, enable):
        services = ["SysMain", "Spooler", "DiagTrack", "WSearch"]
        action = "stop" if enable else "start"
        for service in services:
            try:
                cmd = ["net", action, service]
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.run(cmd, capture_output=True, startupinfo=si)
            except: pass

    def boost_system(self):
        def _run_boost():
            self.btn_boost.configure(state="disabled", text="BOOSTING...")
            self.after(0, lambda: self.log_perf("Starting Boost..."))
            try:
                subprocess.run(["ipconfig", "/flushdns"], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.after(0, lambda: self.log_perf("DNS Flushed"))
            except: pass
            try:
                self.clipboard_clear()
                self.after(0, lambda: self.log_perf("Clipboard Cleared"))
            except: pass
            try:
                pid = ctypes.windll.kernel32.GetCurrentProcess()
                ctypes.windll.psapi.EmptyWorkingSet(pid)
                self.after(0, lambda: self.log_perf("RAM Optimized"))
            except: pass
            self.after(500, lambda: self._boost_complete())
        threading.Thread(target=_run_boost, daemon=True).start()

    def _boost_complete(self):
        self.btn_boost.configure(state="normal", text="BOOST NOW")
        self.log_perf("Boost Complete!")

    def start_cleaning(self):
        if self.is_cleaning: return
        self.is_cleaning = True
        self.btn_clean.configure(state="disabled", text="CLEANING...", fg_color="gray30")
        self.clean_status.configure(text="Cleaning in progress...", text_color="white")
        for row in self.target_rows.values():
            row.set_status('waiting')
        self.cleaner.start_cleaning(update_callback=self.update_ui, complete_callback=self.cleaning_complete, target_status_callback=self.update_target_status)

    def update_target_status(self, target, status, message):
        self.after(0, lambda: self._update_target_status_main_thread(target, status, message))

    def _update_target_status_main_thread(self, target, status, message):
        if target in self.target_rows:
            self.target_rows[target].set_status(status, message)

    def update_ui(self, message, progress):
        pass

    def cleaning_complete(self, deleted, errors, bytes_freed):
        self.after(0, lambda: self._cleaning_complete_main_thread(deleted, errors, bytes_freed))

    def _cleaning_complete_main_thread(self, deleted, errors, bytes_freed):
        self.is_cleaning = False
        self.btn_clean.configure(state="normal", text="CLEAN SYSTEM", fg_color=COLOR_SUCCESS)
        saved_str = format_bytes(bytes_freed)
        self.clean_status.configure(text=f"Check finished! Freed {saved_str}", text_color=COLOR_SUCCESS)

    def on_close(self):
        self.running = False
        self.cleaner.stop_cleaning()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
