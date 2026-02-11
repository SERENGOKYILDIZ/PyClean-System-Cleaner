# PyClean - System Cleaner

**PyClean** is a modern, high-performance system cleaning utility for Windows. Built with Python and CustomTkinter, it features a premium dark UI, configurable cleaning targets, and robust file operations to reclaim disk space safely and effectively.

## ✨ Key Features

- **Premium Dark UI**:
  - Sleek, modern interface with a deep dark theme (`#1a1a1a`).
  - Card-style layout for cleaning targets.
  - Real-time animated progress bar and status indicators.
- **Configurable Targets**:
  - Fully customizable via `targets.txt`.
  - Supports environment variables (e.g., `%TEMP%`, `%USERPROFILE%`).
  - Automatically creates a default configuration if none exists.
- **Robust Cleaning Engine**:
  - **Smart Deletion**: Handles read-only files and permission errors automatically.
  - **Safe Skipping**: Gracefully skips locked or in-use system files without crashing.
  - **Deep Clean**: Targets Temp, Prefetch, Recent Items, Recycle Bin, and more.
- **Auto-Elevation**: Automatically restarts with Administrator privileges to ensure full access to restricted system folders (like `Prefetch`).
- **No Console Mode**: Supports silent background execution (rename to `.pyw`).
- **Detailed Reporting**: Displays total disk space recovered in MB upon completion.

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
   > **Pro Tip:** Rename `main.py` to `main.pyw` to hide the command console window completely!

## ⚙️ Configuration

### Customizing Targets (`targets.txt`)
The application reads cleaning paths from `targets.txt` in the same directory. You can add or remove paths as needed.
**Example:**
```text
%TEMP%
C:\Windows\Prefetch
%USERPROFILE%\AppData\Local\Google\Chrome\User Data\Default\Cache
```

### App Settings (`config.py`)
Modify `config.py` to change the application name, version, window size, or theme colors.

## ⚠️ Disclaimer

This software deletes files from your system. While it is designed to target temporary and cache directories, the developer is not responsible for any unintended data loss. **Always review your `targets.txt` before running.**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## 👨‍💻 Author

**Semi Eren Gökyıldız**
- Email: [gokyildizsemieren@gmail.com](mailto:gokyildizsemieren@gmail.com)
- Website: [https://semierengokyildiz.vercel.app/](https://semierengokyildiz.vercel.app/)
- GitHub: [SERENGOKYILDIZ](https://github.com/SERENGOKYILDIZ)
- LinkedIn: [semi-eren-gokyildiz](https://www.linkedin.com/in/semi-eren-gokyildiz/)
