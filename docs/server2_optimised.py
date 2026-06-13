"""
🎯 TOKEN-EFFICIENT MCP FILESYSTEM AGENT
Purpose: Enable LLMs to perform all file operations with minimal token usage
Features: File search, read, write, edit, batch ops - ALL optimized for tokens
"""

import os
import ast
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import sys
import itertools

from mcp.server import FastMCP

# ========================
# LOGGING SETUP (STDERR ONLY)
# ========================
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========================
# CONFIGURATION
# ========================

mcp = FastMCP("filesystem-agent")

# Base directory - configurable via MCP_BASE_DIR env var
BASE_DIR = Path(os.getenv("MCP_BASE_DIR", str(Path.home() / "Data/Repos"))).resolve()

# Token-efficiency settings
MAX_RESULTS = 50  # Reduced from 100 to minimize token usage
MAX_FILE_SIZE_KB = 500  # Files > 500KB require chunked reading
MAX_LINES_TO_SEARCH = 10000  # Stop searching after this many lines
MAX_PREVIEW_LINES = 100  # Default preview size (saves tokens)
TOTAL_BATCH_SIZE_KB = 2000  # 2MB limit for batch operations
CONTEXT_WIDTH = 40  # Characters around match (20 before, query, 20 after)

# Directories to ignore
IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", "venv", ".venv",
    ".env", "dist", "build", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "*.egg-info", ".tox", ".coverage"
}

# Binary file extensions
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg",
    ".pdf", ".exe", ".dll", ".so", ".zip", ".tar", ".gz",
    ".pyc", ".pyo", ".o", ".a", ".lib", ".db", ".sqlite"
}

# ========================
# HELPER FUNCTIONS
# ========================

def safe_path(path: str) -> Path:
    """Ensure path is within BASE_DIR and symlink-safe."""
    try:
        p = (BASE_DIR / path).resolve()
        base_resolved = BASE_DIR.resolve()

        if not str(p).startswith(str(base_resolved)):
            raise ValueError("Access denied: Path outside base directory")

        return p
    except Exception as e:
        logger.error(f"Path validation error: {e}")
        raise


def is_text_file(path: Path) -> bool:
    """Quick check if file is text-readable (not binary)."""
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return False

    try:
        with open(path, "rb") as f:
            chunk = f.read(512)
            if b'\x00' in chunk:
                return False
        return True
    except:
        return False


def count_file_lines(path: Path) -> int:
    """Count lines in file efficiently."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except:
        return 0


def get_file_size_kb(path: Path) -> float:
    """Get file size in KB."""
    try:
        return round(path.stat().st_size / 1024, 2)
    except:
        return 0


def format_size(kb: float) -> str:
    """Format file size for display."""
    if kb < 1:
        return "<1KB"
    elif kb < 1024:
        return f"{kb:.0f}KB"
    else:
        return f"{kb/1024:.1f}MB"


def get_function_signature(node) -> Optional[str]:
    """Extract function signature from AST node."""
    if not isinstance(node, ast.FunctionDef):
        return None

    args = [arg.arg for arg in node.args.args]
    return f"def {node.name}({', '.join(args)})"


# ========================
# BASIC TOOLS
# ========================

@mcp.tool()
def ping() -> str:
    """Health check - verify server is running."""
    return "pong"


@mcp.tool()
def get_base_dir() -> Dict[str, Any]:
    """Get the base directory info."""
    try:
        stat = BASE_DIR.stat()
        return {
            "base_dir": str(BASE_DIR),
            "exists": BASE_DIR.exists(),
            "is_dir": BASE_DIR.is_dir(),
            "readable": os.access(BASE_DIR, os.R_OK),
            "status": "Ready to manage files"
        }
    except Exception as e:
        return {"error": str(e)}


# ========================
# DIRECTORY LISTING TOOLS
# ========================

@mcp.tool()
def list_directory(path: str = ".") -> Dict[str, Any]:
    """List directory contents with minimal tokens."""
    try:
        p = safe_path(path)
        if not p.is_dir():
            return {"error": f"Not a directory: {path}"}

        items = []
        total_size = 0
        file_count = 0
        dir_count = 0

        for item in sorted(p.iterdir()):
            if item.name.startswith("."):
                continue

            if item.is_dir():
                dir_count += 1
                items.append({"name": item.name + "/", "type": "dir"})
            else:
                file_count += 1
                size_kb = get_file_size_kb(item)
                total_size += size_kb
                items.append({
                    "name": item.name,
                    "type": "file",
                    "size": format_size(size_kb)
                })

        return {
            "path": str(p.relative_to(BASE_DIR.resolve())),
            "items": items,
            "summary": f"{file_count} files, {dir_count} dirs, {format_size(total_size)} total"
        }
    except Exception as e:
        logger.error(f"list_directory error: {e}")
        return {"error": str(e)}


@mcp.tool()
def get_tree(path: str = ".", max_depth: int = 2) -> Dict:
    """Get compact directory tree."""
    try:
        p = safe_path(path)
        if not p.is_dir():
            return {}

        def build_tree(current_path: Path, depth: int) -> Dict:
            if depth >= max_depth:
                return {}

            result = {}
            try:
                for item in sorted(current_path.iterdir()):
                    if item.name.startswith(".") or item.name in IGNORE_DIRS:
                        continue

                    if item.is_dir():
                        result[item.name + "/"] = build_tree(item, depth + 1)
                    else:
                        result[item.name] = format_size(get_file_size_kb(item))
            except:
                pass

            return result

        return build_tree(p, 0)
    except Exception as e:
        logger.error(f"get_tree error: {e}")
        return {}


# ========================
# FILE INFO TOOLS
# ========================

@mcp.tool()
def file_summary(path: str) -> Dict[str, Any]:
    """Get file info without content (minimal tokens)."""
    try:
        p = safe_path(path)
        if not p.exists():
            return {"error": f"File not found: {path}"}

        stat = p.stat()
        size_kb = get_file_size_kb(p)

        result = {
            "path": str(p.relative_to(BASE_DIR.resolve())),
            "size": format_size(size_kb),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }

        if is_text_file(p):
            result["type"] = "text"
            result["lines"] = count_file_lines(p)
        else:
            result["type"] = "binary"

        return result
    except Exception as e:
        logger.error(f"file_summary error: {e}")
        return {"error": str(e)}


# ========================
# FILE READING TOOLS
# ========================

@mcp.tool()
def read_file(path: str, preview_lines: int = 0) -> str:
    """Read file with optional preview mode (saves tokens!)."""
    try:
        p = safe_path(path)
        if not p.exists():
            return f"Error: File not found: {path}"

        size_kb = get_file_size_kb(p)

        if size_kb > MAX_FILE_SIZE_KB:
            return f"Error: File too large ({format_size(size_kb)}). Use read_file_chunked() or preview_lines parameter."

        if preview_lines > 0:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                lines = list(itertools.islice(f, preview_lines))
                content = "".join(lines)
                total_lines = count_file_lines(p)
                return f"[Preview {preview_lines}/{total_lines} lines]\n\n{content}"

        with open(p, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    except Exception as e:
        logger.error(f"read_file error: {e}")
        return f"Error reading file: {e}"


@mcp.tool()
def read_file_chunked(path: str, start_chunk: int = 0, chunk_size_kb: int = 10) -> Dict[str, Any]:
    """Read file in chunks for huge files."""
    try:
        p = safe_path(path)
        if not p.exists():
            return {"error": f"File not found: {path}"}

        size_kb = get_file_size_kb(p)

        with open(p, "rb") as f:
            start_byte = start_chunk * (chunk_size_kb * 1024)
            f.seek(start_byte)

            chunk_bytes = f.read(chunk_size_kb * 1024)
            if not chunk_bytes:
                return {"error": "Chunk out of range", "total_chunks": start_chunk}

            chunk_text = chunk_bytes.decode("utf-8", errors="replace")
            total_chunks = (int(size_kb * 1024) + (chunk_size_kb * 1024) - 1) // (chunk_size_kb * 1024)

            return {
                "chunk": start_chunk,
                "total_chunks": total_chunks,
                "file_size": format_size(size_kb),
                "progress": f"{start_chunk + 1}/{total_chunks}",
                "content": chunk_text
            }

    except Exception as e:
        logger.error(f"read_file_chunked error: {e}")
        return {"error": str(e)}


@mcp.tool()
def batch_read_files(paths: List[str]) -> Dict[str, Any]:
    """Read multiple files at once."""
    try:
        total_size_kb = 0
        file_paths = []

        for path in paths:
            p = safe_path(path)
            if p.exists() and p.is_file():
                size_kb = get_file_size_kb(p)
                if size_kb > MAX_FILE_SIZE_KB:
                    return {"error": f"File too large: {path} ({format_size(size_kb)})"}
                total_size_kb += size_kb
                file_paths.append(p)

        if total_size_kb > TOTAL_BATCH_SIZE_KB:
            return {"error": f"Total size {format_size(total_size_kb)} exceeds limit {format_size(TOTAL_BATCH_SIZE_KB)}"}

        result = {}
        for p in file_paths:
            try:
                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    rel_path = str(p.relative_to(BASE_DIR.resolve()))
                    result[rel_path] = f.read()
            except Exception as e:
                rel_path = str(p.relative_to(BASE_DIR.resolve()))
                result[rel_path] = f"Error: {e}"

        return {
            "count": len(result),
            "total_size": format_size(total_size_kb),
            "files": result
        }

    except Exception as e:
        logger.error(f"batch_read_files error: {e}")
        return {"error": str(e)}


# ========================
# FILE WRITING TOOLS
# ========================

@mcp.tool()
def write_file(path: str, content: str) -> Dict[str, Any]:
    """Create or overwrite a file."""
    try:
        p = safe_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)

        with open(p, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "status": "Written",
            "path": str(p.relative_to(BASE_DIR.resolve())),
            "size": format_size(get_file_size_kb(p)),
            "lines": count_file_lines(p)
        }
    except Exception as e:
        logger.error(f"write_file error: {e}")
        return {"error": str(e)}


@mcp.tool()
def append_file(path: str, content: str) -> Dict[str, Any]:
    """Append content to existing file."""
    try:
        p = safe_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)

        with open(p, "a", encoding="utf-8") as f:
            f.write(content)

        return {
            "status": "Appended",
            "path": str(p.relative_to(BASE_DIR.resolve())),
            "size": format_size(get_file_size_kb(p)),
            "lines": count_file_lines(p)
        }
    except Exception as e:
        logger.error(f"append_file error: {e}")
        return {"error": str(e)}


@mcp.tool()
def create_directory(path: str) -> Dict[str, Any]:
    """Create a directory."""
    try:
        p = safe_path(path)
        p.mkdir(parents=True, exist_ok=True)

        return {
            "status": "Created",
            "path": str(p.relative_to(BASE_DIR.resolve()))
        }
    except Exception as e:
        logger.error(f"create_directory error: {e}")
        return {"error": str(e)}


# ========================
# FILE EDITING TOOLS
# ========================

@mcp.tool()
def replace_text(path: str, old_text: str, new_text: str, count: int = -1) -> Dict[str, Any]:
    """Find and replace text in file."""
    try:
        p = safe_path(path)
        if not p.exists():
            return {"error": f"File not found: {path}"}

        with open(p, "r", encoding="utf-8") as f:
            content = f.read()

        if old_text not in content:
            return {"error": "Text not found in file"}

        if count == -1:
            new_content = content.replace(old_text, new_text)
            replacements = content.count(old_text)
        else:
            new_content = content.replace(old_text, new_text, count)
            replacements = min(count, content.count(old_text))

        with open(p, "w", encoding="utf-8") as f:
            f.write(new_content)

        return {
            "status": "Replaced",
            "path": str(p.relative_to(BASE_DIR.resolve())),
            "replacements": replacements
        }

    except Exception as e:
        logger.error(f"replace_text error: {e}")
        return {"error": str(e)}


@mcp.tool()
def insert_at_line(path: str, line_number: int, text: str) -> Dict[str, Any]:
    """Insert text at a specific line number."""
    try:
        p = safe_path(path)
        if not p.exists():
            return {"error": f"File not found: {path}"}

        with open(p, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if line_number < 1 or line_number > len(lines) + 1:
            return {"error": f"Invalid line {line_number} (file has {len(lines)} lines)"}

        if text and not text.endswith("\n"):
            text += "\n"

        lines.insert(line_number - 1, text)

        with open(p, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return {
            "status": "Inserted",
            "path": str(p.relative_to(BASE_DIR.resolve())),
            "at_line": line_number,
            "total_lines": len(lines)
        }

    except Exception as e:
        logger.error(f"insert_at_line error: {e}")
        return {"error": str(e)}


@mcp.tool()
def delete_lines(path: str, start_line: int, end_line: int) -> Dict[str, Any]:
    """Delete a range of lines."""
    try:
        p = safe_path(path)
        if not p.exists():
            return {"error": f"File not found: {path}"}

        with open(p, "r", encoding="utf-8") as f:
            lines = f.readlines()

        total = len(lines)
        if start_line < 1 or end_line < 1 or start_line > total or end_line > total:
            return {"error": f"Invalid range {start_line}-{end_line} (file has {total} lines)"}

        if start_line > end_line:
            return {"error": "start_line must be <= end_line"}

        del lines[start_line - 1:end_line]
        deleted = end_line - start_line + 1

        with open(p, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return {
            "status": "Deleted",
            "path": str(p.relative_to(BASE_DIR.resolve())),
            "deleted_lines": deleted,
            "remaining_lines": len(lines)
        }

    except Exception as e:
        logger.error(f"delete_lines error: {e}")
        return {"error": str(e)}


# ========================
# SEARCH TOOLS (MINIMAL TOKENS)
# ========================

@mcp.tool()
def search_files(query: str, path: str = ".", max_results: int = 20) -> Dict[str, Any]:
    """Search for files by name (minimal tokens)."""
    try:
        base = safe_path(path)
        results = []
        query_lower = query.lower()

        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

            for file in files:
                if query_lower in file.lower():
                    rel_path = str(Path(root) / file).replace(str(base), "").lstrip("/")
                    results.append(rel_path)

                    if len(results) >= max_results:
                        return {
                            "query": query,
                            "found": len(results),
                            "limited": True,
                            "results": results
                        }

        return {
            "query": query,
            "found": len(results),
            "limited": False,
            "results": results
        }

    except Exception as e:
        logger.error(f"search_files error: {e}")
        return {"error": str(e)}


@mcp.tool()
def search_content(
    query: str,
    path: str = ".",
    max_results: int = 15,
    extensions: List[str] = None
) -> Dict[str, Any]:
    """Search file contents with context (minimal tokens!)."""
    try:
        base = safe_path(path)
        results = []
        query_lower = query.lower()
        total_lines_searched = 0

        if extensions:
            extensions = {ext if ext.startswith(".") else "." + ext for ext in extensions}

        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

            for file in files:
                file_path = Path(root) / file

                if extensions and file_path.suffix not in extensions:
                    continue

                if not is_text_file(file_path):
                    continue

                if get_file_size_kb(file_path) > MAX_FILE_SIZE_KB:
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_num, line in enumerate(f, 1):
                            total_lines_searched += 1

                            if total_lines_searched > MAX_LINES_TO_SEARCH:
                                return {
                                    "query": query,
                                    "found": len(results),
                                    "limited": True,
                                    "reason": f"Searched {MAX_LINES_TO_SEARCH} lines",
                                    "results": results
                                }

                            if query_lower in line.lower():
                                rel_path = str(file_path.relative_to(base))

                                line_lower = line.lower()
                                match_pos = line_lower.find(query_lower)
                                start = max(0, match_pos - CONTEXT_WIDTH)
                                end = min(len(line), match_pos + len(query) + CONTEXT_WIDTH)
                                context = line[start:end].strip()

                                results.append({
                                    "file": rel_path,
                                    "line": line_num,
                                    "match": context
                                })

                                if len(results) >= max_results:
                                    return {
                                        "query": query,
                                        "found": len(results),
                                        "limited": True,
                                        "reason": f"Found {max_results} matches",
                                        "results": results
                                    }

                except Exception as e:
                    logger.debug(f"Error reading {file_path}: {e}")
                    continue

        return {
            "query": query,
            "found": len(results),
            "limited": False,
            "results": results
        }

    except Exception as e:
        logger.error(f"search_content error: {e}")
        return {"error": str(e)}


@mcp.tool()
def search_files_by_ext(extension: str, path: str = ".", max_results: int = 30) -> Dict[str, Any]:
    """Find files by extension (minimal tokens)."""
    try:
        base = safe_path(path)
        results = []

        if not extension.startswith("."):
            extension = "." + extension

        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

            for file in files:
                if file.endswith(extension):
                    rel_path = str(Path(root) / file).replace(str(base), "").lstrip("/")
                    results.append(rel_path)

                    if len(results) >= max_results:
                        return {
                            "extension": extension,
                            "found": len(results),
                            "limited": True,
                            "results": results
                        }

        return {
            "extension": extension,
            "found": len(results),
            "limited": False,
            "results": results
        }

    except Exception as e:
        logger.error(f"search_files_by_ext error: {e}")
        return {"error": str(e)}


# ========================
# CODE INTELLIGENCE (PYTHON ONLY)
# ========================

@mcp.tool()
def search_code_structure(
    path: str = ".",
    search_type: str = "functions",
    max_results: int = 25
) -> Dict[str, Any]:
    """Find Python code structures (functions, classes, imports)."""
    base = safe_path(path)
    results = []

    try:
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

            for file in files:
                if not file.endswith(".py"):
                    continue

                file_path = Path(root) / file

                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        tree = ast.parse(f.read())

                    rel_path = str(file_path.relative_to(base))

                    for node in ast.walk(tree):
                        if search_type == "functions" and isinstance(node, ast.FunctionDef):
                            results.append({
                                "type": "function",
                                "name": node.name,
                                "file": rel_path,
                                "line": node.lineno,
                                "signature": get_function_signature(node),
                                "args": len(node.args.args)
                            })

                        elif search_type == "classes" and isinstance(node, ast.ClassDef):
                            results.append({
                                "type": "class",
                                "name": node.name,
                                "file": rel_path,
                                "line": node.lineno,
                                "methods": len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                            })

                        elif search_type == "imports" and isinstance(node, (ast.Import, ast.ImportFrom)):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    results.append({
                                        "type": "import",
                                        "module": alias.name,
                                        "file": rel_path,
                                        "line": node.lineno
                                    })
                            else:
                                results.append({
                                    "type": "from_import",
                                    "module": node.module or ".",
                                    "file": rel_path,
                                    "line": node.lineno,
                                    "items": len(node.names)
                                })

                        if len(results) >= max_results:
                            return {
                                "search_type": search_type,
                                "language": "Python",
                                "found": len(results),
                                "limited": True,
                                "results": results
                            }

                except Exception as e:
                    logger.debug(f"Error parsing {file_path}: {e}")
                    continue

        return {
            "search_type": search_type,
            "language": "Python",
            "found": len(results),
            "limited": False,
            "results": results
        }

    except Exception as e:
        logger.error(f"search_code_structure error: {e}")
        return {"error": str(e)}


# ========================
# SERVER STARTUP
# ========================

if __name__ == "__main__":
    logger.info("🚀 Token-Optimized MCP Filesystem Agent v2 starting...")
    logger.info(f"📁 BASE_DIR: {BASE_DIR}")
    logger.info(f"⭐ Optimized for: Minimal token usage + LLM efficiency")
    logger.info(f"🔧 Tools: 20+ file operations")
    logger.info(f"✅ All systems operational")

    mcp.run(transport='stdio')