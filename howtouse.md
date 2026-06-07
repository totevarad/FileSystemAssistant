# How to Use — LLM-Powered File System Assistant

Welcome! This guide will walk you through launching and interacting with the assistant for the first time.

---

## 📋 Prerequisites

Before running the application, make sure you have:
1. **Python 3.10 or higher** installed on your system.
2. A **Groq API Key** (you can generate one for free at [console.groq.com/keys](https://console.groq.com/keys)).

---

## 🚀 Easy Launch (Recommended)

We provide double-clickable launcher scripts that automatically handle Python virtual environment creation, package installations, and configuration verification.

### Windows (cmd / PowerShell)
1. **Double-click** the [run.bat](file:///c:/Users/varad/Desktop/Gen%20AI/FileSystemAssistant/run.bat) file at the project root.
2. On first run, it will automatically create `venv/`, install dependencies (including the `rich` Terminal UI package), copy `.env.example` to `.env`, and prompt you to add your key.
3. Open [.env](file:///c:/Users/varad/Desktop/Gen%20AI/FileSystemAssistant/.env) in any text editor, replace `your_groq_api_key_here` with your real Groq API Key, and save.
4. **Double-click** `run.bat` again to open the styled interactive Terminal dashboard!

### macOS / Linux
1. Open a terminal in the project directory.
2. Make the script executable and run it:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```
3. Configure your `GROQ_API_KEY` inside the generated `.env` file and re-run `./run.sh` to start the styled Terminal dashboard.

---

## 🛠️ Manual Execution (Alternative)

If you prefer to configure the workspace manually, execute these commands in your shell:

```bash
# 1. Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env     # Windows
cp .env.example .env       # macOS/Linux
# (Edit .env to set GROQ_API_KEY)

# 4. Start the program
python llm_file_assistant.py
```

---

## 💬 Sample Queries to Try

Once the CLI displays the `You:` prompt, try these interactions:

1. **Discovery:**
   `List all files in the resumes folder`
2. **Analysis:**
   `Find resumes mentioning Python experience`
3. **Write Summary:**
   `Create a summary file for john_doe.pdf`
4. **Rejection Guard (Safety Check):**
   `what is the capital of India` (The assistant will refuse to answer out-of-scope queries).
5. **Exit:**
   Type `exit` or `quit` to end the session.

---

## 📦 Deliverable Rationale: Scripts (.bat / .sh) vs. Binaries (.exe)

For this project scope, **launcher scripts (`run.bat` and `run.sh`)** are the best-suited delivery mechanism instead of compiled `.exe` files for the following reasons:

| Feature | Launcher Scripts (Selected) | Compiled Binaries (.exe) |
| :--- | :--- | :--- |
| **Cross-Platform** | Yes (Dedicated scripts for Windows & Unix). | No (Windows only; requires separate macOS/Linux builds). |
| **Security Flags** | Clean. Windows Defender will run scripts without warnings. | High alert. Custom `.exe` files often trigger Windows SmartScreen warnings. |
| **Footprint** | Tiny (~2KB) script that pulls dependencies into venv. | Huge (~40MB+) package carrying embedded interpreter. |
| **Code Auditing** | Fully transparent. Easy for reviewers to audit script files. | Opaque. Blocks static verification and code reviews. |
| **Config Modifiability** | Fully integrates with the local `.env` and custom file paths. | Harder to debug relative path mappings inside static binaries. |
