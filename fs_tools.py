"""
fs_tools.py — Core File System Tool Functions (Part A)

This module implements the four deterministic file-system utilities used by the
LLM-Powered File System Assistant. It is completely independent of the LLM layer
and can be tested in isolation.

Functions:
    read_file(filepath)        → dict   Read PDF, DOCX, or TXT and return text + metadata
    list_files(directory, ...) → list   List files in a directory with optional extension filter
    write_file(filepath, ...)  → dict   Write text content to a file (auto-creates directories)
    search_in_file(filepath, ...)→ dict Case-insensitive keyword search returning matching lines

Error Contract:
    No function ever raises a raw exception to the caller.
    All failures are returned as structured error dicts:
        {"status": "error", "error_code": "<CODE>", "message": "<description>"}
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Internal Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _error(error_code: str, message: str) -> dict:
    """Return a standard error payload dict."""
    return {
        "status": "error",
        "error_code": error_code,
        "message": message,
    }


def _extract_pdf_text(filepath: Path) -> str:
    """Extract plain text from a PDF file using pypdf."""
    import pypdf  # lazy import — keeps startup fast if only txt/docx needed

    reader = pypdf.PdfReader(str(filepath))
    pages_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages_text.append(text)
    return "\n".join(pages_text)


def _extract_docx_text(filepath: Path) -> str:
    """Extract plain text from a DOCX file using python-docx."""
    from docx import Document  # lazy import

    doc = Document(str(filepath))
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(paragraphs)


def _extract_txt_text(filepath: Path) -> str:
    """Read a plain-text file, falling back from UTF-8 to latin-1 on decode errors."""
    try:
        return filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return filepath.read_text(encoding="latin-1")


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────


def read_file(filepath: str) -> dict:
    """
    Read and extract structured text and metadata from a local file.

    Supports the following formats: PDF (.pdf), Word document (.docx),
    and plain text (.txt).

    Args:
        filepath (str): Absolute or relative path to the target file.

    Returns:
        dict: On success —
            {
                "status": "success",
                "filepath": str,
                "metadata": {
                    "file_size_bytes": int,
                    "file_type": str,       # "pdf" | "docx" | "txt"
                    "character_count": int,
                },
                "content": str,
            }
        dict: On failure —
            {
                "status": "error",
                "error_code": str,    # FILE_NOT_FOUND | PARSING_FAILED |
                                      # PERMISSION_DENIED | UNSUPPORTED_FORMAT
                "message": str,
            }

    Examples:
        >>> read_file("resumes/john_doe.pdf")
        {"status": "success", "filepath": "resumes/john_doe.pdf", ...}

        >>> read_file("resumes/ghost.pdf")
        {"status": "error", "error_code": "FILE_NOT_FOUND", ...}
    """
    path = Path(filepath)
    extension = path.suffix.lower()

    # ── Existence check ──────────────────────────────────────────────────────
    try:
        if not path.exists():
            return _error(
                "FILE_NOT_FOUND",
                f"File '{filepath}' does not exist.",
            )
    except PermissionError:
        return _error(
            "PERMISSION_DENIED",
            f"Read access denied for path '{filepath}'.",
        )

    # ── Format validation ────────────────────────────────────────────────────
    supported_extensions = {".pdf", ".docx", ".txt"}
    if extension not in supported_extensions:
        return _error(
            "UNSUPPORTED_FORMAT",
            f"Unsupported file format '{extension}'. "
            f"Supported formats: {', '.join(sorted(supported_extensions))}.",
        )

    # ── Metadata (size) ──────────────────────────────────────────────────────
    try:
        file_size_bytes = path.stat().st_size
    except PermissionError:
        return _error(
            "PERMISSION_DENIED",
            f"Read access denied for path '{filepath}'.",
        )

    # ── Content extraction ───────────────────────────────────────────────────
    try:
        if extension == ".pdf":
            content = _extract_pdf_text(path)
            file_type = "pdf"

        elif extension == ".docx":
            content = _extract_docx_text(path)
            file_type = "docx"

        else:  # .txt
            content = _extract_txt_text(path)
            file_type = "txt"

    except PermissionError:
        return _error(
            "PERMISSION_DENIED",
            f"Read access denied while reading '{filepath}'.",
        )
    except Exception as exc:
        return _error(
            "PARSING_FAILED",
            f"Unable to parse file '{filepath}': {type(exc).__name__}: {exc}",
        )

    return {
        "status": "success",
        "filepath": str(filepath),
        "metadata": {
            "file_size_bytes": file_size_bytes,
            "file_type": file_type,
            "character_count": len(content),
        },
        "content": content,
    }


# ─────────────────────────────────────────────────────────────────────────────


def list_files(directory: str, extension: Optional[str] = None) -> list | dict:
    """
    List all files within a directory, with optional file-extension filtering.

    Performs a non-recursive scan of the target directory. Each file is
    represented as a metadata dictionary containing its name, path, size,
    and last-modified timestamp.

    Args:
        directory (str): Path to the directory to scan.
        extension (str, optional): Filter files by this extension, including
            the leading dot (e.g., '.pdf', '.txt'). Case-insensitive.
            If None or empty, all files are returned.

    Returns:
        list: On success — a list of dicts, one per matching file:
            [
                {
                    "filename": str,
                    "filepath": str,
                    "size_bytes": int,
                    "modified_date": str,   # ISO 8601 UTC, e.g. "2026-06-01T15:30:00Z"
                },
                ...
            ]
            Returns an empty list [] if no files match the filter.

        dict: On failure —
            {
                "status": "error",
                "error_code": "INVALID_DIRECTORY",
                "message": str,
            }

    Examples:
        >>> list_files("resumes")
        [{"filename": "john_doe.pdf", "filepath": "resumes/john_doe.pdf", ...}, ...]

        >>> list_files("resumes", extension=".pdf")
        [{"filename": "john_doe.pdf", ...}, {"filename": "jane_smith.pdf", ...}]

        >>> list_files("nonexistent_dir")
        {"status": "error", "error_code": "INVALID_DIRECTORY", ...}
    """
    dir_path = Path(directory)

    # ── Validation ───────────────────────────────────────────────────────────
    if not dir_path.exists():
        return _error(
            "INVALID_DIRECTORY",
            f"Path '{directory}' does not exist.",
        )

    if not dir_path.is_dir():
        return _error(
            "INVALID_DIRECTORY",
            f"Path '{directory}' is not a directory.",
        )

    # Normalize extension filter
    ext_filter = extension.lower() if extension else None

    # ── Directory scan ───────────────────────────────────────────────────────
    results = []
    try:
        for entry in sorted(dir_path.iterdir()):
            if not entry.is_file():
                continue

            # Apply extension filter if provided
            if ext_filter and entry.suffix.lower() != ext_filter:
                continue

            try:
                stat = entry.stat()
                size_bytes = stat.st_size
                # Convert mtime (Unix timestamp) to ISO 8601 UTC string
                modified_dt = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                modified_date = modified_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except OSError:
                # If stat fails for one file, skip it gracefully
                continue

            results.append({
                "filename": entry.name,
                "filepath": str(entry),
                "size_bytes": size_bytes,
                "modified_date": modified_date,
            })

    except PermissionError:
        return _error(
            "INVALID_DIRECTORY",
            f"Permission denied when reading directory '{directory}'.",
        )

    return results


# ─────────────────────────────────────────────────────────────────────────────


def write_file(filepath: str, content: str) -> dict:
    """
    Write text content to a specified file path.

    Automatically creates any missing parent directories in the path so that
    callers never need to pre-create folder structures.

    Args:
        filepath (str): Target file path to write content into.
            Parent directories are created dynamically if they don't exist.
        content (str): The string payload to write into the file (UTF-8 encoded).

    Returns:
        dict: On success —
            {
                "status": "success",
                "filepath": str,
                "message": "File written successfully.",
            }
        dict: On failure —
            {
                "status": "error",
                "error_code": str,    # IO_ERROR | PERMISSION_DENIED
                "message": str,
            }

    Examples:
        >>> write_file("outputs/john_doe_output.txt", "Summary: John is a Python engineer.")
        {"status": "success", "filepath": "outputs/john_doe_output.txt", ...}

        >>> write_file("/read_only_dir/file.txt", "content")
        {"status": "error", "error_code": "PERMISSION_DENIED", ...}
    """
    target = Path(filepath)

    # ── Create parent directories ─────────────────────────────────────────────
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        return _error(
            "PERMISSION_DENIED",
            f"Permission denied creating directories for '{filepath}'.",
        )
    except OSError as exc:
        return _error(
            "IO_ERROR",
            f"Failed to create parent directories for '{filepath}': {exc}",
        )

    # ── Write content ─────────────────────────────────────────────────────────
    try:
        target.write_text(content, encoding="utf-8")
    except PermissionError:
        return _error(
            "PERMISSION_DENIED",
            f"Write access denied for path '{filepath}'.",
        )
    except (OSError, IOError) as exc:
        return _error(
            "IO_ERROR",
            f"Failed to write content to '{filepath}': {exc}",
        )

    return {
        "status": "success",
        "filepath": str(filepath),
        "message": "File written successfully.",
    }


# ─────────────────────────────────────────────────────────────────────────────


def search_in_file(filepath: str, keyword: str) -> dict:
    """
    Perform a case-insensitive keyword search within a file's text content.

    Internally delegates file reading to read_file(), so it supports the same
    formats (PDF, DOCX, TXT) and inherits its error handling.

    A "match" is any line that contains the keyword substring, case-insensitively.
    The full line (stripped of leading/trailing whitespace) is returned as context.

    Args:
        filepath (str): Path to the target file to search within.
        keyword (str): The search term. Case-insensitive substring match.

    Returns:
        dict: On success (even if no matches found) —
            {
                "status": "success",
                "filepath": str,
                "keyword": str,
                "match_count": int,
                "matches": [
                    {
                        "line_number": int,   # 1-indexed
                        "context": str,       # full trimmed line containing keyword
                    },
                    ...
                ],
            }
        dict: On failure (file missing, parse error, etc.) — propagates the
            error dict from read_file() directly:
            {
                "status": "error",
                "error_code": str,
                "message": str,
            }

    Examples:
        >>> search_in_file("resumes/emily_chen.txt", "Python")
        {"status": "success", "match_count": 6, "matches": [...]}

        >>> search_in_file("resumes/carol_white.txt", "xyz_not_found")
        {"status": "success", "match_count": 0, "matches": []}

        >>> search_in_file("resumes/ghost.txt", "Python")
        {"status": "error", "error_code": "FILE_NOT_FOUND", ...}
    """
    # ── Read file content (delegates format detection + error handling) ───────
    read_result = read_file(filepath)

    # Propagate any read error directly
    if read_result.get("status") == "error":
        return read_result

    content: str = read_result["content"]
    keyword_lower = keyword.lower()

    # ── Line-by-line search ───────────────────────────────────────────────────
    matches = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if keyword_lower in stripped.lower():
            matches.append({
                "line_number": line_number,
                "context": stripped,
            })

    return {
        "status": "success",
        "filepath": str(filepath),
        "keyword": keyword,
        "match_count": len(matches),
        "matches": matches,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI — Manual Testing Helper
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    print("\n--- read_file: TXT ---")
    print(json.dumps(read_file("resumes/emily_chen.txt"), indent=2)[:500])

    print("\n--- read_file: PDF ---")
    print(json.dumps(read_file("resumes/john_doe.pdf"), indent=2)[:500])

    print("\n--- read_file: DOCX ---")
    print(json.dumps(read_file("resumes/alice_jones.docx"), indent=2)[:500])

    print("\n--- read_file: missing file ---")
    print(json.dumps(read_file("resumes/ghost.pdf"), indent=2))

    print("\n--- read_file: unsupported format ---")
    print(json.dumps(read_file("resumes/test.xyz"), indent=2))

    print("\n--- list_files: all ---")
    result = list_files("resumes")
    print(f"Total: {len(result)} files")
    for f in result:
        print(f"  {f['filename']} ({f['size_bytes']} bytes)")

    print("\n--- list_files: .pdf only ---")
    result = list_files("resumes", extension=".pdf")
    print(f"PDF files: {[f['filename'] for f in result]}")

    print("\n--- list_files: invalid directory ---")
    print(json.dumps(list_files("nonexistent_xyz"), indent=2))

    print("\n--- write_file ---")
    print(json.dumps(write_file("outputs/test_output.txt", "Hello from fs_tools!"), indent=2))

    print("\n--- search_in_file: Python in emily_chen.txt ---")
    r = search_in_file("resumes/emily_chen.txt", "Python")
    print(f"Match count: {r['match_count']}")
    for m in r["matches"][:3]:
        print(f"  Line {m['line_number']}: {m['context'][:80]}")

    print("\n--- search_in_file: no matches ---")
    r2 = search_in_file("resumes/carol_white.txt", "xyz_no_match")
    print(f"Match count: {r2['match_count']}, matches: {r2['matches']}")

    print("\n--- search_in_file: missing file ---")
    print(json.dumps(search_in_file("resumes/ghost.txt", "Python"), indent=2))
