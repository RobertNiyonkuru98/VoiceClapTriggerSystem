# Assistant - Voice & Clap Controlled

This project is a voice-activated assistant that triggers system actions based on a wake word, number of claps, and optional voice modifiers.

## How to Run

### 1. Activate the Virtual Environment
Open your terminal in the project root and run:

**For PowerShell:**
```powershell
.venv\Scripts\Activate.ps1
```

**For Command Prompt (CMD):**
```cmd
.venv\Scripts\activate.bat
```

**For Command Prompt (Bash):**
```bash
source .venv/Scripts/activate
```

**For Command Prompt (Git Bash):**
```bash
source .venv/Scripts/activate
```

### 2. Run the Main Script
Once the environment is active, navigate to the script directory or run it from the root:
```bash
python main.py
```

---

## How it Works

1.  **Wake Word**: The system waits for you to say the wake word: **"jesus"**. (Configurable in `config.py`).
2.  **Clap Detection**: After the wake word, you have **4 seconds** to clap. The number of claps determines the action category.
3.  **Modifier Word**: After clapping, the system waits **2 seconds** for a "modifier" word to specify the action.

### Command Table

| Claps | Modifier | Action |
| :--- | :--- | :--- |
| **1** | *(None)* | Launch Study Mode (Brave with Canvas/Calendar) |
| **1** | "social" | Open Instagram PWA |
| **1** | "music" | Open Spotify |
| **1** | "movie" | Open MovieBox PWA |
| **2** | "peace" | Open ChatGPT |
| **2** | "study" | Launch Study Mode |
| **2** | *(None)* | Snap VS Code & Notepad to sides |
| **3** | *(Any)* | **System Shutdown Mode**: Close Brave/Code and Open Steam |

---

## Configuration
You can customize the behavior in `config.py`:
- `WAKE_WORD`: Change "jesus" to your preferred trigger.
- `THRESHOLD`: Increase if claps aren't being detected; decrease if background noise triggers it.
- `BRAVE_PATH`: Ensure this matches your Brave installation path.
- `STUDY_URLS`: Add/remove URLs for your study sessions.
