# LLM-Powered File System Assistant: Technical Specifications

This document outlines the technical stack chosen for the **LLM-Powered File System Assistant** and explains the engineering rationale behind each component.

---

## 🏛️ System Architecture Overview

The system is built using a highly decoupled, layered architecture to ensure modularity, ease of testing, and reliability:

1. **User Interface Layer:** An interactive Command-Line Interface (CLI) chat shell.
2. **Orchestration Layer (`llm_file_assistant.py`):** The LLM reasoning engine that manages memory, registries, and the ReAct (Reasoning + Acting) execution loop.
3. **Service Layer (`fs_tools.py`):** Deterministic, pure-Python file system utilities. This layer is entirely independent of the LLM.
4. **Infrastructure Layer:** The local filesystem and configuration system (.env).

---

## 🛠️ Technology Stack & Rationale

| Component | Technology Selected | Rationale for Selection |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Standard for AI development. Supports modern syntax, static typing annotations (`typing.Optional`, etc.), and native filesystem utilities (`pathlib`). |
| **LLM Inference Engine** | Groq API Client | Provides ultra-fast inference speed, lowering user response latency. It features native compatibility with the OpenAI SDK structure. |
| **Large Language Model** | `openai/gpt-oss-120b` | Selected for robust reasoning, accurate tool call generation, and compliant system-prompt steering (out-of-scope query filtering). |
| **Configuration** | `python-dotenv` | Standard security practice. Keeps sensitive API keys (`GROQ_API_KEY`) and variable system paths out of the codebase. |
| **PDF Extraction** | `pypdf` | A lightweight, pure-Python library for reading and extracting plain text from multi-page PDF files without external binary dependencies. |
| **DOCX Extraction** | `python-docx` | Robust, standard package for parsing Microsoft Word (`.docx`) file properties and iterating over text paragraphs reliably. |
| **Sample Generation** | `fpdf2` | Used strictly in developer scripts to programmatically create sample resumes with varying metadata sizes and text contents. |

---

## ⚙️ Engineering Decisions for Reliability

* **Decoupled Service Boundary:** The tools in `fs_tools.py` never raise raw exceptions. If a filesystem operation fails (e.g., file not found, permission error), it returns a structured error dictionary (`{"status": "error", "error_code": "...", "message": "..."}`). The orchestration layer translates these payloads into user-friendly responses, ensuring system stability.
* **OpenAI-Compatible Tool Schema:** Switched tool schemas to standard JSON Schema declarations. Added `anyOf: [string, null]` for optional parameters (e.g., extension filters) to guarantee compliance with the strict parameter validators of Groq/OpenAI endpoints.
* **Automatic Backoff & Rate-Limit Handling:** Integrates a regex-driven retry handler. When rate limit errors (`429 RESOURCE_EXHAUSTED`) are encountered, it parses the server-recommended wait time (e.g., `Please retry in X seconds`) and sleeps automatically before retrying, minimizing API drops.
* **Out-of-Scope Safety Constraints:** The system prompt is engineered to reject general queries (e.g., general knowledge, creative writing) and explicitly enforce operational bounds within `resumes/` and `outputs/`.
