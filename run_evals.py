"""
run_evals.py â€” Quick static evaluation script for Phases 1 & 2.

Usage:
    .\\venv\\Scripts\\python.exe run_evals.py

Phase 3 & 4 evaluations require interactive testing â€” see docs/evals.md.
"""

from pathlib import Path
import sys

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"
WARN = "[WARN]"


def check(label: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    suffix = f" â€” {detail}" if detail and not condition else ""
    print(f"  {status} {label}{suffix}")


def section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# â”€â”€ Phase 1: Scaffolding & Environment â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

section("Phase 1 â€” Scaffolding & Environment")

req = Path("requirements.txt")
check("requirements.txt exists", req.exists())
if req.exists():
    req_text = req.read_text(encoding="utf-8")
    check("google-genai in requirements.txt",   "google-genai"   in req_text)
    check("pypdf in requirements.txt",          "pypdf"          in req_text)
    check("python-docx in requirements.txt",    "python-docx"    in req_text)
    check("python-dotenv in requirements.txt",  "python-dotenv"  in req_text)
    check("fpdf2 in requirements.txt",          "fpdf2"          in req_text)

env_ex = Path(".env.example")
check(".env.example exists", env_ex.exists())
if env_ex.exists():
    env_text = env_ex.read_text(encoding="utf-8")
    check("GEMINI_API_KEY in .env.example",  "GEMINI_API_KEY"  in env_text)
    check("LLM_MODEL in .env.example",       "LLM_MODEL"       in env_text)
    check("RESUMES_DIR in .env.example",     "RESUMES_DIR"     in env_text)
    check("OUTPUTS_DIR in .env.example",     "OUTPUTS_DIR"     in env_text)

gi = Path(".gitignore")
check(".gitignore exists", gi.exists())
if gi.exists():
    gi_text = gi.read_text(encoding="utf-8")
    check(".env in .gitignore",     ".env"     in gi_text)
    check("outputs/ in .gitignore", "outputs/" in gi_text)
    check("__pycache__/ in .gitignore", "__pycache__/" in gi_text)

check("README.md exists", Path("README.md").exists())
if Path("README.md").exists():
    rm_text = Path("README.md").read_text(encoding="utf-8")
    check("README has install section",    "pip install"     in rm_text)
    check("README has GEMINI_API_KEY",     "GEMINI_API_KEY"  in rm_text)
    check("README has run instructions",   "llm_file_assistant.py" in rm_text)

check("venv/Scripts/python.exe exists", Path("venv/Scripts/python.exe").exists())

resumes_dir = Path("resumes")
check("resumes/ directory exists", resumes_dir.exists() and resumes_dir.is_dir())
if resumes_dir.exists():
    resume_files = [f for f in resumes_dir.iterdir() if f.is_file()]
    exts = {f.suffix for f in resume_files}
    check(f"resumes/ has >= 5 files ({len(resume_files)} found)", len(resume_files) >= 5)
    check(".pdf resumes present",  ".pdf"  in exts)
    check(".docx resumes present", ".docx" in exts)
    check(".txt resumes present",  ".txt"  in exts)

env_file = Path(".env")
if env_file.exists():
    env_content = env_file.read_text(encoding="utf-8")
    has_real_key = "GEMINI_API_KEY" in env_content and "your_gemini_api_key_here" not in env_content
    check(".env has real GEMINI_API_KEY set", has_real_key,
          "Key still has placeholder value" if not has_real_key else "")
else:
    print(f"  {WARN} .env file not found â€” create it from .env.example before Phase 3")


# â”€â”€ Phase 2: fs_tools.py â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

section("Phase 2 â€” fs_tools.py (Service Layer)")

if not Path("fs_tools.py").exists():
    print(f"  {SKIP} fs_tools.py not yet created â€” skipping all Phase 2 checks")
else:
    try:
        import fs_tools
    except Exception as e:
        print(f"  {FAIL} Cannot import fs_tools.py: {e}")
        sys.exit(1)

    # --- read_file: PDF ---
    r_pdf = fs_tools.read_file("resumes/john_doe.pdf")
    check("read_file('john_doe.pdf') status=success",        r_pdf.get("status") == "success")
    check("read_file PDF has content",                       len(r_pdf.get("content", "")) > 50)
    check("read_file PDF has metadata dict",                 isinstance(r_pdf.get("metadata"), dict))
    check("read_file PDF metadata.file_type = 'pdf'",        r_pdf.get("metadata", {}).get("file_type") == "pdf")
    check("read_file PDF metadata.character_count > 0",      r_pdf.get("metadata", {}).get("character_count", 0) > 0)
    check("read_file PDF metadata.file_size_bytes > 0",      r_pdf.get("metadata", {}).get("file_size_bytes", 0) > 0)

    # --- read_file: TXT ---
    r_txt = fs_tools.read_file("resumes/emily_chen.txt")
    check("read_file('emily_chen.txt') status=success",      r_txt.get("status") == "success")
    check("read_file TXT metadata.file_type = 'txt'",        r_txt.get("metadata", {}).get("file_type") == "txt")
    check("read_file TXT content contains 'Python'",         "python" in r_txt.get("content", "").lower())

    # --- read_file: DOCX ---
    r_docx = fs_tools.read_file("resumes/alice_jones.docx")
    check("read_file('alice_jones.docx') status=success",    r_docx.get("status") == "success")
    check("read_file DOCX metadata.file_type = 'docx'",      r_docx.get("metadata", {}).get("file_type") == "docx")
    check("read_file DOCX content contains 'leadership'",    "leadership" in r_docx.get("content", "").lower())

    # --- read_file: missing file ---
    r_miss = fs_tools.read_file("resumes/ghost_123.pdf")
    check("read_file missing file -> status=error",          r_miss.get("status") == "error")
    check("read_file missing file -> FILE_NOT_FOUND",        r_miss.get("error_code") == "FILE_NOT_FOUND")
    check("read_file missing file -> has 'message' key",     "message" in r_miss)

    # --- read_file: unsupported format ---
    Path("resumes/_test_unsupported.xyz").write_text("dummy")
    r_bad = fs_tools.read_file("resumes/_test_unsupported.xyz")
    check("read_file .xyz -> status=error",                  r_bad.get("status") == "error")
    check("read_file .xyz -> UNSUPPORTED_FORMAT",            r_bad.get("error_code") == "UNSUPPORTED_FORMAT")
    Path("resumes/_test_unsupported.xyz").unlink(missing_ok=True)

    # --- list_files: no filter ---
    lst_all = fs_tools.list_files("resumes")
    check("list_files('resumes') returns list",              isinstance(lst_all, list))
    check("list_files('resumes') has >= 5 entries",          len(lst_all) >= 5)
    if lst_all:
        sample = lst_all[0]
        check("list_files entry has 'filename'",             "filename"      in sample)
        check("list_files entry has 'filepath'",             "filepath"      in sample)
        check("list_files entry has 'size_bytes'",           "size_bytes"    in sample)
        check("list_files entry has 'modified_date'",        "modified_date" in sample)

    # --- list_files: extension filter ---
    lst_pdf = fs_tools.list_files("resumes", extension=".pdf")
    check("list_files('.pdf') returns only PDFs",            all(f["filename"].endswith(".pdf") for f in lst_pdf))
    check("list_files('.pdf') has >= 1 result",              len(lst_pdf) >= 1)

    lst_csv = fs_tools.list_files("resumes", extension=".csv")
    check("list_files('.csv') returns empty list",           isinstance(lst_csv, list) and len(lst_csv) == 0)

    # --- list_files: bad directory ---
    lst_bad = fs_tools.list_files("nonexistent_xyz_dir")
    check("list_files bad dir -> error dict",                isinstance(lst_bad, dict))
    check("list_files bad dir -> status=error",              lst_bad.get("status") == "error")
    check("list_files bad dir -> INVALID_DIRECTORY",         lst_bad.get("error_code") == "INVALID_DIRECTORY")

    lst_file = fs_tools.list_files("resumes/carol_white.txt")
    check("list_files on file path -> INVALID_DIRECTORY",    lst_file.get("error_code") == "INVALID_DIRECTORY")

    # --- write_file ---
    wr = fs_tools.write_file("outputs/_eval_test/check.txt", "eval content")
    check("write_file status=success",                       wr.get("status") == "success")
    check("write_file created nested directories",           Path("outputs/_eval_test/check.txt").exists())
    check("write_file content correct",                      Path("outputs/_eval_test/check.txt").read_text(encoding="utf-8") == "eval content")
    import shutil
    shutil.rmtree("outputs/_eval_test", ignore_errors=True)

    # --- search_in_file ---
    sr = fs_tools.search_in_file("resumes/emily_chen.txt", "Python")
    check("search_in_file returns dict",                     isinstance(sr, dict))
    check("search_in_file 'Python' match_count > 0",         sr.get("match_count", 0) > 0)
    check("search_in_file matches is a list",                isinstance(sr.get("matches"), list))
    if sr.get("matches"):
        m = sr["matches"][0]
        check("search_in_file match has 'line_number'",      "line_number" in m)
        check("search_in_file match has 'context'",          "context"     in m)
        check("search_in_file context contains keyword",     "python" in m.get("context", "").lower())

    # --- search_in_file: case insensitivity ---
    sr_u = fs_tools.search_in_file("resumes/emily_chen.txt", "PYTHON")
    sr_l = fs_tools.search_in_file("resumes/emily_chen.txt", "python")
    sr_m = fs_tools.search_in_file("resumes/emily_chen.txt", "Python")
    counts = {sr_u["match_count"], sr_l["match_count"], sr_m["match_count"]}
    check("search_in_file case-insensitive (all variants equal)", len(counts) == 1)

    # --- search_in_file: no matches ---
    sr_0 = fs_tools.search_in_file("resumes/carol_white.txt", "xyz_not_found_123")
    check("search_in_file no match -> match_count=0",        sr_0.get("match_count") == 0)
    check("search_in_file no match -> matches=[]",           sr_0.get("matches") == [])

    # --- search_in_file: missing file ---
    sr_bad = fs_tools.search_in_file("resumes/ghost_999.txt", "Python")
    check("search_in_file missing file -> status=error",     sr_bad.get("status") == "error")
    check("search_in_file missing file -> FILE_NOT_FOUND",   sr_bad.get("error_code") == "FILE_NOT_FOUND")

    # --- no raw exceptions ---
    raw_ex_cases = [
        ("read_file missing",    lambda: fs_tools.read_file("nonexistent.pdf")),
        ("list_files bad dir",   lambda: fs_tools.list_files("nonexistent_dir")),
        ("search_in_file miss",  lambda: fs_tools.search_in_file("nope.txt", "kw")),
    ]
    for label, fn in raw_ex_cases:
        try:
            result = fn()
            is_structured = isinstance(result, (dict, list))
            check(f"No raw exception â€” {label}", is_structured)
        except Exception as exc:
            check(f"No raw exception â€” {label}", False, f"Raised {type(exc).__name__}: {exc}")


# â”€â”€ Phase 3 & 4 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

section("Phase 3 & 4 â€” Interactive / Manual Tests Only")
print("  See docs/evals.md for the full interactive test scripts.")
print("  Run: .\\venv\\Scripts\\python.exe llm_file_assistant.py")

print("\n" + "="*60)
print("  Evaluation complete.")
print("="*60 + "\n")

