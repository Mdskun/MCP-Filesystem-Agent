<div align="center">

# 🗂️ MCP Filesystem Agent

### Token-efficient filesystem access for Claude — read, write, search, and analyze code without burning your context window

<p align="center">
  <img src="FileAgent.png" alt="MCP Filesystem Agent" width="140" />
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENCE)
[![Version](https://img.shields.io/badge/version-3.1.1-blue.svg)](CHANGELOG.md)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![MCPB](https://img.shields.io/badge/packaging-MCPB%200.3-6f42c1.svg)](manifest.json)
[![GitHub stars](https://img.shields.io/github/stars/Mdskun/mcp-fs-agent?style=social)](https://github.com/Mdskun/mcp-fs-agent/stargazers)

**[Quick Start](#-quick-start) · [Features](#-features) · [Configuration](#-configuration) · [Tech Stack](#-tech-stack) · [Contributing](#-contributing)**

</div>

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Demo](#-demo)
- [Tech Stack](#-tech-stack)
- [Requirements](#-requirements)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Packaging as a Desktop Extension](#-packaging-as-a-desktop-extension)
- [How It Works](#-how-it-works)
- [Project Structure](#-project-structure)
- [Documentation](#-documentation)
- [Security & Privacy](#-security--privacy)
- [Contributing](#-contributing)
- [License](#-license)
- [Author](#-author)

---

## 🔭 Overview

Every time an LLM reads a whole file just to answer a small question, it burns thousands of tokens it didn't need. **MCP Filesystem Agent** is a [Model Context Protocol](https://modelcontextprotocol.io) server that gives Claude 22 purpose-built file operations — preview reads, chunked pagination, AST-based code search, dry-run edits — so it gets exactly the context it needs and nothing more.

**The problem:** naive "read the whole file" tool-use patterns don't scale past a few hundred lines before they eat your context budget.

**The solution:** structured, scoped operations — `read_file(preview_lines=50)` instead of dumping 2,000 lines; `search_code_structure()` instead of reading five files to find one function; `replace_text(dry_run=True)` so edits are previewed before they're committed.

**Who it's for:** developers who want Claude to work directly across a real codebase or document tree — through Claude Desktop, Claude Code, or any MCP-compatible client — without babysitting what gets read.

---

## ✨ Features

- 🎯 **Scoped by design** — access is limited to directories you explicitly allow, passed as CLI arguments exactly like the official filesystem MCP server. Nothing outside that scope is reachable.
- ⚡ **Preview & chunked reads** — pull the first N lines or a specific byte-range chunk instead of an entire file, so large files don't blow the context window.
- 🔍 **Multi-language code intelligence** — AST-accurate function/class/import extraction for Python, regex-based for JavaScript, Go, and Rust.
- ✏️ **Dry-run edits** — preview a find-and-replace before committing it, so you see the diff before anything changes on disk.
- 🧭 **Fast search, not full reads** — search by filename, extension, or content (plain text or regex) with contextual snippets instead of whole-file dumps.
- 📦 **Batch reads with size guards** — read multiple related files in one call, capped so a batch can't quietly consume your whole budget.
- 🐳 **Production Docker setup** — non-root user, resource limits, a real process healthcheck (not a no-op).
- 🧪 **Actually tested** — path-safety, CLI-arg handling, and content search all have regression tests in `tests/`.

---

## 🖼️ Demo

<p align="center">
  <em>Once installed, Claude Desktop renders a native config screen generated directly from <code>manifest.json</code> — pick allowed directories, and tools are auto-grouped into "Read-only" vs. "Write/destructive" based on each tool's annotations.</em>
</p>

```
You: What's in my project, and does it have any TODOs left?

Claude uses: get_tree(path=".", max_depth=2)
             search_content(query="TODO")

Result: A directory tree plus every TODO with file and line number —
        without Claude reading a single full file.
```

---

## 🧱 Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3.8+** | Core implementation — a single, dependency-light module |
| **[MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)** (`FastMCP`) | Tool registration, annotations, and the stdio transport Claude speaks |
| **Pydantic** *(via `mcp`)* | Tool annotation schema (`ToolAnnotations`) |
| **`ast` (stdlib)** | 100%-accurate Python function/class/import extraction |
| **`re` (stdlib)** | Regex-based structure extraction for JS/Go/Rust, and regex search mode |
| **Docker** | Optional containerized deployment, non-root, healthchecked |
| **MCPB** (`manifest_version 0.3`) | Packaging format for Claude Desktop's Extensions / Connectors Directory |
| **pytest** | Regression tests for path safety, CLI config, and content search |

---

## 📋 Requirements

| | |
|---|---|
| **OS** | Linux, macOS, Windows |
| **Python** | 3.8 or newer |
| **RAM** | ~50MB base |
| **Network** | None — fully local, no outbound calls |
| **Docker** *(optional)* | 20.10+ with Compose 1.29+ |

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/Mdskun/mcp-fs-agent.git
cd mcp-fs-agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run — pass the directory Claude should access as an argument
python server3.py /path/to/your/projects
```

You should see:
```
============================================================
🚀 MCP FILESYSTEM AGENT v3 (PRODUCTION-READY)
============================================================
📁 BASE DIRECTORIES (1):
   1. /path/to/your/projects
============================================================
```

### Connect it to Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "filesystem-agent": {
      "command": "python",
      "args": ["/path/to/mcp-fs-agent/server3.py", "/path/to/your/projects"]
    }
  }
}
```

Restart Claude Desktop. Add more allowed directories by listing more paths in `args` — one server, multiple scoped roots.

### Run it in Docker instead

```bash
docker-compose up -d
docker-compose logs -f     # watch it start
docker-compose down        # stop it
```

### Prefer a system service?

<details>
<summary><strong>Linux (systemd)</strong></summary>

```ini
# /etc/systemd/system/mcp-fs-agent.service
[Unit]
Description=MCP Filesystem Agent
After=network.target

[Service]
Type=simple
User=your-username
Environment="MCP_BASE_DIR=/home/your-username/projects"
ExecStart=/home/your-username/mcp-fs-agent/venv/bin/python /home/your-username/mcp-fs-agent/server3.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mcp-fs-agent
```
</details>

<details>
<summary><strong>Windows (nssm)</strong></summary>

```cmd
nssm install mcp-fs-agent "C:\path\to\venv\Scripts\python.exe" "C:\path\to\server3.py" "C:\Users\YourName\Projects"
nssm start mcp-fs-agent
```
</details>

<details>
<summary><strong>Troubleshooting</strong></summary>

| Symptom | Fix |
|---|---|
| `No module named 'mcp'` | `pip install -r requirements.txt` |
| `Access denied: Path outside allowed directories` | Double-check the path passed as a CLI arg or `MCP_BASE_DIR` |
| Claude doesn't see the server | Fully quit and reopen Claude Desktop (a reload isn't enough) |
| Out of memory on a huge file | Use `read_file_chunked()` instead of `read_file()` |
</details>

---

## ⚙️ Configuration

### Simplest: command-line arguments (recommended)

```bash
python server3.py /path/to/projects
python server3.py /path/to/projects /path/to/documents /data/external   # multiple roots
```

### Alternative: environment variables

| Variable | Default | Description |
|---|---|---|
| `MCP_BASE_DIR` | `~/Data/Repos` | Single allowed directory |
| `MCP_BASE_DIRS` | *(not set)* | Comma-separated list of allowed directories |
| `PYTHONUNBUFFERED` | `1` | Unbuffered stderr output (recommended) |

Priority order: **CLI args → `MCP_BASE_DIRS` → `MCP_BASE_DIR` → default.**

### Tunable limits

Edit near the top of `server3.py`:

```python
MAX_FILE_SIZE_KB   = 2000   # single-file read/write cap (2MB)
MAX_RESULTS        = 50     # max search results returned
DEFAULT_CHUNK_SIZE_KB = 50  # chunk size for read_file_chunked()
TOTAL_BATCH_SIZE_KB = 5000  # cap for batch_read_files()
MAX_LINES_TO_SEARCH = 10000 # cap for search_content()
```

---

## 📦 Packaging as a Desktop Extension

The repo ships `manifest.json` (MCPB spec `0.3`) so it can be packaged as a `.mcpb` bundle and installed as a Claude Desktop extension — this is what renders the native "Allowed Directories" config screen.

```bash
# 1. Bundle the mcp dependency using the *exact* interpreter that will run it
/usr/bin/python3 -m pip install "mcp>=1.9,<2" --target=server/lib

# 2. Install the MCPB CLI
npm install -g @anthropic-ai/mcpb

# 3. Validate, then pack
mcpb validate manifest.json
mcpb pack .
```

> **Interpreter mismatch is the #1 failure mode.** `pydantic_core` ships a compiled binary — if you `pip install --target=server/lib` from a venv or conda environment that isn't the exact Python Claude Desktop launches (usually `/usr/bin/python3`), you'll get `ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'` at runtime. Always install with the target interpreter itself (`/usr/bin/python3 -m pip install ...`, not a bare `pip install ...`).

Install the resulting `.mcpb` in Claude Desktop, test it against a disposable directory first, then submit via the Desktop Extension form (a separate path from the Connectors Directory portal, which is for remote HTTPS servers only).

---

## 🧠 How It Works

**User flow:**
1. You point the server at one or more directories (CLI args, env var, or the Desktop Extension's directory picker).
2. Claude calls a tool — say, `search_content(query="TODO")`.
3. Every path is resolved and checked against the allowed directories before any file touches disk.
4. A compact, structured `ToolResponse` comes back — not a raw file dump.

**Internally:**

```
Claude ──▶ FastMCP tool call ──▶ safe_path() validation ──▶ file operation ──▶ ToolResponse
                                       │
                                       └─ segment-aware check via Path.relative_to()
                                          (rejects sibling-directory & ../ traversal)
```

There's no framework pattern here beyond "one function per tool" — it's a single, flat module by design, prioritizing readability over abstraction for a project this size.

---

## 📁 Project Structure

```
mcp-fs-agent/
├── server3.py              # The entire server — all 22 tools, one file
├── manifest.json           # MCPB packaging manifest (Desktop Extension config)
├── requirements.txt        # Runtime dependency (mcp SDK)
├── .mcpbignore             # Excludes venv/tests/docs from the packed bundle
├── Dockerfile              # Non-root, healthchecked container build
├── docker-compose.yml      # One-command Docker deployment
├── PRIVACY.md              # Data-handling policy (required for submission)
├── SECURITY.md             # Security features, known limitations, disclosure process
├── CHANGELOG.md            # Version history, including real fixes (not just features)
├── CONTRIBUTING.md         # Dev setup, tool template, PR process
└── tests/
    ├── test_safe_path.py       # Path-traversal regression tests
    ├── test_cli_args.py        # CLI-arg config priority tests
    └── test_search_content.py  # Content-search matching regression tests
```

---

## 📚 Documentation

- 📝 **[CHANGELOG.md](CHANGELOG.md)** — every version, including the real bugs that got fixed (a string-prefix path check, a broken match object in search) — not just a feature list.
- 🔒 **[SECURITY.md](SECURITY.md)** — security model, Docker hardening, and how to report a vulnerability.
- 🔐 **[PRIVACY.md](PRIVACY.md)** — what data this touches (nothing leaves your machine).
- 🤝 **[CONTRIBUTING.md](CONTRIBUTING.md)** — dev setup, the required tool-annotation pattern, commit conventions.

---

## 🔒 Security & Privacy

- **Path validation** is segment-aware (`Path.relative_to()`), not a naive string-prefix check — sibling directories that share a name prefix with an allowed folder can't be reached.
- **Zero network calls.** No telemetry, no analytics, nothing sent anywhere. See [PRIVACY.md](PRIVACY.md) for the full policy.
- **Every tool is annotated** (`readOnlyHint` / `destructiveHint`) so Claude Desktop can correctly group and gate write/destructive operations from read-only ones.

Full details in [SECURITY.md](SECURITY.md).

---

## 🤝 Contributing

Contributions are welcome — especially test coverage for the write/edit tools, which is the biggest known gap right now.

```bash
git checkout -b feature/your-feature-name
# make changes, add tests
pytest tests/ -v
```

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for the full dev setup, the required tool-annotation pattern for new tools, and PR conventions.

---

## 📄 License

Released under the **[MIT License](LICENCE)** — use it, modify it, ship it.

---

## 👤 Author

**Manthan** ([@Mdskun](https://github.com/Mdskun))

If this saved you a context window or two, a ⭐ on the repo is the easiest way to say thanks.

<div align="center">

**[⬆ Back to top](#-mcp-filesystem-agent)**

</div>
