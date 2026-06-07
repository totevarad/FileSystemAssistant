# LLM-Powered File System Assistant

A command-line utility that bridges **Large Language Models (LLMs)** with local file system operations. Using OpenAI's Function Calling, the assistant can search, read, list, and write files autonomously based on natural language commands.

---

## 📦 Prerequisites

- Python 3.10 or higher
- A [Groq API key](https://console.groq.com/keys)

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd FileSystemAssistant
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
# Copy the example file
copy .env.example .env    # Windows
cp .env.example .env      # macOS/Linux

# Edit .env and add your Groq API key (from https://console.groq.com/keys)
GROQ_API_KEY=gsk_...
LLM_MODEL=openai/gpt-oss-120b
RESUMES_DIR=resumes
OUTPUTS_DIR=outputs
```

---

## 🚀 Running the Assistant

```bash
python llm_file_assistant.py
```

You will be greeted with an interactive chat prompt:

```
File System Assistant — type 'exit' to quit

You: 
```

---

## 💬 Example Queries

| Query | What the LLM Does |
| :--- | :--- |
| `Read all resumes in the resumes folder` | Calls `list_files`, then `read_file` for each |
| `Find resumes mentioning Python experience` | Calls `list_files`, then `search_in_file` on each |
| `Create a summary file for john_doe.pdf` | Calls `read_file`, generates summary, calls `write_file` |
| `Find Python resumes and summarize each one` | Full pipeline: list → search → read → write |

---

## 📁 Project Structure

```
FileSystemAssistant/
├── docs/
│   ├── architecture.md       # System architecture documentation
│   └── problemStatement.md   # Assignment requirements
├── resumes/                  # Sample resume files (PDF, DOCX, TXT)
├── outputs/                  # Auto-generated output files
├── fs_tools.py               # Core file system tool functions (Part A)
├── llm_file_assistant.py     # LLM agent & CLI entrypoint (Part B)
├── requirements.txt          # Python dependencies
├── specs.md                  # Tech stack and rationale specification
├── howtouse.md               # User guide for starting the assistant
├── run.bat                   # Double-clickable Windows launcher
├── run.sh                    # Linux/macOS launcher script
├── .env.example              # Environment variable template
└── README.md                 # This file
```

---

## 🛠️ Core Tools (`fs_tools.py`)

| Function | Description |
| :--- | :--- |
| `read_file(filepath)` | Reads PDF, DOCX, or TXT and returns text + metadata |
| `list_files(directory, extension?)` | Lists files in a directory with optional type filter |
| `write_file(filepath, content)` | Writes text to a file, creating directories as needed |
| `search_in_file(filepath, keyword)` | Case-insensitive keyword search returning matching lines |

---

## 📤 Output File Naming Convention

When the assistant generates summary files, it follows this naming pattern:

| Scenario | Output Filename |
| :--- | :--- |
| First run | `resume_john_doe_output.txt` |
| Second run | `resume_john_doe_output_v1.txt` |
| Third run | `resume_john_doe_output_v2.txt` |

---

## 🤝 Dependencies

| Package | Purpose |
| :--- | :--- |
| `groq` | Groq LLM API client with Function Calling support |
| `pypdf` | PDF text extraction |
| `python-docx` | DOCX parsing |
| `python-dotenv` | `.env` configuration loading |
| `fpdf2` | Sample PDF generation (dev only) |
