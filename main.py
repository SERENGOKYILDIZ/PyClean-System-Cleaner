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
import time
from config import *
from engine import CleanManager, GameModeManager
from monitor import HardwareMonitor
from ui import AppUI

# Configuration
ctk.set_appearance_mode(APPEARANCE_MODE)
ctk.set_default_color_theme(THEME_COLOR)

def main():
    # Initialize Modules
    clean_mgr = CleanManager()
    game_mgr = GameModeManager()
    monitor = HardwareMonitor()
    
    # Initialize UI
    app = AppUI(clean_mgr, monitor, game_mgr)
    
    # Start Monitoring
    monitor.start_monitoring()
    
    # Background Thread to push data to UI
    def ui_update_loop():
        # Fetch static info once after a short delay
        time.sleep(1)
        static_info = monitor.get_static_info()
        
        while app.winfo_exists():
            dynamic_stats = monitor.get_dynamic_stats()
            # Push updates to UI thread
            app.after(0, lambda: app.update_monitor_ui(static_info, dynamic_stats))
            time.sleep(1)
            
    threading.Thread(target=ui_update_loop, daemon=True).start()
    
    # Run Loop
    app.mainloop()
    
    # Cleanup
    clean_mgr.stop_cleaning()
    monitor.stop()

if __name__ == "__main__":
    main()
