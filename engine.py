import os
import shutil
import subprocess
import threading
import stat

class CleanManager:
    def __init__(self):
        self.running = False
        self.default_targets = [
            r"%TEMP%",
            r"C:\Windows\Prefetch",
            r"%USERPROFILE%\AppData\Local\Temp",
        ]
        self.config_file = "targets.txt"
        
    def load_targets(self):
        targets = []
        if not os.path.exists(self.config_file):
            with open(self.config_file, "w") as f:
                f.write("\n".join(self.default_targets))
        
        with open(self.config_file, "r") as f:
            for line in f:
                path = os.path.expandvars(line.strip())
                if path and os.path.exists(path):
                    targets.append(path)
        return targets

    def start_cleaning(self, update_callback, complete_callback, target_status_callback):
        self.running = True
        threading.Thread(target=self._clean_process, args=(update_callback, complete_callback, target_status_callback), daemon=True).start()

    def stop_cleaning(self):
        self.running = False

    def _clean_process(self, update_callback, complete_callback, target_status_callback):
        targets = self.load_targets()
        total_freed = 0
        deleted_count = 0
        errors = 0
        
        for target in targets:
            if not self.running: break
            
            target_status_callback(target, 'running', 'Scanning...')
            
            try:
                # Calculate size before deletion (approx)
                current_freed = 0
                if os.path.isdir(target):
                    for root, dirs, files in os.walk(target):
                        for name in files:
                            try:
                                fp = os.path.join(root, name)
                                current_freed += os.path.getsize(fp)
                            except: pass
                            
                    # Actual Deletion
                    shutil.rmtree(target, onerror=self._remove_readonly)
                    # Re-create the folder if it's a system folder we just emptied
                    try:
                        os.makedirs(target, exist_ok=True)
                    except: pass
                    
                    target_status_callback(target, 'done', 'Cleaned')
                elif os.path.isfile(target):
                    current_freed = os.path.getsize(target)
                    os.remove(target)
                    target_status_callback(target, 'done', 'Deleted')
                
                total_freed += current_freed
                deleted_count += 1
                
            except Exception as e:
                errors += 1
                target_status_callback(target, 'error', 'Error')
                
        complete_callback(deleted_count, errors, total_freed)
        self.running = False

    def _remove_readonly(self, func, path, excinfo):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass

class GameModeManager:
    def __init__(self):
        pass

    def toggle_mode(self, enable):
        services = ["SysMain", "Spooler", "DiagTrack", "WSearch"]
        action = "stop" if enable else "start"
        
        def _run():
            for service in services:
                try:
                    cmd = ["net", action, service]
                    si = subprocess.STARTUPINFO()
                    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    subprocess.run(cmd, capture_output=True, startupinfo=si)
                except: pass
        
        threading.Thread(target=_run, daemon=True).start()
