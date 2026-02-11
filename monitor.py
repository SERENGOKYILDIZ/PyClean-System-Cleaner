import subprocess
import winreg
import platform
import threading
import time
import shutil
import sys
try:
    import psutil
except ImportError:
    pass

class HardwareMonitor:
    def __init__(self):
        self.gpu_data = {"load": 0.0, "vram_total": 0, "vram_used": 0}
        self.running = True
        
    def start_monitoring(self):
        threading.Thread(target=self._monitor_gpu_loop, daemon=True).start()

    def stop(self):
        self.running = False

    def run_ps_cmd(self, cmd):
        """Runs a PowerShell command and returns clean string"""
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            full_cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd]
            result = subprocess.run(full_cmd, capture_output=True, text=True, startupinfo=si)
            return result.stdout.strip()
        except Exception:
            return ""

    def get_static_info(self):
        info = {}
        
        # CPU Name
        cpu_name = ""
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            cpu_name = winreg.QueryValueEx(key, "ProcessorNameString")[0]
            winreg.CloseKey(key)
        except: pass
        if not cpu_name: cpu_name = platform.processor()
        info['cpu_name'] = cpu_name.strip()

        # GPU Name
        gpu_name = self.run_ps_cmd("""Get-PnpDevice -Class Display -Status OK | Select-Object -First 1 -ExpandProperty FriendlyName""")
        if not gpu_name: gpu_name = "Generic Graphics"
        info['gpu_name'] = gpu_name

        # Motherboard
        prod = self.run_ps_cmd("Get-WmiObject -Class Win32_BaseBoard | Select-Object -ExpandProperty Product")
        man = self.run_ps_cmd("Get-WmiObject -Class Win32_BaseBoard | Select-Object -ExpandProperty Manufacturer")
        info['mobo_model'] = prod
        info['mobo_man'] = man
        
        # Disk Model
        disk_model = self.run_ps_cmd("Get-PhysicalDisk | Select-Object -First 1 -ExpandProperty FriendlyName")
        if not disk_model: disk_model = "Standard Disk Drive"
        info['disk_model'] = disk_model
        
        # RAM Total
        try:
            mem = psutil.virtual_memory()
            info['ram_total'] = f"{mem.total / (1024**3):.1f} GB"
        except: 
            info['ram_total'] = "-- GB"
            
        return info

    def get_dynamic_stats(self):
        stats = {}
        try:
            # CPU
            stats['cpu_pct'] = psutil.cpu_percent(interval=None)
            freq = psutil.cpu_freq()
            stats['cpu_freq'] = f"{freq.current/1000:.2f}" if freq else "--"
            
            # RAM
            mem = psutil.virtual_memory()
            stats['ram_pct'] = mem.percent
            stats['ram_used_gb'] = mem.used / (1024**3)
            stats['ram_total_gb'] = mem.total / (1024**3)
            
            # Disk
            parts_str = ""
            for part in psutil.disk_partitions():
                if 'cdrom' in part.opts or part.fstype == '': continue
                try:
                    usage = shutil.disk_usage(part.mountpoint)
                    free_gb = usage.free / (1024**3)
                    parts_str += f"{part.device}  {free_gb:.1f} GB Free\n"
                except: pass
            stats['disk_parts'] = parts_str.strip()
            
            # GPU (Threaded data)
            stats['gpu_load'] = self.gpu_data['load']
            stats['gpu_vram_used'] = self.gpu_data['vram_used']
            stats['gpu_vram_total'] = self.gpu_data['vram_total']
            
        except: pass
        return stats

    def _monitor_gpu_loop(self):
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
                parts = [x.strip() for x in out.split(',')]
                if len(parts) >= 3:
                    load = float(parts[0])
                    total = float(parts[1])
                    used = float(parts[2])
            except:
                # Fallback WMIC
                try:
                    si2 = subprocess.STARTUPINFO()
                    si2.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    ram_out = subprocess.check_output(
                        "wmic path win32_VideoController get AdapterRAM", shell=True, startupinfo=si2
                    ).decode().strip()
                    lines = ram_out.split()
                    if len(lines) > 1 and lines[1].isdigit():
                        total = int(lines[1]) / (1024**2)
                except: pass
            
            self.gpu_data = {"load": load, "vram_total": total, "vram_used": used}
            time.sleep(1.5)
