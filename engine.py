import os
import shutil
import subprocess
import threading
import stat

import json

class CleanManager:
    def __init__(self):
        self.running = False
        self.default_targets = [
            r"%TEMP%",
            r"C:\Windows\Prefetch",
            r"C:\Windows\Temp",
            r"C:\Windows\SoftwareDistribution\Download",
            r"C:\Windows\System32\spool\PRINTERS",
            r"%USERPROFILE%\AppData\Local\Microsoft\Windows\INetCache",
            r"%USERPROFILE%\AppData\Local\Microsoft\Windows\INetCookies",
            r"%APPDATA%\Microsoft\Windows\Recent",
            r"C:\Windows\Minidump",
            r"C:\Windows\Logs\CBS",
            r"C:\Windows\Logs\DISM",
            r"C:\Windows\Logs\WindowsUpdate",
            r"%ProgramData%\Microsoft\Windows\WER\ReportArchive",
            r"%ProgramData%\Microsoft\Windows\WER\ReportQueue",
            r"%USERPROFILE%\AppData\Local\Microsoft\Windows\WER\ReportArchive",
            r"%USERPROFILE%\AppData\Local\Microsoft\Windows\WER\ReportQueue",
            r"%USERPROFILE%\AppData\Local\D3DSCache",
            r"%USERPROFILE%\AppData\Local\Google\Chrome\User Data\Default\Cache",
            r"%USERPROFILE%\AppData\Local\Microsoft\Edge\User Data\Default\Cache",
        ]
        
        # Setup AppData persistence
        appdata = os.getenv('LOCALAPPDATA')
        self.config_dir = os.path.join(appdata, "PyClean")
        self.config_file = os.path.join(self.config_dir, "settings.json")
        
        self.raw_targets = []   # Stores %VAR% paths for UI
        self.target_dirs = []   # Stores C:\Expanded paths for Cleaning
        
        self.load_settings()

    def load_settings(self):
        # 1. Create dir if missing
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)
            
        # 2. Check file
        if not os.path.exists(self.config_file):
            # Load defaults and save them
            self.raw_targets = list(self.default_targets)
            self.save_settings()
        else:
            # Read file
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    self.raw_targets = data.get("targets", self.default_targets)
            except:
                self.raw_targets = list(self.default_targets)
        
        # Update expanded paths for engine use
        self._refresh_expanded_paths()
        return self.target_dirs

    def save_settings(self):
        try:
            data = {"targets": self.raw_targets}
            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=4)
        except: pass

    def _refresh_expanded_paths(self):
        """Expands raw targets into valid system paths for cleaning."""
        self.target_dirs.clear()
        seen = set()
        
        for t in self.raw_targets:
            t = t.strip()
            if not t: continue
            
            expanded = os.path.expandvars(t)
            # Only add if it exists and hasn't been added
            if os.path.exists(expanded) and expanded not in seen:
                self.target_dirs.append(expanded)
                seen.add(expanded)

    def update_paths(self, new_raw_list):
        """
        Receives raw list from UI (with %VARS%), updates settings, and expands.
        """
        if new_raw_list is None: new_raw_list = []
        
        # Deduplicate raw list while preserving order
        clean_raw = []
        seen_raw = set()
        for t in new_raw_list:
            t = t.strip()
            if t and t not in seen_raw:
                clean_raw.append(t)
                seen_raw.add(t)
        
        self.raw_targets = clean_raw
        self.save_settings()
        self._refresh_expanded_paths()
        
        return self.target_dirs

    def start_cleaning(self, update_callback, complete_callback, target_status_callback, custom_targets=None):
        self.running = True
        threading.Thread(target=self._clean_process, args=(update_callback, complete_callback, target_status_callback, custom_targets), daemon=True).start()

    def stop_cleaning(self):
        self.running = False

    def _clean_process(self, update_callback, complete_callback, target_status_callback, custom_targets=None):
        targets = self.target_dirs if custom_targets is None else [os.path.expandvars(t) for t in custom_targets if t.strip()]
             
        total_freed = 0
        deleted_count = 0
        errors = 0
        
        for target in targets:
            if not self.running: break
            
            target_status_callback(target, 'running', 'Scanning...')
            
            try:
                current_freed = 0
                if os.path.isdir(target):
                    for root, dirs, files in os.walk(target):
                        for name in files:
                            try:
                                fp = os.path.join(root, name)
                                current_freed += os.path.getsize(fp)
                            except: pass
                            
                    shutil.rmtree(target, onerror=self._remove_readonly)
                    os.makedirs(target, exist_ok=True)
                    target_status_callback(target, 'done', 'Cleaned')
                elif os.path.isfile(target):
                    current_freed = os.path.getsize(target)
                    os.remove(target)
                    target_status_callback(target, 'done', 'Deleted')
                
                total_freed += current_freed
                deleted_count += 1
                
            except Exception:
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