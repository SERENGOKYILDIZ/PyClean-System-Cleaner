import os
import shutil
import subprocess
import re
import sys

# --- CONFIGURATION ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config.py")
MAIN_SCRIPT = os.path.join(PROJECT_ROOT, "main.py")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
ICON_FILE = os.path.join(ASSETS_DIR, "icon.ico")
RELEASE_DIR = os.path.join(PROJECT_ROOT, "release")

def get_version():
    """Extracts VERSION from config.py using regex."""
    try:
        with open(CONFIG_FILE, "r") as f:
            content = f.read()
            match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"[ERROR] Could not read config.py: {e}")
    return None

def main():
    print(f"[INFO] Starting Standalone Build Process...")
    
    version = get_version()
    if not version:
        print("[ERROR] Version not found in config.py!")
        return
    
    print(f"[INFO] Detected Version: {version}")
    
    # Setup Directories
    output_dir = os.path.join(RELEASE_DIR, f"v{version}")
    build_work_path = os.path.join(RELEASE_DIR, "build_temp")
    spec_path = os.path.join(RELEASE_DIR, "spec")
    
    if os.path.exists(output_dir):
        print(f"[INFO] Cleaning existing release directory...")
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    exe_name = f"PyClean_v{version}"
    
    # --- PYINSTALLER COMMAND ---
    # We use --onefile and --add-data to embed everything inside the EXE
    cmd = [
        "pyinstaller",
        "--noconsole",
        "--onefile", 
        f"--name={exe_name}",
        f"--distpath={output_dir}",
        f"--workpath={build_work_path}",
        f"--specpath={spec_path}",
        # Embedding the assets folder inside the EXE
        f"--add-data={ASSETS_DIR if os.path.exists(ASSETS_DIR) else '.'};assets",
        "--collect-all=customtkinter",
        "--hidden-import=psutil",
        "--hidden-import=PIL",
        MAIN_SCRIPT
    ]
    
    if os.path.exists(ICON_FILE):
        cmd.append(f"--icon={ICON_FILE}")
        print(f"[INFO] Embedding icon into EXE: {ICON_FILE}")

    print("[INFO] Running PyInstaller... Please wait.")
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        print("[ERROR] PyInstaller failed!")
        return

    # --- POST-BUILD CLEANUP ---
    # No need to copy targets.txt or assets anymore as they are bundled or handled by AppData
    
    print("\n" + "="*60)
    print(f"[SUCCESS] Standalone Build Complete!")
    print(f"Location: {os.path.join(output_dir, exe_name + '.exe')}")
    print("[INFO] No external files required. The EXE is fully portable.")
    print("="*60)

    # Clean up temporary build files
    try:
        shutil.rmtree(build_work_path)
        print("[INFO] Temporary build files cleaned.")
    except Exception as e:
        print(f"[WARN] Could not clean temp files: {e}")

if __name__ == "__main__":
    main()