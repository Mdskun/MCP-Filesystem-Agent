# 🚀 MCP Filesystem Agent v3

**Token-Optimized File Management for AI Models**

A production-ready [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server enabling Claude and other LLMs to perform intelligent file operations with minimal token usage. Built for efficiency, security, and ease of use.

<div align="center">

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style: Black](https://img.shields.io/badge/Code%20style-Black-000000.svg)](https://github.com/psf/black)
[![MCP Protocol](https://img.shields.io/badge/MCP-v0.4.0+-purple)](https://modelcontextprotocol.io/)

**[Quick Start](#quick-start)** • **[Features](#features)** • **[Installation](#installation)** • **[Usage](#usage)** • **[Deployment](#deployment)**

</div>

---

## ✨ Features

### 🎯 Core Capabilities
- **25+ File Operations** - Read, write, edit, search, analyze
- **Token-Optimized** - Designed for minimal token usage with LLMs
- **Chunked Reading** - Handle files larger than context window with proper pagination
- **Smart Searching** - Content search, filename search, regex patterns, code structure analysis
- **Code Intelligence** - AST-based analysis for Python (extensible to other languages)
- **Safe Operations** - Dry-run mode for dangerous modifications, path validation, symlink safety

### 🤖 LLM-Friendly Design
- **Standardized Responses** - All tools return consistent `Dict` structure
- **Clear Descriptions** - Every tool optimized for LLM understanding
- **Error Handling** - Informative error messages guide LLM behavior
- **Context Awareness** - Tools provide metadata (file size, line count, progress) for informed decisions
- **Rate Limiting** - Prevents token waste with configurable limits

### 🔒 Security
- **Path Validation** - Prevents directory traversal attacks (../../etc/passwd)
- **Symlink Safety** - Resolves symlinks securely within BASE_DIR
- **Binary Detection** - Avoids reading binary files as text
- **Size Limits** - Prevents memory overload from accidental large file reads
- **Restricted Access** - All operations confined to BASE_DIR

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Features in Detail](#features-in-detail)
- [Tool Reference](#tool-reference)
- [Usage Examples](#usage-examples)
- [LLM Integration](#llm-integration)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## 🚀 Quick Start

### 1️⃣ Install

```bash
pip install -r requirements.txt
```

### 2️⃣ Configure Base Directory

```bash
export MCP_BASE_DIR="/path/to/your/projects"
# or on Windows:
# set MCP_BASE_DIR=C:\Users\YourName\Projects
```

### 3️⃣ Run Server

```bash
python server_v3.py
```

### 4️⃣ Connect to Claude

In Claude.ai Settings → Developer → Add MCP Server:
- **Name:** `filesystem-agent`
- **Script path:** `/full/path/to/server_v3.py`
- **Environment:** `MCP_BASE_DIR=/your/base/dir`

✅ **Done!** All file tools now available in Claude.

---

## 📦 Installation

### Requirements
- Python 3.8+
- pip

### Steps

```bash
# Clone or download the repository
cd mcp-fs-agent

# Install dependencies
pip install -r requirements.txt

# Set your base directory (optional, defaults to ~/Data/Repos)
export MCP_BASE_DIR="$HOME/projects"

# Start the server
python server_v3.py
```

### Verify Installation

```bash
$ python server_v3.py
==============================================================================
🚀 TOKEN-OPTIMIZED MCP FILESYSTEM AGENT v3 (PRODUCTION-READY)
==============================================================================
📁 BASE_DIR: /home/user/projects
✨ Features:
  ✅ 25+ file operations (read, write, search, edit)
  ✅ Standardized Dict return types (LLM-friendly)
  ✅ Proper chunked reading with pagination
  ...
📚 Ready to use with Claude.ai or any MCP-compatible LLM
==============================================================================
```

---

## 🎯 Features in Detail

### 📂 Directory Operations
**Why LLMs Need This:** Navigate projects, understand structure without loading full files

- `list_directory()` - List files with metadata (size, type)
- `get_tree()` - Compact directory tree (configurable depth)
- `create_directory()` - Create folders recursively

**LLM Benefit:** Get full project overview in one token-efficient call

### 📄 Smart File Reading
**Why LLMs Need This:** Handle files larger than context window, preview before full read

- `read_file()` - Full read OR preview-only (first N lines)
- `read_file_chunked()` - **NEW v3**: Proper pagination for huge files
  - Specify `chunk_index` to jump to any position
  - Returns progress (e.g., "3/100 chunks")
  - Never loads entire file into memory
- `batch_read_files()` - Read multiple files in one call
- `file_summary()` - Get file info without reading (ultra-token-efficient)

**LLM Benefit:** `preview_lines=50` = 50 lines read instead of 1000 = 95% token savings

### 🔧 Safe File Editing
**Why LLMs Need This:** Modify files safely with preview before commit

- `write_file()` - Create/overwrite
- `append_file()` - Add to end
- `replace_text()` - **NEW v3**: `dry_run=True` shows changes first
- `insert_at_line()` - Insert at specific line
- `delete_lines()` - Delete range

**LLM Benefit:** `dry_run=True` prevents accidental file corruption

### 🔍 Intelligent Search
**Why LLMs Need This:** Find what you need without scanning entire codebase

- `search_files()` - Find by filename
- `search_files_by_ext()` - Find by type (.py, .txt, etc)
- `search_content()` - **NEW v3**: Supports regex patterns + context around matches
- `search_code_structure()` - **NEW v3**: Functions, classes, imports with line numbers

**LLM Benefit:** Regex pattern `^def .*_handler` finds all handlers instantly vs scanning entire code

### 🐍 Code Intelligence
**Why LLMs Need This:** Understand code structure without reading files

- Python AST parsing for functions, classes, imports
- Returns signatures and metadata
- **Extensible** to JavaScript, Go, Rust, etc. (see below)

**LLM Benefit:** "Show me all functions that start with 'handle'" = instant code map

---

## 🛠️ Tool Reference

### Quick Lookup Table

| Category | Tool | Use When | LLM Efficiency |
|----------|------|----------|--------|
| **Read** | `read_file()` | Need full file content | 💚 Good with `preview_lines` |
| **Read** | `read_file_chunked()` | File > 2MB | 💚 Excellent (pagination) |
| **Read** | `batch_read_files()` | Need multiple files | 💚 Good (one call vs many) |
| **Info** | `file_summary()` | Need size/lines only | 💛 Best (no content read) |
| **Write** | `write_file()` | Create/overwrite | 💚 Safe |
| **Edit** | `replace_text()` | Find & replace | 💚 Good with `dry_run` |
| **Search** | `search_files()` | Find by name | 💛 Best (simple substring) |
| **Search** | `search_content()` | Find by content | 💚 Good with limits |
| **Code** | `search_code_structure()` | Find functions/classes | 💛 Best (AST, not text) |

### Complete Tools List

#### Basic
```python
ping() -> Dict
get_base_dir() -> Dict
```

#### Directory Operations
```python
list_directory(path: str = ".") -> Dict
get_tree(path: str = ".", max_depth: int = 2) -> Dict
create_directory(path: str) -> Dict
```

#### File Reading
```python
read_file(path: str, preview_lines: int = 0) -> Dict
read_file_chunked(path: str, chunk_index: int = 0, chunk_size_kb: int = 50) -> Dict
batch_read_files(paths: List[str]) -> Dict
file_summary(path: str) -> Dict
```

#### File Writing
```python
write_file(path: str, content: str) -> Dict
append_file(path: str, content: str) -> Dict
```

#### File Editing
```python
replace_text(path: str, old_text: str, new_text: str, count: int = -1, dry_run: bool = False) -> Dict
insert_at_line(path: str, line_number: int, text: str) -> Dict
delete_lines(path: str, start_line: int, end_line: int) -> Dict
```

#### Search
```python
search_files(query: str, path: str = ".", max_results: int = 20) -> Dict
search_content(query: str, path: str = ".", max_results: int = 15,
               extensions: List[str] = None, use_regex: bool = False) -> Dict
search_files_by_ext(extension: str, path: str = ".", max_results: int = 30) -> Dict
```

#### Code Analysis
```python
search_code_structure(path: str = ".", search_type: str = "functions", max_results: int = 25) -> Dict
```

---

## 💡 Usage Examples

### Example 1: Preview Before Full Read (Token-Efficient)
```
User: Read the first 50 lines of app/main.py

Claude uses: read_file(path="app/main.py", preview_lines=50)

Response:
{
  "status": "success",
  "action": "read_file",
  "mode": "preview",
  "preview_lines": 50,
  "total_lines": 450,
  "content": "#!/usr/bin/env python3\n..."
}

✅ Only 50 lines loaded, not 450!
```

### Example 2: Large File with Pagination
```
User: My app.log is huge. Read it in chunks starting from the beginning.

Claude uses: read_file_chunked(
    path="logs/app.log",
    chunk_index=0,
    chunk_size_kb=100
)

Response:
{
  "status": "success",
  "chunk_index": 0,
  "total_chunks": 25,
  "progress": "1/25",
  "file_size": "2.5MB",
  "content": "2024-01-15 10:00:00 INFO ...\n..."
}

✅ Can request chunk 5, 10, 20, etc without reloading!
```

### Example 3: Safe Replace with Dry-Run
```
User: Change all "console.log" to "logger.debug" in src/util.js - but show me first!

Claude uses: replace_text(
    path="src/util.js",
    old_text="console.log",
    new_text="logger.debug",
    dry_run=True
)

Response:
{
  "status": "success",
  "mode": "dry_run",
  "would_replace": 12,
  "preview": "const logger = require('./logger');\nlogger.debug('Debug message');\n...",
  "ready_to_commit": true
}

User: Looks good, do it!

Claude uses: replace_text(..., dry_run=False)

✅ No surprises, changes committed safely!
```

### Example 4: Code Structure Analysis
```
User: Show me all functions in the project

Claude uses: search_code_structure(search_type="functions", max_results=30)

Response:
{
  "status": "success",
  "found": 8,
  "results": [
    {
      "type": "function",
      "name": "handle_request",
      "file": "app/handlers.py",
      "line": 45,
      "signature": "def handle_request(req, resp)",
      "args": 2
    },
    ...
  ]
}

✅ Understand entire codebase structure without reading any files!
```

### Example 5: Regex Search
```
User: Find all TODO comments in Python files

Claude uses: search_content(
    query=r"#\s*TODO",
    extensions=[".py"],
    use_regex=True
)

Response:
{
  "status": "success",
  "found": 5,
  "results": [
    {
      "file": "app/main.py",
      "line": 127,
      "match": "# TODO: Refactor authentication logic"
    },
    ...
  ]
}

✅ Powerful pattern matching without manual code review!
```

---

## 🤖 LLM Integration

### With Claude.ai

1. Go to **Settings** → **Developer** → **Add MCP Server**
2. Fill in:
   - **Name:** `filesystem-agent`
   - **Script command:** `python /path/to/server_v3.py`
   - **Environment variables:**
     ```
     MCP_BASE_DIR=/home/user/projects
     ```
3. Click **Test Connection** (server must be running)
4. Use in any chat!

### Example Claude Conversation
```
User: Analyze my Flask app's structure

Claude: I'll examine your Flask app...
[Uses search_code_structure to find routes, models, handlers]
[Uses file_summary to check file sizes]
[Uses read_file with preview_lines on key files]

Here's what I found:
- 3 route handlers in app/routes.py
- 2 database models in app/models.py
- Configuration in config.py (45 lines)
...
```

### Response Format All LLMs Understand
Every tool returns standardized Dict:
```python
{
    "status": "success|error|info",    # Always present
    "action": "tool_name",              # What was called
    "path": "relative/path",            # If applicable
    # ... tool-specific fields ...
}
```

This makes LLMs reliable at:
- ✅ Checking if operation succeeded
- ✅ Understanding what was attempted
- ✅ Handling errors gracefully
- ✅ Chaining multiple operations

---

## ⚙️ Configuration

Edit `server_v3.py` to customize (all at the top):

```python
# Base directory (default: ~/Data/Repos, override with MCP_BASE_DIR env var)
BASE_DIR = Path(os.getenv("MCP_BASE_DIR", str(Path.home() / "Data/Repos"))).resolve()

# Token optimization settings
MAX_FILE_SIZE_KB = 2000          # Max single file (2MB)
MAX_RESULTS = 50                 # Max search results
DEFAULT_CHUNK_SIZE_KB = 50       # Chunk size for large files
TOTAL_BATCH_SIZE_KB = 5000       # Max total for batch_read_files (5MB)
CONTEXT_WIDTH = 80               # Chars around search match
MAX_LINES_TO_SEARCH = 10000      # Stop after this many lines

# Ignore directories
IGNORE_DIRS = {".git", "node_modules", "__pycache__", "venv", ...}

# Ignore binary files
BINARY_EXTENSIONS = {".exe", ".pdf", ".zip", ".so", ...}
```

---

## 🚢 Deployment

### Development (Local Machine)
```bash
export MCP_BASE_DIR="$HOME/projects"
python server_v3.py
# Leave running, connect from Claude
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server_v3.py .
ENV MCP_BASE_DIR=/workspace
CMD ["python", "server_v3.py"]
```

Build & run:
```bash
docker build -t mcp-fs-agent .
docker run -e MCP_BASE_DIR=/projects -v ~/projects:/projects mcp-fs-agent
```

### Linux Systemd Service
Create `/etc/systemd/system/mcp-fs.service`:
```ini
[Unit]
Description=MCP Filesystem Agent
After=network.target

[Service]
Type=simple
User=yourusername
Environment="MCP_BASE_DIR=/home/yourusername/projects"
ExecStart=/usr/bin/python3 /home/yourusername/server_v3.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable & start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-fs
sudo systemctl start mcp-fs
sudo systemctl status mcp-fs
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Access denied: Path outside base directory"** | Set `MCP_BASE_DIR` correctly: `export MCP_BASE_DIR="/your/path"` |
| **"File too large" error** | Use `read_file_chunked()` for files > 2MB |
| **Tools not showing in Claude** | Restart Claude/reload page; ensure server is running |
| **Server won't start** | Check Python 3.8+, install requirements: `pip install -r requirements.txt` |
| **Can't find file** | Verify file is under `BASE_DIR`; check path is relative to base |

---

## 🔒 Security

### Path Validation
```python
# ✅ These work (within BASE_DIR)
"/projects/my_app/main.py"
"./src/app.py"
"config/settings.json"

# ❌ These are blocked (outside BASE_DIR)
"../../etc/passwd"
"/etc/passwd"
"/home/other_user/file.txt"
```

### Symlink Safety
```python
# Symlinks are resolved and validated
# Even if they point outside BASE_DIR, they're rejected
```

### Binary File Protection
```python
# Automatically skipped for:
.exe, .dll, .so, .pdf, .zip, .jpg, .png, etc.
# Prevents text decode errors and token waste
```

---

## 📊 Performance Tips

### For Large Projects
```python
# ✅ Good: Narrow down with file type first
search_files_by_ext(".py")

# ✅ Good: Limit search scope
search_content(query="TODO", extensions=[".py", ".txt"])

# ✅ Good: Preview first, full read later
read_file(path="large_file.py", preview_lines=50)
```

### For Huge Files (500MB+)
```python
# ✅ Only way to handle huge files
read_file_chunked(path="huge.log", chunk_index=0, chunk_size_kb=500)

# ❌ Never use read_file() on huge files
```

### For Complex Searches
```python
# ✅ Use regex for complex patterns
search_content(query=r"def [a-z_]+_handler", use_regex=True)

# ✅ Limit max_results to avoid token waste
search_content(query="import", max_results=10)
```

---

## 🆕 What's New in v3

| Feature | v2 | v3 |
|---------|:--:|:--:|
| Standardized return types | ❌ | ✅ |
| Chunked reading with pagination | ❌ | ✅ |
| Dry-run mode for edits | ❌ | ✅ |
| Regex search support | ❌ | ✅ |
| Multi-language code analysis | ❌ | ✅ (Python + extensible) |
| Better tool descriptions | ⚠️ | ✅ |
| Token optimization | ✅ | ✅ |
| Code structure analysis | ✅ | ✅ |
| Path security | ✅ | ✅ |

---

## 🧪 Testing

Run with a sample project:
```bash
# Create test directory
mkdir -p ~/test_mcp/{src,tests}
echo "def hello(): pass" > ~/test_mcp/src/app.py

# Set and run
export MCP_BASE_DIR="$HOME/test_mcp"
python server_v3.py

# In another terminal, test with Claude or manually:
curl -X POST http://localhost:8000/search_files \
  -H "Content-Type: application/json" \
  -d '{"query": ".py"}'
```

---

## 📝 Contributing

Want to add support for JavaScript, Go, or Rust code analysis?

1. Edit `search_code_structure()` in `server_v3.py`
2. Add language detection and parsing
3. Return same format as Python results

Example for JavaScript:
```python
# Add to imports
import re

# Add to search_code_structure() function
elif file.endswith(".js"):
    # Use regex to find function definitions
    matches = re.findall(r'(?:function|const|async)\s+(\w+)', content)
    # Convert to same format as Python
```

---

## 📄 License

MIT License - Free to use, modify, and distribute.

See [LICENSE](LICENSE) file for details.

---

## 🎓 About

Built as a modern file management interface for AI models, emphasizing:
- **Token Efficiency** - Every API choice minimizes token usage
- **LLM Friendliness** - Standardized responses, clear semantics
- **Safety First** - Path validation, size limits, dry-run modes
- **Developer Experience** - Clear docs, easy integration, extensible code

---

## 🤝 Support

- 📖 Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed setup
- 🐛 See [Troubleshooting](#troubleshooting) section above
- 💬 Open an issue for bugs or feature requests
- ⭐ Star this repo if it helps you!

---

<div align="center">

**Made with ❤️ for AI developers**

*Transform how AI manages your files*

</div>