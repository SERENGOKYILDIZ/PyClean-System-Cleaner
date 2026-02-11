if __name__ == "__main__":
    import ctypes
    import sys
    import os

    # TIP: Save this file as 'main.pyw' to run without a console window.
    # The following block prevents crashes when running without a console (e.g. via pythonw.exe).
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
        # Re-run the program with admin rights
        # Force pythonw.exe to prevent console window if we are running with python.exe
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
from cleaner import CleanManager
from config import APP_NAME, VERSION, WINDOW_SIZE, THEME_COLOR, APPEARANCE_MODE

# Configuration
ctk.set_appearance_mode("Dark") # Force Dark Mode for this design
ctk.set_default_color_theme(THEME_COLOR)

# Enhanced Colors
COLOR_BG = "#1a1a1a"         # Very dark background
COLOR_CARD = "#2b2b2b"       # Card background
COLOR_ACCENT = "#3B8ED0"     # Primary Blue
COLOR_SUCCESS = "#2CC985"    # Green
COLOR_TEXT_MAIN = "#FFFFFF"
COLOR_TEXT_SEC = "#A0A0A0"

class TargetRow(ctk.CTkFrame):
    def __init__(self, master, target_path, **kwargs):
        super().__init__(master, fg_color=COLOR_CARD, corner_radius=10, height=50, **kwargs)
        self.target_path = target_path
        
        # Grid layout for row items
        self.grid_columnconfigure(1, weight=1) # Path name expands
        
        # Icon/Indicator
        self.status_indicator = ctk.CTkLabel(self, text="●", font=("Arial", 20), text_color="gray40", width=40)
        self.status_indicator.grid(row=0, column=0, padx=(10, 5), pady=10)
        
        # Path Label
        display_name = target_path
        if "%TEMP%" in target_path: display_name = "System Temp Files"
        elif "Prefetch" in target_path: display_name = "Windows Prefetch Cache"
        elif "Recent" in target_path: display_name = "Recent Items History"
        elif "Downloads" in target_path: display_name = "Downloads Folder"
        elif "recycle" in target_path.lower(): display_name = "Recycle Bin"
        else:
             # Just show last folder name if it's long
             display_name = os.path.basename(target_path) if os.path.basename(target_path) else target_path

        self.name_label = ctk.CTkLabel(self, text=display_name, font=("Roboto Medium", 14), text_color=COLOR_TEXT_MAIN, anchor="w")
        self.name_label.grid(row=0, column=1, sticky="w", padx=5)
        
        # Status Label (Right side)
        self.status_text = ctk.CTkLabel(self, text="Waiting", font=("Segoe UI", 12), text_color=COLOR_TEXT_SEC, anchor="e", width=80)
        self.status_text.grid(row=0, column=2, padx=(5, 15))

    def set_status(self, status, message=None):
        if status == 'waiting':
            self.status_indicator.configure(text="●", text_color="gray40")
            self.status_text.configure(text="Waiting", text_color=COLOR_TEXT_SEC)
        elif status == 'running':
            self.status_indicator.configure(text="🔄", text_color=COLOR_ACCENT) 
            self.status_text.configure(text="Cleaning...", text_color=COLOR_ACCENT)
        elif status == 'done':
            self.status_indicator.configure(text="✔", text_color=COLOR_SUCCESS)
            self.status_text.configure(text="Cleaned", text_color=COLOR_SUCCESS)
        elif status == 'error':
            self.status_indicator.configure(text="✕", text_color="#d63031")
            self.status_text.configure(text="Error", text_color="#d63031")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry(WINDOW_SIZE)
        self.configure(fg_color=COLOR_BG) # Set main window background
        
        # Grid Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=1) # Checklist (Main Content)
        self.grid_rowconfigure(2, weight=0) # Controls
        self.grid_rowconfigure(3, weight=0) # Footer

        self.cleaner = CleanManager()
        self.is_cleaning = False
        self.target_rows = {} # Map path -> TargetRow widget
        
        self.targets = self.cleaner.load_targets()

        self._setup_ui()
        self._populate_targets()

    def _setup_ui(self):
        # --- Header Section ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, pady=(25, 15), padx=25, sticky="ew")
        
        title_label = ctk.CTkLabel(header_frame, text=APP_NAME, font=("Roboto Medium", 28), text_color=COLOR_TEXT_MAIN)
        title_label.pack(side="left")
        
        version_badge = ctk.CTkLabel(header_frame, text=VERSION, font=("Segoe UI", 12, "bold"), 
                                     fg_color=COLOR_CARD, text_color=COLOR_ACCENT, corner_radius=5, height=24, width=50)
        version_badge.pack(side="left", padx=10)

        # --- Checklist Section ---
        self.checklist_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", label_text="")
        self.checklist_frame.grid(row=1, column=0, padx=20, pady=5, sticky="nsew")

        # --- Controls Section ---
        controls_frame = ctk.CTkFrame(self, fg_color="#232323", corner_radius=0, height=100) # Sticky bottom bar look
        controls_frame.grid(row=2, column=0, sticky="ew")
        
        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(controls_frame, height=4, corner_radius=0, progress_color=COLOR_ACCENT)
        self.progress_bar.pack(fill="x", side="top")
        self.progress_bar.set(0)

        # Status text
        self.total_status = ctk.CTkLabel(controls_frame, text="Ready to optimize system", font=("Segoe UI", 13), text_color="gray70")
        self.total_status.pack(pady=(15, 5))

        # Main Button
        self.btn_action = ctk.CTkButton(
            controls_frame, 
            text="CLEAN SYSTEM", 
            width=280, 
            height=50, 
            corner_radius=8,
            font=("Roboto Medium", 15), 
            fg_color=COLOR_ACCENT,
            hover_color="#327ab3",
            command=self.start_cleaning
        )
        self.btn_action.pack(pady=(5, 20))
        
    def _populate_targets(self):
        for target in self.targets:
            row = TargetRow(self.checklist_frame, target_path=target)
            row.pack(fill="x", pady=4, padx=5)
            self.target_rows[target] = row

    def start_cleaning(self):
        if self.is_cleaning:
            return

        self.is_cleaning = True
        self.btn_action.configure(state="disabled", text="OPTIMIZING...", fg_color="gray30")
        self.total_status.configure(text="Scanning files...", text_color="white")
        self.progress_bar.set(0)
        
        # Reset UI
        for row in self.target_rows.values():
            row.set_status('waiting')
            
        # Start cleaning via manager
        self.cleaner.start_cleaning(
            update_callback=self.update_ui, 
            complete_callback=self.cleaning_complete,
            target_status_callback=self.update_target_status
        )

    def update_target_status(self, target, status, message):
        self.after(0, lambda: self._update_target_status_main_thread(target, status, message))

    def _update_target_status_main_thread(self, target, status, message):
        if target in self.target_rows:
            self.target_rows[target].set_status(status, message)

    def update_ui(self, message, progress):
        self.after(0, lambda: self._update_ui_main_thread(message, progress))

    def _update_ui_main_thread(self, message, progress):
        self.progress_bar.set(progress)
        # We don't flood the UI status text with file paths anymore, kept it cleaner
        # Just ensure users know it's working
        if progress < 1.0:
             self.total_status.configure(text=f"Processing... {int(progress*100)}%")

    def cleaning_complete(self, deleted, errors, bytes_freed):
        self.after(0, lambda: self._cleaning_complete_main_thread(deleted, errors, bytes_freed))

    def _cleaning_complete_main_thread(self, deleted, errors, bytes_freed):
        self.is_cleaning = False
        self.progress_bar.set(1.0)
        self.btn_action.configure(state="normal", text="CLEAN SYSTEM", fg_color=COLOR_SUCCESS)
        
        mb_freed = bytes_freed / (1024 * 1024)
        summary = f"Optimization Complete! Freed {mb_freed:.2f} MB"
        self.total_status.configure(text=summary, text_color=COLOR_SUCCESS)

if __name__ == "__main__":
    app = App()
    app.mainloop()
