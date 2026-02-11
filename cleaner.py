import os
import shutil
import winshell
import threading
import sys
import stat

class CleanManager:
    def __init__(self):
        self.stop_event = threading.Event()

    def _remove_readonly(self, func, path, excinfo):
        """Helper to remove read-only files if rmtree fails."""
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass

    CONFIG_FILE = "targets.txt"

    def load_targets(self):
        """
        Loads targets from local config file. 
        Creates default file if not exists.
        Returns list of existing absolute paths.
        """
        defaults = [
            "%TEMP%",
            os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Prefetch'),
            os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp'),
            os.path.expanduser('~\\AppData\\Roaming\\Microsoft\\Windows\\Recent'),
        ]

        if not os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "w") as f:
                    for path in defaults:
                        f.write(path + "\n")
            except Exception as e:
                print(f"Error creating config: {e}")
                # Fallback to defaults if file creation fails
                return [os.path.expandvars(p) for p in defaults if os.path.exists(os.path.expandvars(p))]

        valid_targets = []
        try:
            with open(self.CONFIG_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    
                    # Expand vars like %TEMP%
                    expanded = os.path.expandvars(line)
                    if os.path.exists(expanded):
                        valid_targets.append(expanded)
        except Exception as e:
            print(f"Error reading config: {e}")
            
        return valid_targets

    def count_files(self, targets):
        """Counts total files to be cleaned for progress bar calculation."""
        total_files = 0
        for target in targets:
            try:
                for entry in os.scandir(target):
                    total_files += 1
            except PermissionError:
                pass
            except Exception:
                pass
        return total_files

    def get_size(self, path):
        try:
            return os.path.getsize(path)
        except:
            return 0

    def clean(self, update_callback=None, complete_callback=None, target_status_callback=None):
        """
        Main cleaning function.
        :param update_callback: function(message, progress_percent)
        :param complete_callback: function(deleted_count, error_count, freed_bytes)
        :param target_status_callback: function(target_path, status, message) -> status: 'running', 'done', 'error'
        """
        targets = self.load_targets()
        
        # We need to count files again if we want accurate progress bar for the "total" progress
        # OR we can just do indeterminate or per-target progress. 
        # User asked for per-target checklist.
        # But let's keep total progress for any other UI elements might want it.
        total_files = self.count_files(targets)
        deleted_count = 0
        error_count = 0
        processed_count = 0
        total_bytes_freed = 0

        # Empty Recycle Bin first
        try:
            if update_callback:
                update_callback("Emptying Recycle Bin...", 0)
            
            winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
            if update_callback:
                update_callback("Recycle Bin Emptied.", 0)
        except Exception as e:
             pass

        if not targets:
             if complete_callback: complete_callback(0,0,0)
             return

        for target in targets:
            if self.stop_event.is_set():
                break
            
            target_name = os.path.basename(target)
            target_deleted = 0
            target_bytes = 0
            
            # Notify UI: Target Started
            if target_status_callback:
                target_status_callback(target, 'running', "Scanning...")
            
            if update_callback:
                update_callback(f"Scanning {target_name}...", 0 if total_files == 0 else processed_count / total_files)

            try:
                # Scan first to see if empty? No, just iterate.
                files_found_in_target = 0
                for entry in os.scandir(target):
                    files_found_in_target += 1
                    if self.stop_event.is_set():
                        break
                    
                    processed_count += 1
                    progress = 0 if total_files == 0 else (processed_count / total_files)
                    
                    try:
                        file_size = self.get_size(entry.path)
                        
                        if update_callback:
                             # Shorten path for log
                            short_name = (entry.name[:30] + '..') if len(entry.name) > 30 else entry.name
                            update_callback(f"Deleting: {short_name}", progress)

                        if entry.is_dir():
                            shutil.rmtree(entry.path, onerror=self._remove_readonly)
                        else:
                            try:
                                os.remove(entry.path)
                            except PermissionError:
                                # Force delete read-only files
                                os.chmod(entry.path, stat.S_IWRITE)
                                os.remove(entry.path)
                        
                        deleted_count += 1
                        target_deleted += 1
                        total_bytes_freed += file_size
                        target_bytes += file_size
                        
                    except PermissionError:
                        error_count += 1
                    except Exception as e:
                        error_count += 1
                
                # Notify UI: Target Done
                if target_status_callback:
                    mb = target_bytes / (1024*1024)
                    target_status_callback(target, 'done', f"Done ({mb:.2f} MB)")
                
                if update_callback:
                     mb_freed = target_bytes / (1024 * 1024)
                     update_callback(f"Cleaned {target_name}: {target_deleted} files, {mb_freed:.2f} MB recovered.", progress)
                        
            except PermissionError:
                if target_status_callback:
                    target_status_callback(target, 'error', "Access Denied")
            except Exception as e:
                if target_status_callback:
                    target_status_callback(target, 'error', str(e))

        if complete_callback:
            complete_callback(deleted_count, error_count, total_bytes_freed)

    def start_cleaning(self, update_callback, complete_callback, target_status_callback):
        self.stop_event.clear()
        thread = threading.Thread(target=self.clean, args=(update_callback, complete_callback, target_status_callback), daemon=True)
        thread.start()

    def stop_cleaning(self):
        self.stop_event.set()
