# PyClean - System Cleaner & Optimizer

**PyClean** is a modern, high-performance system maintenance utility for Windows. Built with Python and CustomTkinter, it combines a powerful cleaner with a **pro-grade system monitor** and **game booster** in a sleek, compact interface.

## 📥 Downloads
> **[Download v1.1.6](https://github.com/SERENGOKYILDIZ/PyClean-System-Cleaner/releases/download/v1.1.6/PyClean_v1.1.6.exe)**
>
> **[Download v1.1.5](https://github.com/SERENGOKYILDIZ/PyClean-System-Cleaner/releases/download/v1.1.5/PyClean_v1.1.5.exe)**
> 
> *No installation required. Single portable executable.*

---

## ✨ Key Features

### 🧹 System Cleaner
- **Deep Cleaning**: Targets Temp, Prefetch, Recent Items, Recycle Bin, and custom paths.
- **Smart Deletion**: Handles read-only files and permission errors automatically.
- **Configurable Targets**: Fully customizable via `targets.txt` (supports environment variables).
- **Real-Time Status**: Animated progress indicators for each cleaning target.

### 📊 Professional Hardware Monitor
- **Detailed Specs**: Displays precise model names for CPU, GPU, Motherboard, and Disk (Physical Model).
- **Live Stats**: Read **VRAM Usage**, CPU Clock Speed, and GPU Load in real-time.
- **Click-to-Copy**: Click any hardware name to instantly copy it to your clipboard.
- **Intelligent Detection**: Uses PowerShell PnP and WMI for accuracy (no "N/A" errors).

### 🎮 Game Mode
- **Performance Boost**: Temporarily stops non-essential background services (SysMain, DiagTrack, etc.) to free up resources.
- **One-Click Toggle**: Switch between Gaming and Standard modes instantly.

### 🚀 Performance Hub
- **RAM & CPU Gauge**: Live percentage monitoring.
- **Quick Boost**: Instantly flush DNS, clear clipboard, and optimize RAM working sets with one click.

### 🎨 Premium UI
- **Compact Design**: Minimalist 500x720 window with a deep dark theme (`#1a1a1a`).
- **Neon Accents**: Bright blue highlights for critical live data.
- **Auto-Elevation**: Automatically restarts with Admin privileges for full system access.

## 🚀 Installation & Usage

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/SERENGOKYILDIZ/PyClean-System-Cleaner.git
   cd PyClean-System-Cleaner
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   ```bash
   python main.py
   ```
   > **Pro Tip:** Rename `main.py` to `main.pyw` to hide the console window!

## ⚙️ Configuration

### Customizing Targets (`targets.txt`)
Add or remove paths in `targets.txt`. Supports `%TEMP%`, `%USERPROFILE%`, etc.

### App Settings (`config.py`)
Modify `config.py` to change the application name, version (`v1.1`), window size, or theme colors.

## ⚠️ Disclaimer

This software performs file deletion and system service modifications. The developer is not responsible for any unintended data loss. **Always review your `targets.txt`.**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## 👨‍💻 Author

**Semi Eren Gökyıldız**
- Email: [gokyildizsemieren@gmail.com](mailto:gokyildizsemieren@gmail.com)
- Website: [https://semierengokyildiz.vercel.app/](https://semierengokyildiz.vercel.app/)
- GitHub: [SERENGOKYILDIZ](https://github.com/SERENGOKYILDIZ)
- LinkedIn: [semi-eren-gokyildiz](https://www.linkedin.com/in/semi-eren-gokyildiz/)
