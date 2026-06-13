# 🚀 MCP Filesystem Agent v3 - Setup & Usage Guide

## What Is This?

An MCP (Model Context Protocol) server that enables **Claude and other LLMs** to perform file operations with **minimal token usage**. Perfect for:
- Reading, writing, editing files
- Searching code and content
- Analyzing Python code structure
- Large file handling with pagination
- Safe operations with dry-run mode

---

## ⚡ Quick Start (5 minutes)

### 1. Install Dependencies

```bash
pip install mcp fastapi uvicorn
```

Or use requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Set the Base Directory

Choose where the agent can access files:

```bash
# Option A: Use default (~/Data/Repos)
# - Just run the server

# Option B: Use custom directory
export MCP_BASE_DIR="/path/to/your/projects"
# Then run the server

# Option C: Windows
set MCP_BASE_DIR=C:\Users\YourName\Projects
# Then run the server
```

### 3. Start the Server

```bash
python server_v3.py
```

You should see:
```
==============================================================================
🚀 TOKEN-OPTIMIZED MCP FILESYSTEM AGENT v3 (PRODUCTION-READY)
==============================================================================
📁 BASE_DIR: /home/hp/Data/Repos
   Set MCP_BASE_DIR environment variable to change this

✨ Features:
  ✅ 25+ file operations (read, write, search, edit)
  ✅ Standardized Dict return types (LLM-friendly)
  ✅ Proper chunked reading with pagination
  ✅ Dry-run mode for dangerous operations
  ✅ Regex support in content search
  ✅ Code structure analysis (Python AST)
  ✅ Token-optimized for Claude & other LLMs

📚 Ready to use with Claude.ai or any MCP-compatible LLM
==============================================================================
```

**✅ Server is running and ready!**

---

## 📱 Using with Claude.ai

### Step 1: Configure in Claude Settings

1. Open Claude.ai → Settings → **Developer**
2. Click **"Add MCP Server"**
3. Fill in:
   - **Name:** `filesystem-agent`
   - **Script path:** `/path/to/server_v3.py`
   - **Environment variables:** `MCP_BASE_DIR=/your/base/dir`

### Step 2: Start a Chat

In any Claude chat, you now have access to all tools. Example:

> **You:** "Search for all Python files in the current project"
>
> **Claude:** I'll search for Python files...
> [Uses `search_files_by_ext` tool]

---

## 🛠️ Available Tools (v3 Improvements)

### Key Improvements in v3

✅ **Standardized Returns**: All tools return `Dict` with consistent structure:
```python
{
    "status": "success" | "error" | "info",
    "action": "tool_name",
    "path": "relative/path",  # if applicable
    ...other fields...
}
```

✅ **Proper Pagination**: `read_file_chunked()` now supports:
```python
chunk_index = 0  # Which chunk
chunk_size_kb = 50  # Size of each chunk
# Returns: {chunk_index, total_chunks, progress: "1/10", content}
```

✅ **Dry-Run Mode**: Dangerous operations like `replace_text()` can preview:
```python
replace_text(
    path="config.py",
    old_text="old_value",
    new_text="new_value",
    dry_run=True  # Preview only, don't modify!
)
```

✅ **Regex Search**: `search_content()` supports regex patterns:
```python
search_content(
    query="def .*_handler",  # Regex pattern
    use_regex=True  # Enable regex mode
)
```

### All Tools Reference

#### 📋 Basic & Info
- `ping()` - Health check
- `get_base_dir()` - Current base directory configuration

#### 📂 Directory Operations
- `list_directory(path)` - List files in directory with metadata
- `get_tree(path, max_depth)` - Directory tree structure
- `create_directory(path)` - Create folder

#### 📄 File Reading
- `read_file(path, preview_lines=0)` - Read full or preview first N lines
- `read_file_chunked(path, chunk_index=0, chunk_size_kb=50)` - Read large files in chunks with pagination
- `batch_read_files(paths)` - Read multiple files at once
- `file_summary(path)` - Get file info without reading content

#### ✏️ File Writing
- `write_file(path, content)` - Create or overwrite
- `append_file(path, content)` - Add to end of file

#### 🔧 File Editing
- `replace_text(path, old, new, dry_run=False)` - Find & replace with dry-run preview
- `insert_at_line(path, line_num, text)` - Insert at specific line
- `delete_lines(path, start, end)` - Delete line range

#### 🔍 Search
- `search_files(query, max_results=20)` - Find files by name
- `search_content(query, use_regex=False)` - Search file contents with context
- `search_files_by_ext(extension)` - Find files by type (.py, .txt, etc)

#### 🐍 Code Analysis (Python)
- `search_code_structure(search_type="functions")` - Find functions, classes, imports in Python files

---

## 💡 Usage Examples

### Example 1: Read a File with Preview (Token-Efficient)

```
You: Read the first 50 lines of config.py to see what's in it

Claude uses: read_file(path="config.py", preview_lines=50)
Response:
{
  "status": "success",
  "action": "read_file",
  "mode": "preview",
  "preview_lines": 50,
  "total_lines": 245,
  "content": "# Configuration file\n..."
}
```

✅ **Token Savings**: Only gets 50 lines instead of 245!

---

### Example 2: Read Large File with Pagination

```
You: I have a 5MB log file. Read the first chunk to see the format.

Claude uses: read_file_chunked(path="app.log", chunk_index=0, chunk_size_kb=50)
Response:
{
  "status": "success",
  "action": "read_file_chunked",
  "chunk_index": 0,
  "total_chunks": 100,
  "progress": "1/100",
  "file_size": "5.0MB",
  "content": "2024-01-15 10:23:45 ERROR...\n..."
}
```

✅ **Smart Pagination**: Can request chunk 50 next, or chunk 99, etc.

---

### Example 3: Safe Search & Replace with Dry-Run

```
You: Replace all "localhost" with "127.0.0.1" in config files, but show me first

Claude uses: replace_text(
    path="config.py",
    old_text="localhost",
    new_text="127.0.0.1",
    dry_run=True  # <-- SAFE MODE
)
Response:
{
  "status": "success",
  "action": "replace_text",
  "mode": "dry_run",
  "would_replace": 3,
  "preview": "# Configuration\nhost = 127.0.0.1\n...",
  "ready_to_commit": True
}

You: Looks good, make the actual changes

Claude uses: replace_text(same params, dry_run=False)  # Now commits
```

✅ **Safety First**: Preview before modifying!

---

### Example 4: Search with Regex

```
You: Find all function definitions in my Python code

Claude uses: search_content(
    query="^def ",
    extensions=[".py"],
    use_regex=True
)
Response:
{
  "status": "success",
  "action": "search_content",
  "found": 12,
  "results": [
    {
      "file": "app/main.py",
      "line": 45,
      "match": "def handle_request():"
    },
    ...
  ]
}
```

✅ **Powerful Search**: Regex for complex patterns!

---

### Example 5: Analyze Code Structure

```
You: Show me all classes in the project

Claude uses: search_code_structure(search_type="classes")
Response:
{
  "status": "success",
  "action": "search_code_structure",
  "search_type": "classes",
  "found": 8,
  "results": [
    {
      "type": "class",
      "name": "DatabaseConnection",
      "file": "db/connection.py",
      "line": 12,
      "methods": 5
    },
    ...
  ]
}
```

✅ **Code Intelligence**: Understand structure without reading full files!

---

## 🔒 Security Features

✅ **Path Safety**: All paths restricted to `BASE_DIR`
- ✅ Prevents `../../etc/passwd` attacks
- ✅ Symlink-safe resolution
- ✅ Access outside base directory is blocked

✅ **File Size Limits**:
- Single files: 2MB max
- Batch operations: 5MB total
- Prevents accidental memory overload

✅ **Binary File Protection**:
- Skips `.exe`, `.dll`, `.pdf`, `.zip`, etc.
- Won't try to read binary as text

---

## ⚙️ Configuration

Edit these constants in `server_v3.py` to customize:

```python
# Token optimization
MAX_FILE_SIZE_KB = 2000        # Max file size (2MB)
MAX_RESULTS = 50               # Max search results
DEFAULT_CHUNK_SIZE_KB = 50     # Chunk size for large files
TOTAL_BATCH_SIZE_KB = 5000     # Total batch read limit
CONTEXT_WIDTH = 80             # Characters around search match
MAX_LINES_TO_SEARCH = 10000    # Stop searching after this many lines

# Ignored directories
IGNORE_DIRS = {".git", "node_modules", "__pycache__", ...}

# Binary file extensions
BINARY_EXTENSIONS = {".exe", ".pdf", ".zip", ...}
```

---

## 🐛 Troubleshooting

### Issue: "Access denied: Path outside base directory"

**Solution**: The path is outside `BASE_DIR`. Set correct `MCP_BASE_DIR`:
```bash
export MCP_BASE_DIR="/path/to/your/projects"
python server_v3.py
```

### Issue: "File too large" error

**Solution**: Use chunked reading:
```
read_file_chunked(path="large_file.log", chunk_index=0)
```

### Issue: Tools not showing in Claude

**Solution**: 
1. Restart Claude (or reload page)
2. Check server is running (look for startup message)
3. Verify `server_v3.py` path is correct in Claude settings

### Issue: "Text not found in file" on replace_text

**Solution**: The exact text might have different whitespace:
1. Use dry_run=True first to see file content
2. Copy exact text from preview
3. Then replace

---

## 📊 Performance Tips

### For Large Codebases:
```
✅ Use search_files_by_ext() to narrow down
✅ Use extensions filter: search_content(query="...", extensions=[".py"])
✅ Use preview_lines on first read: read_file(preview_lines=50)
```

### For Large Files:
```
✅ Always use read_file_chunked() for 500KB+ files
✅ Don't try read_file() on huge logs
```

### For Searches:
```
✅ Use regex patterns: search_content(query="^def", use_regex=True)
✅ Limit extensions: search_content(extensions=[".py", ".txt"])
✅ Set realistic max_results: max_results=10 or 20
```

---

## 🚢 Deployment Options

### Option 1: Local Machine (Development)
```bash
export MCP_BASE_DIR="~/projects"
python server_v3.py
# Leave running, use from Claude.ai
```

### Option 2: Docker Container
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY server_v3.py .
ENV MCP_BASE_DIR=/workspace
CMD ["python", "server_v3.py"]
```

### Option 3: System Service (Linux)
Create `/etc/systemd/system/mcp-fs.service`:
```ini
[Unit]
Description=MCP Filesystem Agent
After=network.target

[Service]
Type=simple
User=youruser
Environment="MCP_BASE_DIR=/home/youruser/projects"
ExecStart=/usr/bin/python3 /path/to/server_v3.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable mcp-fs
sudo systemctl start mcp-fs
```

---

## 📈 What's New in v3

| Feature | v2 | v3 |
|---------|----|----|
| Standardized return types | ❌ | ✅ |
| Proper chunked pagination | ❌ | ✅ |
| Dry-run mode | ❌ | ✅ |
| Regex search | ❌ | ✅ |
| Better tool descriptions | ❌ | ✅ |
| Error handling | ✅ | ✅ |
| Token optimization | ✅ | ✅ |
| Code structure analysis | ✅ | ✅ |
| Path security | ✅ | ✅ |
| File size limits | ✅ | ✅ |

---

## 📚 API Reference by Use Case

### Reading Files Safely
```python
# Quick preview
read_file(path, preview_lines=50)

# Full file (under 2MB)
read_file(path)

# Large file (chunked)
read_file_chunked(path, chunk_index=0, chunk_size_kb=50)

# Multiple files
batch_read_files(["file1.py", "file2.py"])
```

### Editing Files Safely
```python
# Preview changes first
replace_text(path, old, new, dry_run=True)

# Then commit
replace_text(path, old, new)

# Or insert/delete
insert_at_line(path, line_num, text)
delete_lines(path, start, end)
```

### Searching
```python
# Find files
search_files(query="config")

# Find by type
search_files_by_ext(".py")

# Search content (simple)
search_content(query="TODO")

# Search content (regex)
search_content(query="def .*_handler", use_regex=True)

# Analyze code
search_code_structure(search_type="functions")
```

---

## 🤝 Contributing / Extending

Want to add more tools? Edit `server_v3.py`:

```python
@mcp.tool()
def my_new_tool(param: str) -> Dict[str, Any]:
    """Description shown to LLMs.
    
    Args:
        param: What this does.
    
    Returns:
        What it returns.
    """
    try:
        # Your logic here
        return ToolResponse.success("my_new_tool", result="value")
    except Exception as e:
        logger.error(f"Error: {e}")
        return ToolResponse.error(str(e), "my_new_tool")
```

All responses automatically get the standardized format! 🎯

---

## 📝 License & Support

MIT License - Use freely!

For issues, check:
1. `MCP_BASE_DIR` is set correctly
2. Python 3.8+ is installed
3. Server is running (`python server_v3.py`)
4. Claude has permission to access the base directory

---

**Happy file managing! 🚀**
