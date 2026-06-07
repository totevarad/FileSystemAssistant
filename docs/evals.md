# Evaluation Checklist — LLM-Powered File System Assistant

This document provides a structured evaluation framework for each implementation phase.
Each phase contains:
- ✅ **Deliverable checklist** — items that must be present/working
- 🟢 **Positive test cases** — expected happy-path behavior
- 🔴 **Negative test cases** — edge cases, missing inputs, and failure modes

> **How to run tests**
> Always activate the virtual environment first:
> ```powershell
> .\venv\Scripts\Activate.ps1
> # or use the venv python directly:
> .\venv\Scripts\python.exe <script>
> ```

---

## Phase 1 — Scaffolding & Environment

### Deliverable Checklist

| # | Deliverable | How to Verify |
|:--|:---|:---|
| 1.1 | `requirements.txt` exists at project root | `Test-Path requirements.txt` → True |
| 1.2 | `requirements.txt` lists all 5 packages | Open file — check for `google-genai`, `pypdf`, `python-docx`, `python-dotenv`, `fpdf2` |
| 1.3 | `.env.example` exists with correct keys | Open file — check for `GEMINI_API_KEY`, `LLM_MODEL`, `RESUMES_DIR`, `OUTPUTS_DIR` |
| 1.4 | `.gitignore` excludes `.env` and `outputs/` | Open file — check for `.env` and `outputs/` entries |
| 1.5 | `README.md` exists with install instructions | Open file — check for `pip install`, `.env` setup, and usage sections |
| 1.6 | `resumes/` directory contains ≥ 5 sample files | `(Get-ChildItem resumes/).Count -ge 5` → True |
| 1.7 | Sample files cover PDF, DOCX, and TXT formats | Files present: `*.pdf`, `*.docx`, `*.txt` |
| 1.8 | `venv/` virtual environment created | `Test-Path venv\Scripts\python.exe` → True |
| 1.9 | All packages importable inside venv | Run import test (see below) |
| 1.10 | `.env` is NOT committed (excluded by gitignore) | `.env` absent from `git ls-files` output |

---

### 🟢 Positive Test Cases — Phase 1

#### P1-POS-01 — All packages import cleanly inside venv

```powershell
.\venv\Scripts\python.exe -c "
from google import genai
import pypdf
import docx
import dotenv
import fpdf
print('PASS: All packages imported successfully')
print('google-genai version:', genai.__version__)
"
```
**Expected output:** `PASS: All packages imported successfully`

---

#### P1-POS-02 — `requirements.txt` installs without errors in a fresh venv

```powershell
python -m venv venv_test
.\venv_test\Scripts\python.exe -m pip install -r requirements.txt --quiet
.\venv_test\Scripts\python.exe -c "from google import genai; print('PASS')"
# Cleanup
Remove-Item -Recurse -Force venv_test
```
**Expected output:** `PASS`

---

#### P1-POS-03 — `resumes/` contains all three file formats

```powershell
.\venv\Scripts\python.exe -c "
from pathlib import Path
files = list(Path('resumes').iterdir())
exts = {f.suffix for f in files}
assert '.pdf'  in exts, 'Missing PDF files'
assert '.docx' in exts, 'Missing DOCX files'
assert '.txt'  in exts, 'Missing TXT files'
assert len(files) >= 5, f'Expected >= 5 files, got {len(files)}'
print(f'PASS: {len(files)} resume files found — formats: {sorted(exts)}')
"
```
**Expected output:** `PASS: 8 resume files found — formats: ['.docx', '.pdf', '.txt']`

---

#### P1-POS-04 — `.env.example` has all required keys

```powershell
.\venv\Scripts\python.exe -c "
content = open('.env.example').read()
required = ['GEMINI_API_KEY', 'LLM_MODEL', 'RESUMES_DIR', 'OUTPUTS_DIR']
for key in required:
    assert key in content, f'Missing key: {key}'
print('PASS: All required keys present in .env.example')
"
```
**Expected output:** `PASS: All required keys present in .env.example`

---

#### P1-POS-05 — `.env` is protected by `.gitignore`

```powershell
git ls-files .env
```
**Expected output:** *(empty — `.env` should not be tracked)*

---

### 🔴 Negative Test Cases — Phase 1

#### P1-NEG-01 — Missing `.env` file is detected gracefully

```powershell
# Temporarily rename .env if it exists, then test behavior
.\venv\Scripts\python.exe -c "
from dotenv import load_dotenv
import os
load_dotenv('.env_nonexistent')
key = os.getenv('GEMINI_API_KEY')
if key is None:
    print('PASS: Missing .env returns None for GEMINI_API_KEY (expected)')
else:
    print('INFO: Key found from environment')
"
```
**Expected output:** `PASS: Missing .env returns None for GEMINI_API_KEY (expected)`

---

#### P1-NEG-02 — `resumes/` directory is empty or missing

```powershell
.\venv\Scripts\python.exe -c "
from pathlib import Path
d = Path('resumes_nonexistent')
exists = d.exists()
print(f'PASS: Non-existent directory exists={exists} (expected False)')
assert not exists
"
```
**Expected output:** `PASS: Non-existent directory exists=False (expected False)`

---

#### P1-NEG-03 — Wrong Python version check

```powershell
.\venv\Scripts\python.exe -c "
import sys
major, minor = sys.version_info[:2]
assert (major, minor) >= (3, 10), f'FAIL: Python {major}.{minor} < 3.10 required'
print(f'PASS: Python {major}.{minor} >= 3.10')
"
```
**Expected output:** `PASS: Python 3.x >= 3.10`

---

---

## Phase 2 — `fs_tools.py` (Service Layer)

### Deliverable Checklist

| # | Deliverable | How to Verify |
|:--|:---|:---|
| 2.1 | `fs_tools.py` exists at project root | `Test-Path fs_tools.py` → True |
| 2.2 | `read_file()` handles PDF format | Call with a `.pdf` path → `status: success` |
| 2.3 | `read_file()` handles DOCX format | Call with a `.docx` path → `status: success` |
| 2.4 | `read_file()` handles TXT format | Call with a `.txt` path → `status: success` |
| 2.5 | `read_file()` returns metadata dict | Response contains `metadata.file_size_bytes`, `file_type`, `character_count` |
| 2.6 | `list_files()` lists directory contents | Returns a list of dicts with `filename`, `filepath`, `size_bytes`, `modified_date` |
| 2.7 | `list_files()` filters by extension | `.pdf` filter returns only PDF files |
| 2.8 | `write_file()` creates file and directories | File and parent dirs are created |
| 2.9 | `write_file()` returns success dict | Response contains `status: success` |
| 2.10 | `search_in_file()` finds keyword | Returns matching lines with `line_number` and `context` |
| 2.11 | `search_in_file()` is case-insensitive | `python` matches lines containing `Python` or `PYTHON` |
| 2.12 | All functions return structured dicts — no raw exceptions | Error cases return `status: error` dicts |

---

### 🟢 Positive Test Cases — Phase 2

#### P2-POS-01 — `read_file()` reads a PDF resume

```python
# Run: .\venv\Scripts\python.exe -c "exec(open('test_p2.py').read())"
import fs_tools

result = fs_tools.read_file("resumes/john_doe.pdf")
assert result["status"] == "success",          f"FAIL: {result}"
assert "content" in result,                    "FAIL: No 'content' key"
assert len(result["content"]) > 100,           "FAIL: Content too short"
assert result["metadata"]["file_type"] == "pdf"
assert result["metadata"]["character_count"] > 0
print("PASS P2-POS-01: read_file PDF ->", result["metadata"])
```

---

#### P2-POS-02 — `read_file()` reads a DOCX resume

```python
result = fs_tools.read_file("resumes/alice_jones.docx")
assert result["status"] == "success",              f"FAIL: {result}"
assert result["metadata"]["file_type"] == "docx"
assert "leadership" in result["content"].lower(),  "FAIL: Expected 'leadership' in DOCX content"
print("PASS P2-POS-02: read_file DOCX ->", result["metadata"])
```

---

#### P2-POS-03 — `read_file()` reads a TXT resume

```python
result = fs_tools.read_file("resumes/emily_chen.txt")
assert result["status"] == "success",          f"FAIL: {result}"
assert result["metadata"]["file_type"] == "txt"
assert "python" in result["content"].lower(),  "FAIL: Expected 'python' in TXT content"
print("PASS P2-POS-03: read_file TXT ->", result["metadata"])
```

---

#### P2-POS-04 — `list_files()` lists all files without filter

```python
result = fs_tools.list_files("resumes")
assert isinstance(result, list),   "FAIL: Expected list"
assert len(result) >= 5,           f"FAIL: Expected >= 5 files, got {len(result)}"
for item in result:
    assert "filename"      in item, "FAIL: Missing 'filename'"
    assert "filepath"      in item, "FAIL: Missing 'filepath'"
    assert "size_bytes"    in item, "FAIL: Missing 'size_bytes'"
    assert "modified_date" in item, "FAIL: Missing 'modified_date'"
print(f"PASS P2-POS-04: list_files returned {len(result)} files")
```

---

#### P2-POS-05 — `list_files()` filters by `.pdf` extension

```python
result = fs_tools.list_files("resumes", extension=".pdf")
assert isinstance(result, list),                      "FAIL: Expected list"
assert all(f["filename"].endswith(".pdf") for f in result), "FAIL: Non-PDF in filtered list"
assert len(result) >= 1,                              "FAIL: Expected at least 1 PDF"
print(f"PASS P2-POS-05: list_files .pdf filter returned {len(result)} files: {[f['filename'] for f in result]}")
```

---

#### P2-POS-06 — `write_file()` writes content and creates parent directories

```python
import os
result = fs_tools.write_file("outputs/test/sample_output.txt", "Hello, File System!")
assert result["status"] == "success",                      f"FAIL: {result}"
assert os.path.exists("outputs/test/sample_output.txt"),   "FAIL: File not created"
assert open("outputs/test/sample_output.txt").read() == "Hello, File System!"
print("PASS P2-POS-06: write_file created nested directories and file")

# Cleanup
import shutil
shutil.rmtree("outputs/test", ignore_errors=True)
```

---

#### P2-POS-07 — `search_in_file()` returns matching lines with context

```python
result = fs_tools.search_in_file("resumes/emily_chen.txt", "Python")
assert "matches" in result,               "FAIL: No 'matches' key"
assert len(result["matches"]) > 0,        "FAIL: Expected matches for 'Python'"
assert result["keyword"] == "Python"
for match in result["matches"]:
    assert "line_number" in match,        "FAIL: Missing 'line_number'"
    assert "context"     in match,        "FAIL: Missing 'context'"
    assert "python" in match["context"].lower(), "FAIL: 'python' not in context"
print(f"PASS P2-POS-07: search_in_file found {result['match_count']} matches for 'Python'")
```

---

#### P2-POS-08 — `search_in_file()` is case-insensitive

```python
result_upper = fs_tools.search_in_file("resumes/emily_chen.txt", "PYTHON")
result_lower = fs_tools.search_in_file("resumes/emily_chen.txt", "python")
result_mixed = fs_tools.search_in_file("resumes/emily_chen.txt", "Python")
counts = {result_upper["match_count"], result_lower["match_count"], result_mixed["match_count"]}
assert len(counts) == 1, f"FAIL: Case sensitivity mismatch — counts: {counts}"
print(f"PASS P2-POS-08: case-insensitive search — all variants returned {counts.pop()} matches")
```

---

### 🔴 Negative Test Cases — Phase 2

#### P2-NEG-01 — `read_file()` on a non-existent file

```python
result = fs_tools.read_file("resumes/does_not_exist.pdf")
assert result["status"] == "error",             f"FAIL: Expected error, got {result['status']}"
assert result["error_code"] == "FILE_NOT_FOUND", f"FAIL: Wrong error code: {result.get('error_code')}"
assert "message" in result
print("PASS P2-NEG-01: read_file missing file ->", result["error_code"])
```

---

#### P2-NEG-02 — `read_file()` on an unsupported file extension

```python
# Create a dummy unsupported file
with open("resumes/test.xyz", "w") as f:
    f.write("dummy content")

result = fs_tools.read_file("resumes/test.xyz")
assert result["status"] == "error",                  f"FAIL: Expected error, got {result['status']}"
assert result["error_code"] == "UNSUPPORTED_FORMAT",  f"FAIL: Wrong code: {result.get('error_code')}"
print("PASS P2-NEG-02: read_file unsupported format ->", result["error_code"])

import os; os.remove("resumes/test.xyz")
```

---

#### P2-NEG-03 — `list_files()` on a non-existent directory

```python
result = fs_tools.list_files("nonexistent_directory")
assert isinstance(result, dict),                   "FAIL: Expected error dict"
assert result["status"] == "error",                f"FAIL: Expected error, got {result.get('status')}"
assert result["error_code"] == "INVALID_DIRECTORY", f"FAIL: Wrong code: {result.get('error_code')}"
print("PASS P2-NEG-03: list_files invalid directory ->", result["error_code"])
```

---

#### P2-NEG-04 — `list_files()` with a file path instead of directory

```python
result = fs_tools.list_files("resumes/carol_white.txt")
assert isinstance(result, dict),                   "FAIL: Expected error dict"
assert result["status"] == "error",                f"FAIL: Expected error, got {result.get('status')}"
assert result["error_code"] == "INVALID_DIRECTORY", f"FAIL: Wrong code: {result.get('error_code')}"
print("PASS P2-NEG-04: list_files on file path ->", result["error_code"])
```

---

#### P2-NEG-05 — `list_files()` with extension filter that matches no files

```python
result = fs_tools.list_files("resumes", extension=".csv")
assert isinstance(result, list), "FAIL: Expected empty list, got non-list"
assert len(result) == 0,         f"FAIL: Expected empty list, got {len(result)} items"
print("PASS P2-NEG-05: list_files no matches -> empty list []")
```

---

#### P2-NEG-06 — `search_in_file()` keyword with zero matches

```python
result = fs_tools.search_in_file("resumes/carol_white.txt", "blockchain_xyz_not_found")
assert "matches" in result,         "FAIL: No 'matches' key"
assert len(result["matches"]) == 0, f"FAIL: Expected 0 matches, got {len(result['matches'])}"
assert result["match_count"] == 0
print("PASS P2-NEG-06: search_in_file no matches -> match_count=0, matches=[]")
```

---

#### P2-NEG-07 — `search_in_file()` on a non-existent file

```python
result = fs_tools.search_in_file("resumes/ghost_file.txt", "Python")
assert result["status"] == "error",              f"FAIL: Expected error, got {result.get('status')}"
assert result["error_code"] == "FILE_NOT_FOUND",  f"FAIL: Wrong code: {result.get('error_code')}"
print("PASS P2-NEG-07: search_in_file missing file ->", result["error_code"])
```

---

#### P2-NEG-08 — No raw exceptions raised by any tool

```python
import traceback

tests = [
    (fs_tools.read_file, ["nonexistent.pdf"]),
    (fs_tools.read_file, ["resumes/test.xyz"]),
    (fs_tools.list_files, ["nonexistent_dir"]),
    (fs_tools.search_in_file, ["nonexistent.txt", "keyword"]),
]
for fn, args in tests:
    try:
        result = fn(*args)
        assert isinstance(result, (dict, list)), f"FAIL: {fn.__name__} returned {type(result)}"
    except Exception as e:
        print(f"FAIL: {fn.__name__}{tuple(args)} raised raw exception: {e}")
        traceback.print_exc()
        raise

print("PASS P2-NEG-08: No raw exceptions — all errors returned as structured dicts")
```

---

---

## Phase 3 — `llm_file_assistant.py` (Orchestration Layer)

### Deliverable Checklist

| # | Deliverable | How to Verify |
|:--|:---|:---|
| 3.1 | `llm_file_assistant.py` exists at project root | `Test-Path llm_file_assistant.py` → True |
| 3.2 | Script starts without errors when `.env` is set | `python llm_file_assistant.py` shows CLI prompt |
| 3.3 | Gemini client initializes with `GEMINI_API_KEY` | No `AuthenticationError` or `ValueError` on startup |
| 3.4 | Tool Schema Registry has all 4 tools registered | 4 schemas present in `TOOLS` list |
| 3.5 | Tool Dispatch Router maps all 4 tool names | Dispatch map contains `read_file`, `list_files`, `write_file`, `search_in_file` |
| 3.6 | System prompt is defined and non-empty | `SYSTEM_PROMPT` variable is a non-empty string |
| 3.7 | ReAct loop handles single-step tool call | LLM calls one tool and returns a final answer |
| 3.8 | ReAct loop handles multi-step tool call chain | LLM chains multiple tools in one query |
| 3.9 | Conversation history is maintained across turns | Follow-up query refers to prior context correctly |
| 3.10 | Output files follow naming convention | First output: `<name>_output.txt`, next: `<name>_output_v1.txt` |
| 3.11 | `exit` / `quit` terminates CLI cleanly | No traceback on clean exit |

---

### 🟢 Positive Test Cases — Phase 3

#### P3-POS-01 — LLM client initializes from `.env`

```python
# Run: .\venv\Scripts\python.exe -c "exec(open('test_p3_init.py').read())"
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
assert api_key and api_key != "your_gemini_api_key_here", \
    "FAIL: GEMINI_API_KEY not set in .env"

client = genai.Client(api_key=api_key)
print("PASS P3-POS-01: Gemini client initialized successfully")
```

---

#### P3-POS-02 — Tool Schema Registry has all 4 tools

```python
import llm_file_assistant as lfa

tool_names = {t.name for t in lfa.TOOLS}   # adjust to actual attribute structure
expected   = {"read_file", "list_files", "write_file", "search_in_file"}
missing    = expected - tool_names
assert not missing, f"FAIL: Missing tools in registry: {missing}"
print(f"PASS P3-POS-02: All 4 tools registered — {sorted(tool_names)}")
```

---

#### P3-POS-03 — Tool Dispatch Router maps all 4 tools

```python
import llm_file_assistant as lfa
import fs_tools

expected = {"read_file", "list_files", "write_file", "search_in_file"}
missing  = expected - set(lfa.TOOL_DISPATCH.keys())
assert not missing, f"FAIL: Missing dispatch entries: {missing}"

# Verify each value is callable
for name, fn in lfa.TOOL_DISPATCH.items():
    assert callable(fn), f"FAIL: Dispatch for '{name}' is not callable"

print(f"PASS P3-POS-03: Dispatch router has all 4 callable entries")
```

---

#### P3-POS-04 — Query: "List all files in the resumes folder" (single tool call)

```
Interactive test — run: .\venv\Scripts\python.exe llm_file_assistant.py

You: List all files in the resumes folder
```
**Expected behavior:**
- LLM calls `list_files(directory="resumes")`
- Returns a formatted list of all 8 resume files with names and sizes
- Does NOT call any other tool

---

#### P3-POS-05 — Query: "Read the resume of Emily Chen" (two-step: list → read)

```
You: Read the resume of Emily Chen
```
**Expected behavior:**
- LLM calls `list_files` or directly calls `read_file(filepath="resumes/emily_chen.txt")`
- Returns a summary or full text of Emily Chen's resume
- LLM produces a final natural-language response

---

#### P3-POS-06 — Query: "Find all resumes that mention Python" (multi-step: list → search × N)

```
You: Find all resumes that mention Python
```
**Expected behavior:**
- LLM calls `list_files(directory="resumes")`
- For each file, calls `search_in_file(filepath=..., keyword="Python")`
- Synthesizes results and names all Python-mentioning candidates
- Final answer lists: john_doe, jane_smith, emily_chen, michael_ross

---

#### P3-POS-07 — Query: "Summarize John Doe's resume and save it" (full pipeline)

```
You: Read John Doe's resume and write a professional summary to outputs/
```
**Expected behavior:**
- Calls `read_file("resumes/john_doe.pdf")`
- Generates a professional summary
- Calls `write_file("outputs/john_doe_output.txt", "<summary>")`
- Confirms the file was written
- Output file `outputs/john_doe_output.txt` exists on disk after the query

---

#### P3-POS-08 — Output file naming convention: first run vs. second run

```
# First run:
You: Create a summary for John Doe's resume
# Expected output file: outputs/john_doe_output.txt

# Second run (same session or next):
You: Create another summary for John Doe's resume
# Expected output file: outputs/john_doe_output_v1.txt
```
**Expected behavior:** The LLM respects the versioning naming convention from the system prompt.

---

#### P3-POS-09 — Conversation context preserved across turns

```
You: Find resumes mentioning Python
# (LLM responds with a list)

You: Now read the first one you found
# (LLM remembers the previous context and reads the correct file)
```
**Expected behavior:** LLM references the previously found file without the user re-specifying it.

---

#### P3-POS-10 — Clean exit via `exit` command

```
You: exit
```
**Expected behavior:** CLI exits gracefully with no traceback or exception.

---

### 🔴 Negative Test Cases — Phase 3

#### P3-NEG-01 — Missing `GEMINI_API_KEY` in `.env`

```python
# Temporarily unset the key
import os, sys
os.environ.pop("GEMINI_API_KEY", None)

try:
    import llm_file_assistant  # should raise or print a clear error
    print("WARN: Script loaded without API key — check for guard at startup")
except SystemExit as e:
    print(f"PASS P3-NEG-01: Script exited with code {e.code} when API key missing")
except Exception as e:
    print(f"PASS P3-NEG-01: Startup error raised: {type(e).__name__}: {e}")
```
**Expected behavior:** Script detects missing API key and exits or raises a clear error — NOT an unhandled `KeyError` or obscure traceback.

---

#### P3-NEG-02 — LLM asked to operate on a non-existent file

```
You: Read the resume of "Zara Phantom" who doesn't exist
```
**Expected behavior:**
- LLM calls `list_files` or `read_file` with the phantom name
- `read_file` returns `FILE_NOT_FOUND` error dict
- LLM reads the error response and tells the user the file was not found
- Does NOT crash or hallucinate file contents

---

#### P3-NEG-03 — LLM asked to search for a keyword with no matches

```
You: Find resumes that mention blockchain or COBOL
```
**Expected behavior:**
- LLM calls `search_in_file` for each resume
- All return `match_count: 0`
- LLM synthesizes: "No resumes mention blockchain or COBOL"
- Does NOT fabricate results

---

#### P3-NEG-04 — Tool call with wrong argument types handled gracefully

```python
# Simulate what would happen if LLM passes bad args
import fs_tools
result = fs_tools.list_files(None)   # None instead of string
assert isinstance(result, dict), "FAIL: Expected error dict for None directory"
assert result["status"] == "error"
print("PASS P3-NEG-04: list_files(None) returned structured error")
```

---

#### P3-NEG-05 — Empty user input is handled gracefully

```
You:         (press Enter with empty input)
```
**Expected behavior:** CLI re-prompts without calling the LLM or crashing.

---

---

## Phase 4 — Polish & Deliverables

### Deliverable Checklist

| # | Deliverable | How to Verify |
|:--|:---|:---|
| 4.1 | `README.md` has installation section | Check for `pip install` or `venv` instructions |
| 4.2 | `README.md` has `.env` configuration section | Check for `GEMINI_API_KEY` setup instructions |
| 4.3 | `README.md` has at least 3 example queries | Check for query examples with expected LLM paths |
| 4.4 | `fs_tools.py` functions all have docstrings | Inspect each function definition |
| 4.5 | `llm_file_assistant.py` functions all have docstrings | Inspect each function definition |
| 4.6 | All 3 canonical end-to-end queries work correctly | Run each query and verify output |
| 4.7 | Error scenarios handled gracefully in live session | Query bad file, keyword with no match, empty input |
| 4.8 | Demo video covers all 3 canonical queries | Watch video — verify all 3 queries are shown |
| 4.9 | Demo video is 2–3 minutes long | Video duration between 120s–180s |
| 4.10 | Output files exist after demo session | `outputs/` directory has `.txt` files after queries |

---

### 🟢 Positive Test Cases — Phase 4

#### P4-POS-01 — README completeness check

```python
readme = open("README.md").read()
required_sections = [
    "Prerequisites",
    "Installation",
    "pip install",
    "GEMINI_API_KEY",
    "python llm_file_assistant.py",
    "Example",
]
for section in required_sections:
    assert section in readme, f"FAIL: README missing section: '{section}'"
print("PASS P4-POS-01: README contains all required sections")
```

---

#### P4-POS-02 — All functions have docstrings

```python
import ast, sys

for module_file in ["fs_tools.py", "llm_file_assistant.py"]:
    try:
        tree = ast.parse(open(module_file).read())
    except FileNotFoundError:
        print(f"SKIP: {module_file} not yet created")
        continue

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            ds = ast.get_docstring(node)
            if not ds:
                print(f"FAIL: {module_file}::{node.name}() is missing a docstring")
            else:
                print(f"  OK: {module_file}::{node.name}()")

print("PASS P4-POS-02: Docstring check complete")
```

---

#### P4-POS-03 — Canonical query 1: "Read all resumes in the resumes folder"

```
# Interactive end-to-end test
You: Read all resumes in the resumes folder
```
**Expected tool call sequence:** `list_files("resumes")` → `read_file(...)` × 8
**Expected final response:** Summary or listing of all 8 resume contents

---

#### P4-POS-04 — Canonical query 2: "Find resumes mentioning Python experience"

```
You: Find resumes mentioning Python experience
```
**Expected tool call sequence:** `list_files("resumes")` → `search_in_file(..., "Python")` × 8
**Expected final response:** Names john_doe, jane_smith, emily_chen, michael_ross (4 matches)

---

#### P4-POS-05 — Canonical query 3: "Create a summary file for john_doe.pdf"

```
You: Create a summary file for john_doe.pdf
```
**Expected tool call sequence:** `read_file("resumes/john_doe.pdf")` → `write_file("outputs/john_doe_output.txt", ...)`
**Post-condition check:**
```powershell
.\venv\Scripts\python.exe -c "
import os
assert os.path.exists('outputs/john_doe_output.txt'), 'FAIL: Output file not created'
content = open('outputs/john_doe_output.txt').read()
assert len(content) > 50, 'FAIL: Output file is nearly empty'
print('PASS P4-POS-05: Summary file created at outputs/john_doe_output.txt')
print('Preview:', content[:200])
"
```

---

#### P4-POS-06 — All outputs follow naming convention

```python
import os
from pathlib import Path

output_files = list(Path("outputs").glob("*.txt")) if Path("outputs").exists() else []
for f in output_files:
    name = f.stem  # filename without extension
    assert "_output" in name, f"FAIL: '{f.name}' does not follow _output naming convention"
    print(f"  OK: {f.name} follows naming convention")

print(f"PASS P4-POS-06: {len(output_files)} output files all follow naming convention")
```

---

### 🔴 Negative Test Cases — Phase 4

#### P4-NEG-01 — Full pipeline error recovery: querying a non-existent file

```
You: Summarize the resume of "John Nobody" and save it
```
**Expected behavior:**
- LLM searches/reads and encounters `FILE_NOT_FOUND`
- Responds: "I could not find a resume for 'John Nobody'"
- Does NOT create an empty output file or hallucinate content
- **Post-condition:** No spurious file created in `outputs/`

---

#### P4-NEG-02 — Keyword search with no results produces honest answer

```
You: Find resumes that mention assembly language or FORTRAN
```
**Expected behavior:**
- LLM runs `search_in_file` on all resumes
- All return `match_count: 0`
- LLM responds: "None of the resumes mention assembly language or FORTRAN"
- Does NOT fabricate match results

---

#### P4-NEG-03 — Repeated summary request triggers versioning

```
# Turn 1
You: Create a summary for carol_white.txt
# Creates outputs/carol_white_output.txt

# Turn 2
You: Create another summary for carol_white.txt
# Should create outputs/carol_white_output_v1.txt — NOT overwrite the first
```
**Post-condition check:**
```python
import os
assert os.path.exists("outputs/carol_white_output.txt"),    "FAIL: v0 file missing"
assert os.path.exists("outputs/carol_white_output_v1.txt"), "FAIL: v1 file missing — versioning not working"
print("PASS P4-NEG-03: Versioning convention respected — both files exist")
```

---

#### P4-NEG-04 — Script handles `Ctrl+C` interrupt gracefully

```
# While CLI is running, press Ctrl+C
^C
```
**Expected behavior:** Clean exit message printed — no ugly traceback exposed to user.

---

---

## Quick Reference — Run All Static Checks

Save the following as `run_evals.py` and run with:
```powershell
.\venv\Scripts\python.exe run_evals.py
```

```python
"""Quick static evaluation script for Phases 1 & 2."""
from pathlib import Path
import sys

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"

def check(label, condition, detail=""):
    if condition:
        print(f"{PASS} {label}")
    else:
        print(f"{FAIL} {label}" + (f" — {detail}" if detail else ""))

# ── Phase 1 checks ──────────────────────────────────────────────────────────
print("\n=== Phase 1: Scaffolding ===")
check("requirements.txt exists",   Path("requirements.txt").exists())
check("google-genai in requirements", "google-genai" in Path("requirements.txt").read_text())
check(".env.example exists",       Path(".env.example").exists())
check("GEMINI_API_KEY in .env.example", "GEMINI_API_KEY" in Path(".env.example").read_text())
check(".gitignore exists",         Path(".gitignore").exists())
check(".env in .gitignore",        ".env" in Path(".gitignore").read_text())
check("README.md exists",          Path("README.md").exists())
check("venv created",              Path("venv/Scripts/python.exe").exists())
resume_files = list(Path("resumes").glob("*")) if Path("resumes").exists() else []
check(f"resumes/ has >= 5 files ({len(resume_files)} found)", len(resume_files) >= 5)
exts = {f.suffix for f in resume_files}
check("PDF resumes present",  ".pdf"  in exts)
check("DOCX resumes present", ".docx" in exts)
check("TXT resumes present",  ".txt"  in exts)

# ── Phase 2 checks ──────────────────────────────────────────────────────────
print("\n=== Phase 2: fs_tools.py ===")
if not Path("fs_tools.py").exists():
    print(f"{SKIP} fs_tools.py not yet created — skipping Phase 2 checks")
else:
    import fs_tools

    # read_file
    r = fs_tools.read_file("resumes/john_doe.pdf")
    check("read_file PDF status=success",       r.get("status") == "success")
    check("read_file PDF has content",           len(r.get("content","")) > 50)
    check("read_file PDF has metadata",          "metadata" in r)

    r2 = fs_tools.read_file("resumes/emily_chen.txt")
    check("read_file TXT status=success",        r2.get("status") == "success")

    r3 = fs_tools.read_file("resumes/alice_jones.docx")
    check("read_file DOCX status=success",       r3.get("status") == "success")

    bad = fs_tools.read_file("resumes/nonexistent.pdf")
    check("read_file missing -> error",          bad.get("status") == "error")
    check("read_file missing -> FILE_NOT_FOUND", bad.get("error_code") == "FILE_NOT_FOUND")

    # list_files
    lst = fs_tools.list_files("resumes")
    check("list_files returns list",             isinstance(lst, list))
    check("list_files has >= 5 items",           len(lst) >= 5)

    lst_pdf = fs_tools.list_files("resumes", ".pdf")
    check("list_files .pdf filter",              all(f["filename"].endswith(".pdf") for f in lst_pdf))

    bad_dir = fs_tools.list_files("nonexistent_dir")
    check("list_files bad dir -> error",         isinstance(bad_dir, dict) and bad_dir.get("status") == "error")

    # write_file
    wr = fs_tools.write_file("outputs/_eval_test.txt", "eval test content")
    check("write_file status=success",           wr.get("status") == "success")
    check("write_file file created on disk",     Path("outputs/_eval_test.txt").exists())
    Path("outputs/_eval_test.txt").unlink(missing_ok=True)

    # search_in_file
    sr = fs_tools.search_in_file("resumes/emily_chen.txt", "Python")
    check("search_in_file has matches",          sr.get("match_count", 0) > 0)
    check("search_in_file match has line_number", all("line_number" in m for m in sr.get("matches",[])))

    sr_none = fs_tools.search_in_file("resumes/emily_chen.txt", "xyz_not_found_123")
    check("search_in_file no matches -> count=0", sr_none.get("match_count") == 0)

    sr_bad = fs_tools.search_in_file("resumes/ghost.txt", "Python")
    check("search_in_file bad file -> error",    sr_bad.get("status") == "error")

print("\n=== Phase 3 & 4: Interactive tests only — run manually ===")
print("See evals.md for query scripts and expected behaviors.\n")
```
