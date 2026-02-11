import ctypes
import sys
import os
import logging
import traceback
from datetime import datetime
import customtkinter as ctk
import threading
import time
from config import *
from engine import CleanManager, GameModeManager
from monitor import HardwareMonitor
from ui import AppUI

# --- SYSTEM LOGGING SETUP ---
# Ensure log file is in the same directory as the executable/script
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_log.txt')

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M',
    filemode='a'  # Append mode
)

# Redirect stdout and stderr to the logging system
class StreamToLogger:
    def __init__(self, level):
        self.level = level
    
    def write(self, message):
        if message.strip():  # Avoid logging empty lines
            logging.log(self.level, message.strip())
    
    def flush(self):
        pass

sys.stdout = StreamToLogger(logging.INFO)
sys.stderr = StreamToLogger(logging.ERROR)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        logging.error("Failed to check admin status:\n" + traceback.format_exc())
        return False

def main():
    try:
        logging.info("Application starting...")
        
        if not is_admin():
            logging.info("Requesting Admin privileges...")
            # Yönetici olarak yeniden başlat
            script = os.path.abspath(sys.argv[0])
            params = ' '.join([f'"{arg}"' for arg in sys.argv])
            # 'runas' parametresi UAC penceresini tetikler
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}"', None, 1)
            sys.exit()

        # Admin ise buradan devam eder
        logging.info("Running with Admin privileges.")
        ctk.set_appearance_mode(APPEARANCE_MODE)
        ctk.set_default_color_theme(THEME_COLOR)

        clean_mgr = CleanManager()
        game_mgr = GameModeManager()
        monitor = HardwareMonitor()
        
        app = AppUI(clean_mgr, monitor, game_mgr)
        
        # UI tamamen açıldıktan sonra izlemeyi başlat
        app.after(500, monitor.start_monitoring)
        
        def ui_update_loop():
            # UI'ın oturması için bekle
            time.sleep(1.5)
            while True:
                try:
                    if not app.winfo_exists(): break
                    static_info = monitor.get_static_info()
                    dynamic_stats = monitor.get_dynamic_stats()
                    # UI thread'ine güvenli veri gönderimi
                    app.after(0, lambda s=static_info, d=dynamic_stats: app.update_monitor_ui(s, d))
                    time.sleep(2) 
                except Exception:
                    logging.error("Error in UI update loop:\n" + traceback.format_exc())
                    break
                
        threading.Thread(target=ui_update_loop, daemon=True).start()
        app.mainloop()
        logging.info("Application closed normally.")

    except Exception:
        logging.critical("CRITICAL ERROR: Main application crashed:\n" + traceback.format_exc())
        # Optional: showing a message box for the user if the UI hasn't started yet or crashed
        try:
            ctypes.windll.user32.MessageBoxW(0, "Application crashed. Check app_log.txt for details.", "Critical Error", 0x10)
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()