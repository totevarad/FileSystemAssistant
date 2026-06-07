"""
llm_file_assistant.py — LLM-Powered File System Assistant (Part B)

Connects the fs_tools.py service layer to Groq API via Tool Calling
(Function Calling), implementing a ReAct (Reasoning + Acting) agent loop
that handles complex, multi-step queries inside a styled Terminal Interface.

Usage:
    .\\venv\\Scripts\\python.exe llm_file_assistant.py
"""

import os
import sys
import json

# Force standard output to use UTF-8 to prevent encoding errors on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import time
import re
from dotenv import load_dotenv
from groq import Groq

# Rich styling library imports
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

import fs_tools


# ─────────────────────────────────────────────────────────────────────────────
# 1. Environment & Client Initialization
# ─────────────────────────────────────────────────────────────────────────────

load_dotenv()

GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
LLM_MODEL      = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
RESUMES_DIR    = os.getenv("RESUMES_DIR", "resumes")
OUTPUTS_DIR    = os.getenv("OUTPUTS_DIR", "outputs")

if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
    print(
        "\n[ERROR] GROQ_API_KEY is not set or still has the placeholder value.\n"
        "  1. Copy .env.example to .env\n"
        "  2. Paste your API key from https://console.groq.com/keys\n"
    )
    sys.exit(1)

client = Groq(api_key=GROQ_API_KEY)
console = Console()


# ─────────────────────────────────────────────────────────────────────────────
# 2. System Prompt
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""You are an intelligent File System Assistant. Your job is to help \
users manage and analyze resume files stored on the local filesystem.

## Available Tools
You have access to four tools:
1. list_files(directory, extension?) — List files in a directory, optionally filtered by extension.
2. read_file(filepath) — Read and extract the full text content from a PDF, DOCX, or TXT file.
3. search_in_file(filepath, keyword) — Case-insensitive keyword search inside a file.
4. write_file(filepath, content) — Write text content to a file (auto-creates parent directories).

## Operational Boundaries
- Resume files are stored in: `{RESUMES_DIR}/`
- All generated output files must be saved in: `{OUTPUTS_DIR}/`
- Never fabricate or guess file contents. Always use read_file() to get actual content.
- Never assume a file exists without verifying via list_files() or read_file() first.

## Output File Naming Convention
When generating summaries or output files for a source file named `<name>.<ext>`:
- First output   →  `{OUTPUTS_DIR}/<name>_output.txt`
- Second output  →  `{OUTPUTS_DIR}/<name>_output_v1.txt`
- Third output   →  `{OUTPUTS_DIR}/<name>_output_v2.txt`
Before writing, check `{OUTPUTS_DIR}/` with list_files() to determine the correct version.

## Multi-Step Query Strategy
For compound queries (e.g., "find Python resumes and summarize each"):
1. Call list_files() to discover all available files.
2. Call search_in_file() or read_file() on each relevant file.
3. Synthesize results, then call write_file() if output is requested.
4. Always tell the user exactly what actions you took.

## Handling Out-of-Scope Queries
- You must ONLY answer questions and perform tasks related to local resume file management, scanning, reading, searching, summarizing, and writing outputs within the configured resumes/outputs folders.
- If a user asks a general question, creative writing question, or any query unrelated to these topics (e.g., "what is the capital of India", "write a poem", "help me code a website"), you MUST politely refuse to answer.
- Your refusal response must explicitly state that you are a File System Assistant specialized in resume management and file-system tasks. Politely explain what you can do (e.g., list files, read contents, search keywords, summarize resumes, write outputs) and state that general knowledge or unrelated questions are out of scope.

## Response Formatting Constraints
1. **read_file Output:** When presenting the contents or details of a file read via `read_file`, your response MUST follow this structure:
   - Do NOT display, print, or repeat the metadata JSON block in your response, as the terminal already displays the Tool Result JSON containing the metadata.
   - Instead, print a clear label or header like "**File Content:**" (or similar), and then directly display the extracted content of the file in its raw, properly structured text format with clear spacing, line breaks, and layout.
   - Do NOT wrap the file content inside JSON or markdown code blocks (unless it is a code file). This prevents double printing and ensures the terminal output is clean, readable, and free of any duplicate prints.
2. **search_in_file Output:** When presenting search results from `search_in_file`, you MUST NEVER use markdown tables. Tables are strictly forbidden. Instead, group matches by file path and display them in a clean, hierarchical list structure:
   - Display each file on a new line with a file emoji and path (e.g., `### 📄 resumes/emily_chen.txt`).
   - List each match as a bullet point under the file header.
   - Display the line number in bold (e.g., `- **Line 12:**`) followed by the matching context.
   - Separate files with a blank line to ensure high readability.

## Error Handling
- If a tool returns status="error", translate it into a clear user-facing message.
- Suggest corrective actions (e.g., check spelling, confirm directory name).
- Never expose raw JSON error payloads directly to the user.
"""


# ─────────────────────────────────────────────────────────────────────────────
# 3. Tool Schema Registry
# ─────────────────────────────────────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Reads and extracts the full text content and metadata from a local "
                "resume file. Supports .pdf, .docx, and .txt formats."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "The absolute or relative path to the resume file.",
                    }
                },
                "required": ["filepath"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": (
                "Lists all files within a specified directory. Optionally filters "
                "results by file extension (e.g., '.pdf', '.docx', '.txt')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "The path of the directory to scan.",
                    },
                    "extension": {
                        "anyOf": [
                            {"type": "string"},
                            {"type": "null"}
                        ],
                        "description": (
                            "Optional extension filter including the leading dot "
                            "(e.g. '.pdf'). Omit to list all file types."
                        ),
                    },
                },
                "required": ["directory"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Writes text content to a specified file path. "
                "Automatically creates any missing parent directories."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "The target file path where content will be written.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The full text content to write into the file.",
                    },
                },
                "required": ["filepath", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_file",
            "description": (
                "Performs a case-insensitive keyword search within a file's text content. "
                "Returns all matching lines with their line numbers and full line context."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "The path to the target file to search within.",
                    },
                    "keyword": {
                        "type": "string",
                        "description": "The search term. Case-insensitive substring match.",
                    },
                },
                "required": ["filepath", "keyword"],
            },
        },
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# 4. Tool Dispatch Router
# ─────────────────────────────────────────────────────────────────────────────

TOOL_DISPATCH: dict = {
    "read_file":      fs_tools.read_file,
    "list_files":     fs_tools.list_files,
    "write_file":     fs_tools.write_file,
    "search_in_file": fs_tools.search_in_file,
}


# ─────────────────────────────────────────────────────────────────────────────
# 5. Helper Functions & ReAct Agent Loop
# ─────────────────────────────────────────────────────────────────────────────

def _print_tool_call(fn_name: str, fn_args: dict) -> None:
    """Pretty-print a tool invocation to the console."""
    args_str = ", ".join(
        f"[yellow]{k}[/yellow]={repr(v)[:60]}" for k, v in fn_args.items()
    )
    console.print(f"\n  [bold blue]🔧 Tool Call:[/bold blue] [green]{fn_name}[/green]({args_str})")


def _print_tool_result(result: dict | list) -> None:
    """Print the structured JSON result of a tool call."""
    console.print("         [bold green]↳ Tool Result JSON:[/bold green]")
    if isinstance(result, dict):
        printable = result.copy()
        if "content" in printable:
            # Remove content field for console logging to prevent double printing and unreadable dump
            printable.pop("content")
        console.print_json(data=printable)
    else:
        console.print_json(data=result)


def print_welcome_dashboard() -> None:
    """Print a beautiful startup interface dashboard in the terminal."""
    console.clear()
    title = Text("🤖 File System Assistant Terminal (Groq Engine)", style="bold cyan")
    
    # Config Table
    config_table = Table(title="Configuration Settings", show_header=True, header_style="bold magenta")
    config_table.add_column("Parameter", style="dim", width=25)
    config_table.add_column("Value", style="green")
    config_table.add_row("Model", LLM_MODEL)
    config_table.add_row("Resumes Directory", RESUMES_DIR)
    config_table.add_row("Outputs Directory", OUTPUTS_DIR)
    
    # Tools Table
    tools_table = Table(title="Available CLI Capabilities", show_header=True, header_style="bold blue")
    tools_table.add_column("Function Call", style="cyan")
    tools_table.add_column("Description", style="white")
    tools_table.add_row("list_files", "List resume files in the resumes/ directory.")
    tools_table.add_row("read_file", "Read text & metadata from PDF, DOCX, or TXT resumes.")
    tools_table.add_row("search_in_file", "Perform case-insensitive keyword searches on content.")
    tools_table.add_row("write_file", "Save resume summaries and updates to outputs/ folder.")
    
    inst_text = Text("\nType your query below. Type 'exit' or 'quit' to close the terminal.\n", style="yellow")
    
    console.print(Panel(title, border_style="cyan"))
    console.print(config_table)
    console.print(tools_table)
    console.print(inst_text)


def run_agent(user_message: str, history: list) -> str:
    """
    Execute one full ReAct (Reasoning + Acting) cycle for the given user message.

    Appends the user message to conversation history, then calls the Groq API
    in a loop. Each iteration either executes tool calls and feeds results back
    to the model, or returns the final text response when the model is done.

    Args:
        user_message (str): The natural language query from the user.
        history (list): Running conversation history (mutated in-place).

    Returns:
        str: The final natural language response from the LLM.
    """
    # Append system prompt if history is empty
    if not history:
        history.append({"role": "system", "content": SYSTEM_PROMPT})

    # Append user message to history
    history.append({"role": "user", "content": user_message})

    max_iterations = 15  # safety guard against infinite tool-call loops

    with console.status("[bold green]Thinking...[/bold green]", spinner="dots") as status:
        for iteration in range(1, max_iterations + 1):

            # ── Groq API call (with 429 Rate Limit retry) ──────────────────────
            retries = 3
            backoff = 2
            response = None
            for attempt in range(retries + 1):
                try:
                    response = client.chat.completions.create(
                        model=LLM_MODEL,
                        messages=history,
                        tools=TOOLS,
                        tool_choice="auto",
                        temperature=0.2,
                    )
                    break
                except Exception as e:
                    is_rate_limit = False
                    if hasattr(e, "status_code") and e.status_code == 429:
                        is_rate_limit = True
                    elif "429" in str(e) or "rate_limit" in str(e).lower() or "RESOURCE_EXHAUSTED" in str(e):
                        is_rate_limit = True
                    
                    if is_rate_limit and attempt < retries:
                        # Try to extract retry delay from API error message
                        match = re.search(r"retry in (\d+\.?\d*)s", str(e), re.IGNORECASE)
                        if match:
                            sleep_time = float(match.group(1)) + 1.0
                        else:
                            sleep_time = (backoff ** (attempt + 1)) * 5.0
                        status.update(f"[bold yellow]Rate limit hit. Retrying in {sleep_time:.1f}s...[/bold yellow]")
                        time.sleep(sleep_time)
                        status.update("[bold green]Thinking...[/bold green]")
                    else:
                        raise e

            # Extract assistant message
            assistant_message = response.choices[0].message
            
            # Append assistant response to history
            history.append(assistant_message)

            tool_calls = assistant_message.tool_calls

            # ── No tool calls → final answer ─────────────────────────────────────
            if not tool_calls:
                return assistant_message.content or "(No response generated.)"

            # ── Execute each tool call and collect responses ──────────────────────
            for tool_call in tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                # Temporarily suspend status spinner to print tool calls cleanly
                status.stop()
                _print_tool_call(fn_name, fn_args)

                # Dispatch to the registered Python function
                if fn_name in TOOL_DISPATCH:
                    try:
                        result = TOOL_DISPATCH[fn_name](**fn_args)
                    except Exception as exc:
                        result = {
                            "status": "error",
                            "error_code": "DISPATCH_ERROR",
                            "message": f"Unexpected error executing '{fn_name}': {exc}",
                        }
                else:
                    result = {
                        "status": "error",
                        "error_code": "UNKNOWN_TOOL",
                        "message": f"No tool registered with name '{fn_name}'.",
                    }

                _print_tool_result(result)
                status.start()

                # Append tool result to history
                history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fn_name,
                    "content": json.dumps(result, default=str, ensure_ascii=False)
                })

    return (
        "[ERROR] The agent reached the maximum number of reasoning steps. "
        "Please try rephrasing your query."
    )


# ─────────────────────────────────────────────────────────────────────────────
# 6. CLI — Interactive Terminal Shell
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """
    Launch the interactive CLI session.

    Maintains a persistent conversation history across all turns so that the
    agent can refer back to prior context within the same session.
    """
    sys.stdout.reconfigure(encoding='utf-8')
    print_welcome_dashboard()

    # Persistent conversation history for the session
    history = []

    while True:
        # ── Read user input ──────────────────────────────────────────────────
        try:
            user_input = console.input("\n[bold cyan]You :[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n\n[bold yellow]Session ended. Goodbye![/bold yellow]")
            break

        # Skip empty input
        if not user_input:
            continue

        # Exit commands
        if user_input.lower() in ("exit", "quit", "bye", "q"):
            console.print("\n[bold yellow]Goodbye![/bold yellow]")
            break

        # ── Run agent and print response ─────────────────────────────────────
        console.print("\n[bold magenta]Assistant:[/bold magenta]", style="dim")
        try:
            answer = run_agent(user_input, history)
            console.print(answer)
        except Exception as exc:
            console.print(f"\n[bold red][ERROR] {type(exc).__name__}: {exc}[/bold red]")
            console.print("Please try again or type 'exit' to quit.")


if __name__ == "__main__":
    main()
