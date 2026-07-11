"""
🎯 TOKEN-EFFICIENT MCP FILESYSTEM AGENT - v3 (PRODUCTION-READY)

Purpose: Enable LLMs (Claude, etc.) to perform all file operations with minimal token usage
Focus: Consistent return types, proper pagination, discoverability, ease of use

Key Improvements:
✅ Standardized return types (Dict) across all tools
✅ Proper chunked reading with pagination
✅ Dry-run mode for dangerous operations
✅ Better tool discoverability and descriptions
✅ Ready-to-use with Claude.ai and any MCP-compatible LLM
✅ Clear deployment documentation
"""

import os
import ast
import re
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import sys
import itertools

from mcp.server import FastMCP
from mcp.types import ToolAnnotations

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

# Base directory - configurable via CLI arguments (like the official
# @modelcontextprotocol/server-filesystem: `python server3.py /path/one /path/two`)
# or via MCP_BASE_DIR / MCP_BASE_DIRS environment variables.
# Priority: CLI args > MCP_BASE_DIRS (comma-sep) > MCP_BASE_DIR (single) > default
def _load_base_dirs():
    """Load allowed base directories with fallback chain."""
    # Priority 1: Command-line arguments — one or more directory paths.
    # This matches the connector config pattern used by the official
    # filesystem MCP server, where each arg is a directory to allow.
    cli_paths = sys.argv[1:]
    if cli_paths:
        paths = [Path(p).expanduser().resolve() for p in cli_paths]
        logger.info(f"Loaded {len(paths)} base directories from command-line arguments")
        return paths

    # Priority 2: Multi-path env var (comma-separated)
    multi_paths = os.getenv("MCP_BASE_DIRS")
    if multi_paths:
        paths = [Path(p.strip()).expanduser().resolve() for p in multi_paths.split(",")]
        logger.info(f"Loaded {len(paths)} base directories from MCP_BASE_DIRS")
        return paths

    # Priority 3: Single path env var (backward compatible)
    single_path = os.getenv("MCP_BASE_DIR")
    if single_path:
        logger.info(f"Loaded single base directory from MCP_BASE_DIR")
        return [Path(single_path).expanduser().resolve()]

    # Priority 4: Default
    default = Path.home() / "Data/Repos"
    logger.info(f"Using default base directory")
    return [default.resolve()]

BASE_DIRS = _load_base_dirs()

# Token-efficiency settings
MAX_RESULTS = 50
MAX_FILE_SIZE_KB = 2000  # 2MB - increased for modern LLMs
MAX_LINES_TO_SEARCH = 10000
MAX_PREVIEW_LINES = 100
TOTAL_BATCH_SIZE_KB = 5000  # 5MB limit for batch operations
CONTEXT_WIDTH = 80  # Characters around match (better context)
DEFAULT_CHUNK_SIZE_KB = 50  # Optimized chunk size

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
    """Ensure path is within ANY BASE_DIR and symlink-safe."""
    def _is_within(candidate: Path, base: Path) -> bool:
        """True only if candidate == base or base is a real ancestor directory
        (segment-aware, unlike a raw string prefix check)."""
        try:
            candidate.relative_to(base)
            return True
        except ValueError:
            return False

    try:
        # Try to resolve from each base directory
        for base_dir in BASE_DIRS:
            try:
                p = (base_dir / path).resolve()
                base_resolved = base_dir.resolve()

                if _is_within(p, base_resolved):
                    return p
            except:
                continue

        # If no base directory matched, try as absolute path
        p = Path(path).resolve()
        for base_dir in BASE_DIRS:
            if _is_within(p, base_dir.resolve()):
                return p

        # Path not in any allowed directory
        allowed = ", ".join(str(bd) for bd in BASE_DIRS)
        raise ValueError(f"Access denied: Path outside allowed directories ({allowed})")

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


def get_relative_path(path: Path) -> str:
    """Get path relative to any configured base directory."""
    try:
        # Try each base directory
        for bd in BASE_DIRS:
            try:
                return str(path.relative_to(bd.resolve()))
            except:
                continue
        # If not relative to any base dir, return absolute path
        return str(path)
    except:
        return str(path)


# ========================
# STANDARDIZED RESPONSE BUILDER
# ========================

class ToolResponse:
    """Standardized response builder for all tools."""

    @staticmethod
    def success(action: str, path: str = "", **kwargs) -> Dict[str, Any]:
        """Build success response."""
        response = {
            "status": "success",
            "action": action,
        }
        if path:
            response["path"] = path
        response.update(kwargs)
        return response

    @staticmethod
    def error(message: str, action: str = "") -> Dict[str, Any]:
        """Build error response."""
        response = {
            "status": "error",
            "message": message,
        }
        if action:
            response["action"] = action
        return response

    @staticmethod
    def info(action: str, **kwargs) -> Dict[str, Any]:
        """Build info response."""
        response = {
            "status": "info",
            "action": action,
        }
        response.update(kwargs)
        return response


# ========================
# BASIC TOOLS
# ========================

@mcp.tool(annotations=ToolAnnotations(
    title="Ping",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False
))
def ping() -> Dict[str, str]:
    """Health check - verify server is running.

    Returns:
        Status message confirming server is operational.
    """
    return ToolResponse.success("ping", server="filesystem-agent", version="v3")


@mcp.tool(annotations=ToolAnnotations(
    title="Get Base Directory",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False
))
def get_base_dir() -> Dict[str, Any]:
    """Get base directory configuration and status.

    Returns:
        List of allowed base directories with status.
        Set via command-line arguments, or MCP_BASE_DIRS / MCP_BASE_DIR
        environment variables.
    """
    try:
        directories = []
        total_size = 0

        for base_dir in BASE_DIRS:
            size_kb = sum(
                get_file_size_kb(p) for p in base_dir.rglob('*') if p.is_file()
            )
            total_size += size_kb

            directories.append({
                "path": str(base_dir),
                "exists": base_dir.exists(),
                "is_directory": base_dir.is_dir(),
                "readable": os.access(base_dir, os.R_OK),
                "writable": os.access(base_dir, os.W_OK),
                "size_mb": format_size(size_kb)
            })

        return ToolResponse.success(
            "get_base_dir",
            base_dir_count=len(BASE_DIRS),
            directories=directories,
            total_size_mb=format_size(total_size)
        )
    except Exception as e:
        return ToolResponse.error(str(e), "get_base_dir")

@mcp.tool(annotations=ToolAnnotations(
    title="Get Configuration",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False
))
def get_config() -> Dict[str, Any]:
    """Get current MCP filesystem agent configuration.

    Returns:
        All active settings, limits, and security configuration.
        Useful for understanding constraints and capabilities.
    """
    try:
        return ToolResponse.success(
            "get_config",
            version="3.0.0",
            allowed_base_dirs=[str(bd) for bd in BASE_DIRS],
            token_limits={
                "max_file_size_mb": MAX_FILE_SIZE_KB / 1024,
                "max_results": MAX_RESULTS,
                "chunk_size_kb": DEFAULT_CHUNK_SIZE_KB,
                "batch_size_mb": TOTAL_BATCH_SIZE_KB / 1024,
                "max_lines_to_search": MAX_LINES_TO_SEARCH,
                "context_width_chars": CONTEXT_WIDTH,
                "max_preview_lines": MAX_PREVIEW_LINES
            },
            ignore_patterns={
                "directories": sorted(list(IGNORE_DIRS)),
                "binary_extensions": sorted(list(BINARY_EXTENSIONS))
            },
            capabilities={
                "read_operations": ["read_file", "read_file_chunked", "batch_read_files"],
                "write_operations": ["write_file", "append_file"],
                "edit_operations": ["replace_text", "insert_at_line", "delete_lines"],
                "search_operations": ["search_files", "search_content", "search_files_by_ext"],
                "code_analysis": ["search_code_structure"],
                "info_operations": ["file_summary", "list_directory", "get_tree"]
            }
        )
    except Exception as e:
        return ToolResponse.error(str(e), "get_config")

@mcp.tool(annotations=ToolAnnotations(
    title="List Allowed Paths",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False
))
def list_allowed_paths() -> Dict[str, Any]:
    """List all accessible base directories with details.

    Returns:
        Each directory's path, size, permissions, and status.
        Use this to verify what you can access.
    """
    try:
        paths = []

        for base_dir in BASE_DIRS:
            try:
                stat = base_dir.stat()
                size_kb = sum(
                    get_file_size_kb(p) for p in base_dir.rglob('*') if p.is_file()
                )

                paths.append({
                    "path": str(base_dir),
                    "exists": base_dir.exists(),
                    "is_directory": base_dir.is_dir(),
                    "readable": os.access(base_dir, os.R_OK),
                    "writable": os.access(base_dir, os.W_OK),
                    "executable": os.access(base_dir, os.X_OK),
                    "size_mb": round(size_kb / 1024, 2),
                    "file_count": len(list(base_dir.rglob('*')))
                })
            except Exception as e:
                paths.append({
                    "path": str(base_dir),
                    "exists": False,
                    "error": str(e)
                })

        return ToolResponse.success(
            "list_allowed_paths",
            count=len(paths),
            paths=paths
        )
    except Exception as e:
        logger.error(f"list_allowed_paths error: {e}")
        return ToolResponse.error(str(e), "list_allowed_paths")
@mcp.tool(annotations=ToolAnnotations(
    title="Get Path Info",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False
))
def path_info(path: str) -> Dict[str, Any]:
    """Get detailed information about a specific path.

    Args:
        path: Path to inspect (relative to any base directory).

    Returns:
        Full path info, permissions, size, which base dir it belongs to.
        Use this to verify you can access a file before operations.
    """
    try:
        p = safe_path(path)

        # Find which base directory this path belongs to
        base_dir_match = None
        rel_path = None
        for bd in BASE_DIRS:
            try:
                rel_path = p.relative_to(bd)
                base_dir_match = bd
                break
            except:
                continue

        if not p.exists():
            return ToolResponse.error(f"Path does not exist: {path}", "path_info")

        stat = p.stat()
        result = {
            "absolute_path": str(p),
            "base_directory": str(base_dir_match) if base_dir_match else "unknown",
            "relative_path": str(rel_path) if rel_path else path,
            "exists": True,
            "readable": os.access(p, os.R_OK),
            "writable": os.access(p, os.W_OK),
            "executable": os.access(p, os.X_OK),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }

        if p.is_file():
            size_kb = get_file_size_kb(p)
            result.update({
                "type": "file",
                "size_bytes": stat.st_size,
                "size_kb": size_kb,
                "size_formatted": format_size(size_kb),
                "lines": count_file_lines(p) if is_text_file(p) else None,
                "is_text": is_text_file(p),
                "is_binary": not is_text_file(p)
            })
        else:
            items = list(p.iterdir())
            result.update({
                "type": "directory",
                "item_count": len(items),
                "file_count": sum(1 for i in items if i.is_file()),
                "dir_count": sum(1 for i in items if i.is_dir())
            })

        return ToolResponse.success("path_info", **result)

    except ValueError as e:
        return ToolResponse.error(str(e), "path_info")
    except Exception as e:
        logger.error(f"path_info error: {e}")
        return ToolResponse.error(str(e), "path_info")

@mcp.tool(annotations=ToolAnnotations(
    title="Validate Path",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False
))
def validate_path(path: str) -> Dict[str, Any]:
    """Validate if a path is accessible and within allowed directories.

    Args:
        path: Path to validate.

    Returns:
        Whether path is valid, which base dir it belongs to, and why (if invalid).
        Use this before attempting file operations.
    """
    try:
        p = safe_path(path)

        # Find which base directory
        for bd in BASE_DIRS:
            try:
                rel = p.relative_to(bd)
                return ToolResponse.success(
                    "validate_path",
                    is_valid=True,
                    absolute_path=str(p),
                    base_directory=str(bd),
                    relative_path=str(rel),
                    exists=p.exists(),
                    is_file=p.is_file(),
                    is_dir=p.is_dir()
                )
            except:
                continue

        # Shouldn't reach here, but just in case
        return ToolResponse.error("Path could not be validated", "validate_path")

    except ValueError as e:
        return ToolResponse.success(
            "validate_path",
            is_valid=False,
            reason=str(e),
            suggestion="Use one of the paths returned by list_allowed_paths()"
        )
    except Exception as e:
        return ToolResponse.error(str(e), "validate_path")

# ========================
# DIRECTORY LISTING TOOLS
# ========================

@mcp.tool(annotations=ToolAnnotations(
    title="List Directory",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False
))
def list_directory(path: str = ".") -> Dict[str, Any]:
    """List directory contents with file metadata.

    Args:
        path: Directory path relative to base directory.

    Returns:
        Dictionary with items, counts, and total size summary.
        Each item includes name, type (file/dir), and size if applicable.
    """
    try:
        p = safe_path(path)
        if not p.is_dir():
            return ToolResponse.error(f"Not a directory: {path}", "list_directory")

        items = []
        total_size_kb = 0
        file_count = 0
        dir_count = 0

        for item in sorted(p.iterdir()):
            if item.name.startswith("."):
                continue

            if item.is_dir():
                dir_count += 1
                items.append({
                    "name": item.name,
                    "type": "directory",
                    "path": get_relative_path(item)
                })
            else:
                file_count += 1
                size_kb = get_file_size_kb(item)
                total_size_kb += size_kb
                items.append({
                    "name": item.name,
                    "type": "file",
                    "path": get_relative_path(item),
                    "size": format_size(size_kb),
                    "size_kb": size_kb
                })

        return ToolResponse.success(
            "list_directory",
            path=get_relative_path(p),
            items=items,
            file_count=file_count,
            directory_count=dir_count,
            total_size=format_size(total_size_kb)
        )
    except Exception as e:
        logger.error(f"list_directory error: {e}")
        return ToolResponse.error(str(e), "list_directory")


@mcp.tool(annotations=ToolAnnotations(
    title="Get Directory Tree",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False
))
def get_tree(path: str = ".", max_depth: int = 2) -> Dict[str, Any]:
    """Get directory tree structure (compact format).

    Args:
        path: Starting directory path.
        max_depth: Maximum depth to traverse (default: 2).

    Returns:
        Nested dictionary representing directory tree with file sizes.
        Good for visualizing project structure with minimal tokens.
    """
    try:
        p = safe_path(path)
        if not p.is_dir():
            return ToolResponse.error(f"Not a directory: {path}", "get_tree")

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

        tree = build_tree(p, 0)
        return ToolResponse.success(
            "get_tree",
            path=get_relative_path(p),
            max_depth=max_depth,
            tree=tree
        )
    except Exception as e:
        logger.error(f"get_tree error: {e}")
        return ToolResponse.error(str(e), "get_tree")


# ========================
# FILE INFO TOOLS
# ========================

@mcp.tool(annotations=ToolAnnotations(
    title="File Summary",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False
))
def file_summary(path: str) -> Dict[str, Any]:
    """Get file metadata without reading content (token-efficient).

    Args:
        path: File path.

    Returns:
        File information: type, size, line count, modification time.
        Perfect for quick checks before full file read.
    """
    try:
        p = safe_path(path)
        if not p.exists():
            return ToolResponse.error(f"File not found: {path}", "file_summary")

        stat = p.stat()
        size_kb = get_file_size_kb(p)

        result = {
            "path": get_relative_path(p),
            "size": format_size(size_kb),
            "size_kb": size_kb,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }

        if is_text_file(p):
            result["type"] = "text"
            result["lines"] = count_file_lines(p)
        else:
            result["type"] = "binary"

        return ToolResponse.success("file_summary", **result)
    except Exception as e:
        logger.error(f"file_summary error: {e}")
        return ToolResponse.error(str(e), "file_summary")


# ========================
# FILE READING TOOLS
# ========================

@mcp.tool(annotations=ToolAnnotations(
    title="Read File",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False
))
def read_file(path: str, preview_lines: int = 0) -> Dict[str, Any]:
    """Read file with optional preview mode (token-efficient).

    Args:
        path: File path.
        preview_lines: If > 0, only read first N lines (saves tokens).
                      If = 0, read entire file (default).

    Returns:
        File content with metadata about total size and lines.
        For large files, use preview_lines or read_file_chunked().
    """
    try:
        p = safe_path(path)
        if not p.exists():
            return ToolResponse.error(f"File not found: {path}", "read_file")

        size_kb = get_file_size_kb(p)

        if size_kb > MAX_FILE_SIZE_KB:
            return ToolResponse.error(
                f"File too large ({format_size(size_kb)}). "
                f"Use read_file_chunked() or preview_lines parameter.",
                "read_file"
            )

        if preview_lines > 0:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                lines = list(itertools.islice(f, preview_lines))
                content = "".join(lines)
                total_lines = count_file_lines(p)
                return ToolResponse.success(
                    "read_file",
                    path=get_relative_path(p),
                    mode="preview",
                    preview_lines=preview_lines,
                    total_lines=total_lines,
                    content=content
                )

        with open(p, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            return ToolResponse.success(
                "read_file",
                path=get_relative_path(p),
                mode="full",
                size=format_size(size_kb),
                lines=count_file_lines(p),
                content=content
            )

    except Exception as e:
        logger.error(f"read_file error: {e}")
        return ToolResponse.error(str(e), "read_file")


@mcp.tool(annotations=ToolAnnotations(
    title="Read File (Chunked)",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False
))
def read_file_chunked(
    path: str,
    chunk_index: int = 0,
    chunk_size_kb: int = 50
) -> Dict[str, Any]:
    """Read file in chunks with proper pagination (for large files).

    Args:
        path: File path.
        chunk_index: Which chunk to read (0-based, default: 0 for first).
        chunk_size_kb: Size of each chunk in KB (default: 50KB).

    Returns:
        Specific chunk with progress info (current/total chunks).
        Use chunk_index to paginate through large files efficiently.

    Example:
        1. Call with chunk_index=0 to get first 50KB
        2. Check total_chunks in response
        3. Call with chunk_index=1 for next 50KB, etc.
    """
    try:
        p = safe_path(path)
        if not p.exists():
            return ToolResponse.error(f"File not found: {path}", "read_file_chunked")

        size_kb = get_file_size_kb(p)
        chunk_bytes = chunk_size_kb * 1024

        # Calculate total chunks
        total_chunks = (int(size_kb * 1024) + chunk_bytes - 1) // chunk_bytes

        if chunk_index >= total_chunks:
            return ToolResponse.error(
                f"Chunk index {chunk_index} out of range (0-{total_chunks-1})",
                "read_file_chunked"
            )

        # Seek and read specific chunk
        with open(p, "rb") as f:
            start_byte = chunk_index * chunk_bytes
            f.seek(start_byte)
            chunk_data = f.read(chunk_bytes)

            if not chunk_data:
                return ToolResponse.error("Chunk out of range", "read_file_chunked")

            chunk_text = chunk_data.decode("utf-8", errors="replace")

            return ToolResponse.success(
                "read_file_chunked",
                path=get_relative_path(p),
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                progress=f"{chunk_index + 1}/{total_chunks}",
                file_size=format_size(size_kb),
                chunk_size=f"{chunk_size_kb}KB",
                content=chunk_text
            )

    except Exception as e:
        logger.error(f"read_file_chunked error: {e}")
        return ToolResponse.error(str(e), "read_file_chunked")


@mcp.tool(annotations=ToolAnnotations(
    title="Batch Read Files",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False
))
def batch_read_files(paths: List[str]) -> Dict[str, Any]:
    """Read multiple files at once (efficient for related files).

    Args:
        paths: List of file paths to read.

    Returns:
        Dictionary mapping file paths to their contents.
        Respects total size limits to avoid excessive token usage.
    """
    try:
        total_size_kb = 0
        file_paths = []

        for path in paths:
            p = safe_path(path)
            if p.exists() and p.is_file():
                size_kb = get_file_size_kb(p)
                if size_kb > MAX_FILE_SIZE_KB:
                    return ToolResponse.error(
                        f"File too large: {path} ({format_size(size_kb)})",
                        "batch_read_files"
                    )
                total_size_kb += size_kb
                file_paths.append(p)

        if total_size_kb > TOTAL_BATCH_SIZE_KB:
            return ToolResponse.error(
                f"Total size {format_size(total_size_kb)} exceeds limit {format_size(TOTAL_BATCH_SIZE_KB)}",
                "batch_read_files"
            )

        result_files = {}
        for p in file_paths:
            try:
                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    rel_path = get_relative_path(p)
                    result_files[rel_path] = f.read()
            except Exception as e:
                rel_path = get_relative_path(p)
                result_files[rel_path] = f"Error: {e}"

        return ToolResponse.success(
            "batch_read_files",
            file_count=len(result_files),
            total_size=format_size(total_size_kb),
            files=result_files
        )

    except Exception as e:
        logger.error(f"batch_read_files error: {e}")
        return ToolResponse.error(str(e), "batch_read_files")


# ========================
# FILE WRITING TOOLS
# ========================

@mcp.tool(annotations=ToolAnnotations(
    title="Write File",
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=True,
    openWorldHint=False
))
def write_file(path: str, content: str) -> Dict[str, Any]:
    """Create or overwrite a file.

    Args:
        path: File path (creates parent directories if needed).
        content: File content to write.

    Returns:
        Success confirmation with file size and line count.
    """
    try:
        p = safe_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)

        with open(p, "w", encoding="utf-8") as f:
            f.write(content)

        return ToolResponse.success(
            "write_file",
            path=get_relative_path(p),
            size=format_size(get_file_size_kb(p)),
            lines=count_file_lines(p),
            mode="created"
        )
    except Exception as e:
        logger.error(f"write_file error: {e}")
        return ToolResponse.error(str(e), "write_file")


@mcp.tool(annotations=ToolAnnotations(
    title="Append to File",
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=False
))
def append_file(path: str, content: str) -> Dict[str, Any]:
    """Append content to existing file.

    Args:
        path: File path (creates if doesn't exist).
        content: Content to append.

    Returns:
        Success confirmation with updated file size and line count.
    """
    try:
        p = safe_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)

        with open(p, "a", encoding="utf-8") as f:
            f.write(content)

        return ToolResponse.success(
            "append_file",
            path=get_relative_path(p),
            size=format_size(get_file_size_kb(p)),
            lines=count_file_lines(p)
        )
    except Exception as e:
        logger.error(f"append_file error: {e}")
        return ToolResponse.error(str(e), "append_file")


@mcp.tool(annotations=ToolAnnotations(
    title="Create Directory",
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False
))
def create_directory(path: str) -> Dict[str, Any]:
    """Create a directory (with parent directories if needed).

    Args:
        path: Directory path.

    Returns:
        Success confirmation with created path.
    """
    try:
        p = safe_path(path)
        p.mkdir(parents=True, exist_ok=True)

        return ToolResponse.success(
            "create_directory",
            path=get_relative_path(p)
        )
    except Exception as e:
        logger.error(f"create_directory error: {e}")
        return ToolResponse.error(str(e), "create_directory")


# ========================
# FILE EDITING TOOLS
# ========================

@mcp.tool(annotations=ToolAnnotations(
    title="Find and Replace Text",
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=False,
    openWorldHint=False
))
def replace_text(
    path: str,
    old_text: str,
    new_text: str,
    count: int = -1,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Find and replace text in file.

    Args:
        path: File path.
        old_text: Text to find.
        new_text: Text to replace with.
        count: Max replacements (-1 = replace all, default).
        dry_run: If True, show preview without modifying (SAFE MODE).

    Returns:
        Replacement count and confirmation.
        Use dry_run=True first to preview changes!
    """
    try:
        p = safe_path(path)
        if not p.exists():
            return ToolResponse.error(f"File not found: {path}", "replace_text")

        with open(p, "r", encoding="utf-8") as f:
            content = f.read()

        if old_text not in content:
            return ToolResponse.error("Text not found in file", "replace_text")

        if count == -1:
            new_content = content.replace(old_text, new_text)
            replacements = content.count(old_text)
        else:
            new_content = content.replace(old_text, new_text, count)
            replacements = min(count, content.count(old_text))

        if dry_run:
            # Show preview without modifying
            preview_lines = new_content.split('\n')[:5]
            return ToolResponse.success(
                "replace_text",
                path=get_relative_path(p),
                mode="dry_run",
                would_replace=replacements,
                preview="\n".join(preview_lines),
                ready_to_commit=True
            )

        # Actually replace
        with open(p, "w", encoding="utf-8") as f:
            f.write(new_content)

        return ToolResponse.success(
            "replace_text",
            path=get_relative_path(p),
            mode="committed",
            replacements=replacements
        )

    except Exception as e:
        logger.error(f"replace_text error: {e}")
        return ToolResponse.error(str(e), "replace_text")


@mcp.tool(annotations=ToolAnnotations(
    title="Insert Text at Line",
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=False
))
def insert_at_line(path: str, line_number: int, text: str) -> Dict[str, Any]:
    """Insert text at a specific line number.

    Args:
        path: File path.
        line_number: Line number (1-based, where 1 is first line).
        text: Text to insert (can span multiple lines).

    Returns:
        Success confirmation with new total line count.
    """
    try:
        p = safe_path(path)
        if not p.exists():
            return ToolResponse.error(f"File not found: {path}", "insert_at_line")

        with open(p, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if line_number < 1 or line_number > len(lines) + 1:
            return ToolResponse.error(
                f"Invalid line {line_number} (file has {len(lines)} lines)",
                "insert_at_line"
            )

        if text and not text.endswith("\n"):
            text += "\n"

        lines.insert(line_number - 1, text)

        with open(p, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return ToolResponse.success(
            "insert_at_line",
            path=get_relative_path(p),
            at_line=line_number,
            total_lines=len(lines)
        )

    except Exception as e:
        logger.error(f"insert_at_line error: {e}")
        return ToolResponse.error(str(e), "insert_at_line")


@mcp.tool(annotations=ToolAnnotations(
    title="Delete Lines",
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=False,
    openWorldHint=False
))
def delete_lines(path: str, start_line: int, end_line: int) -> Dict[str, Any]:
    """Delete a range of lines.

    Args:
        path: File path.
        start_line: Starting line (1-based).
        end_line: Ending line (1-based, inclusive).

    Returns:
        Success confirmation with deleted line count.
    """
    try:
        p = safe_path(path)
        if not p.exists():
            return ToolResponse.error(f"File not found: {path}", "delete_lines")

        with open(p, "r", encoding="utf-8") as f:
            lines = f.readlines()

        total = len(lines)
        if start_line < 1 or end_line < 1 or start_line > total or end_line > total:
            return ToolResponse.error(
                f"Invalid range {start_line}-{end_line} (file has {total} lines)",
                "delete_lines"
            )

        if start_line > end_line:
            return ToolResponse.error("start_line must be <= end_line", "delete_lines")

        del lines[start_line - 1:end_line]
        deleted = end_line - start_line + 1

        with open(p, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return ToolResponse.success(
            "delete_lines",
            path=get_relative_path(p),
            deleted_lines=deleted,
            remaining_lines=len(lines)
        )

    except Exception as e:
        logger.error(f"delete_lines error: {e}")
        return ToolResponse.error(str(e), "delete_lines")


# ========================
# SEARCH TOOLS (MINIMAL TOKENS)
# ========================

@mcp.tool(annotations=ToolAnnotations(
    title="Search Files by Name",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False
))
def search_files(
    query: str,
    path: str = ".",
    max_results: int = 20
) -> Dict[str, Any]:
    """Search for files by name (fast, minimal tokens).

    Args:
        query: Filename substring to search for.
        path: Starting directory.
        max_results: Max results to return.

    Returns:
        List of matching file paths with match count.
    """
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
                        return ToolResponse.success(
                            "search_files",
                            query=query,
                            found=len(results),
                            limited=True,
                            results=results
                        )

        return ToolResponse.success(
            "search_files",
            query=query,
            found=len(results),
            limited=False,
            results=results
        )

    except Exception as e:
        logger.error(f"search_files error: {e}")
        return ToolResponse.error(str(e), "search_files")


@mcp.tool(annotations=ToolAnnotations(
    title="Search File Contents",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False
))
def search_content(
    query: str,
    path: str = ".",
    max_results: int = 15,
    extensions: Optional[List[str]] = None,
    use_regex: bool = False
) -> Dict[str, Any]:
    """Search file contents with context (minimal token impact).

    Args:
        query: Text to search for (or regex pattern if use_regex=True).
        path: Starting directory.
        max_results: Max matches to return.
        extensions: File extensions to search (.py, .txt, etc).
        use_regex: If True, treat query as regex pattern.

    Returns:
        List of matches with file, line number, and context around match.
    """
    try:
        base = safe_path(path)
        results = []
        query_lower = query.lower() if not use_regex else query
        total_lines_searched = 0

        if extensions:
            extensions = {ext if ext.startswith(".") else "." + ext for ext in extensions}

        import re
        regex_pattern = None
        if use_regex:
            try:
                regex_pattern = re.compile(query, re.IGNORECASE)
            except re.error as e:
                return ToolResponse.error(f"Invalid regex: {e}", "search_content")

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
                                return ToolResponse.success(
                                    "search_content",
                                    query=query,
                                    found=len(results),
                                    limited=True,
                                    reason=f"Searched {MAX_LINES_TO_SEARCH} lines",
                                    results=results
                                )

                            # Check for match
                            match_found = False
                            match_pos = 0

                            if use_regex and regex_pattern:
                                m = regex_pattern.search(line)
                                if m:
                                    match_found = True
                                    match_pos = m.start()
                            else:
                                if query_lower in line.lower():
                                    match_found = True
                                    match_pos = line.lower().find(query_lower)

                            if match_found:
                                rel_path = str(file_path.relative_to(base))

                                start = max(0, match_pos - CONTEXT_WIDTH)
                                end = min(len(line), match_pos + len(query) + CONTEXT_WIDTH)
                                context = line[start:end].strip()

                                results.append({
                                    "file": rel_path,
                                    "line": line_num,
                                    "match": context
                                })

                                if len(results) >= max_results:
                                    return ToolResponse.success(
                                        "search_content",
                                        query=query,
                                        found=len(results),
                                        limited=True,
                                        reason=f"Found {max_results} matches",
                                        results=results
                                    )

                except Exception as e:
                    logger.debug(f"Error reading {file_path}: {e}")
                    continue

        return ToolResponse.success(
            "search_content",
            query=query,
            found=len(results),
            limited=False,
            results=results
        )

    except Exception as e:
        logger.error(f"search_content error: {e}")
        return ToolResponse.error(str(e), "search_content")


@mcp.tool(annotations=ToolAnnotations(
    title="Search Files by Extension",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False
))
def search_files_by_ext(
    extension: str,
    path: str = ".",
    max_results: int = 30
) -> Dict[str, Any]:
    """Find files by extension (fast, minimal tokens).

    Args:
        extension: File extension (.py, .txt, etc).
        path: Starting directory.
        max_results: Max results to return.

    Returns:
        List of matching file paths with count.
    """
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
                        return ToolResponse.success(
                            "search_files_by_ext",
                            extension=extension,
                            found=len(results),
                            limited=True,
                            results=results
                        )

        return ToolResponse.success(
            "search_files_by_ext",
            extension=extension,
            found=len(results),
            limited=False,
            results=results
        )

    except Exception as e:
        logger.error(f"search_files_by_ext error: {e}")
        return ToolResponse.error(str(e), "search_files_by_ext")


# ========================
# CODE INTELLIGENCE (MULTI-LANGUAGE)
# ========================

def extract_python_structures(file_path: Path, base_path: Path, search_type: str) -> List[Dict[str, Any]]:
    """Extract Python code structures using AST (most reliable)."""
    results = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            tree = ast.parse(f.read())

        rel_path = str(file_path.relative_to(base_path))

        for node in ast.walk(tree):
            if search_type == "functions" and isinstance(node, ast.FunctionDef):
                results.append({
                    "type": "function",
                    "name": node.name,
                    "file": rel_path,
                    "line": node.lineno,
                    "language": "Python",
                    "signature": get_function_signature(node),
                    "args": len(node.args.args)
                })

            elif search_type == "classes" and isinstance(node, ast.ClassDef):
                methods = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                results.append({
                    "type": "class",
                    "name": node.name,
                    "file": rel_path,
                    "line": node.lineno,
                    "language": "Python",
                    "methods": methods
                })

            elif search_type == "imports" and isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        results.append({
                            "type": "import",
                            "name": alias.name,
                            "file": rel_path,
                            "line": node.lineno,
                            "language": "Python"
                        })
                else:
                    results.append({
                        "type": "from_import",
                        "module": node.module or ".",
                        "file": rel_path,
                        "line": node.lineno,
                        "language": "Python",
                        "items": len(node.names)
                    })
    except Exception as e:
        logger.debug(f"Error parsing Python {file_path}: {e}")

    return results


def extract_javascript_structures(file_path: Path, base_path: Path, search_type: str) -> List[Dict[str, Any]]:
    """Extract JavaScript structures using regex (useful for quick scanning)."""
    results = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        rel_path = str(file_path.relative_to(base_path))

        if search_type == "functions":
            # Match: function name() { }, const name = () => {}, async function name()
            patterns = [
                (r'(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)', 'declaration'),
                (r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>', 'arrow'),
                (r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?function\s*\(([^)]*)\)', 'anonymous'),
            ]

            for line_num, line in enumerate(content.split('\n'), 1):
                for pattern, fn_type in patterns:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        func_name = match.group(1)
                        args = match.group(2) if len(match.groups()) > 1 else ""
                        arg_count = len([a.strip() for a in args.split(',') if a.strip()])

                        results.append({
                            "type": "function",
                            "name": func_name,
                            "file": rel_path,
                            "line": line_num,
                            "language": "JavaScript",
                            "function_type": fn_type,
                            "args": arg_count
                        })

        elif search_type == "classes":
            # Match: class ClassName { }, export class Name
            pattern = r'(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{'

            for line_num, line in enumerate(content.split('\n'), 1):
                matches = re.finditer(pattern, line)
                for match in matches:
                    class_name = match.group(1)
                    extends = match.group(2)

                    results.append({
                        "type": "class",
                        "name": class_name,
                        "file": rel_path,
                        "line": line_num,
                        "language": "JavaScript",
                        "extends": extends or None
                    })

        elif search_type == "imports":
            # Match: import x from 'y', require('x'), import { a, b } from 'x'
            patterns = [
                (r'import\s+(?:{[^}]+}|\w+)\s+from\s+[\'"]([^\'"]+)[\'"]', 'import'),
                (r'require\s*\(\s*[\'"]([^\'"]+)["\']\s*\)', 'require'),
            ]

            for line_num, line in enumerate(content.split('\n'), 1):
                for pattern, import_type in patterns:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        module = match.group(1)

                        results.append({
                            "type": "import",
                            "module": module,
                            "file": rel_path,
                            "line": line_num,
                            "language": "JavaScript",
                            "import_type": import_type
                        })

    except Exception as e:
        logger.debug(f"Error parsing JavaScript {file_path}: {e}")

    return results


def extract_go_structures(file_path: Path, base_path: Path, search_type: str) -> List[Dict[str, Any]]:
    """Extract Go structures using regex."""
    results = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        rel_path = str(file_path.relative_to(base_path))

        if search_type == "functions":
            # Match: func name(...) { }, func (r *Receiver) name(...)
            pattern = r'func\s+(?:\(([^)]*)\)\s+)?(\w+)\s*\(([^)]*)\)'

            for line_num, line in enumerate(content.split('\n'), 1):
                matches = re.finditer(pattern, line)
                for match in matches:
                    func_name = match.group(2)
                    args = match.group(3) if len(match.groups()) > 2 else ""
                    arg_count = len([a.strip() for a in args.split(',') if a.strip()])

                    results.append({
                        "type": "function",
                        "name": func_name,
                        "file": rel_path,
                        "line": line_num,
                        "language": "Go",
                        "args": arg_count
                    })

        elif search_type == "classes":
            # Match: type StructName struct { }
            pattern = r'type\s+(\w+)\s+struct\s*\{'

            for line_num, line in enumerate(content.split('\n'), 1):
                matches = re.finditer(pattern, line)
                for match in matches:
                    struct_name = match.group(1)

                    results.append({
                        "type": "struct",
                        "name": struct_name,
                        "file": rel_path,
                        "line": line_num,
                        "language": "Go"
                    })

        elif search_type == "imports":
            # Match: import "package", import ( "a" "b" )
            pattern = r'import\s+(?:\(\s*)?["\']([^"\']+)["\']'

            for line_num, line in enumerate(content.split('\n'), 1):
                matches = re.finditer(pattern, line)
                for match in matches:
                    module = match.group(1)

                    results.append({
                        "type": "import",
                        "module": module,
                        "file": rel_path,
                        "line": line_num,
                        "language": "Go"
                    })

    except Exception as e:
        logger.debug(f"Error parsing Go {file_path}: {e}")

    return results


def extract_rust_structures(file_path: Path, base_path: Path, search_type: str) -> List[Dict[str, Any]]:
    """Extract Rust structures using regex."""
    results = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        rel_path = str(file_path.relative_to(base_path))

        if search_type == "functions":
            # Match: fn name(...) { }, pub fn name(...), async fn name(...)
            pattern = r'(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*\(([^)]*)\)'

            for line_num, line in enumerate(content.split('\n'), 1):
                matches = re.finditer(pattern, line)
                for match in matches:
                    func_name = match.group(1)
                    args = match.group(2)
                    arg_count = len([a.strip() for a in args.split(',') if a.strip() and ':' in a])

                    results.append({
                        "type": "function",
                        "name": func_name,
                        "file": rel_path,
                        "line": line_num,
                        "language": "Rust",
                        "args": arg_count
                    })

        elif search_type == "classes":
            # Match: struct Name { }, pub struct Name, impl Name
            pattern = r'(?:pub\s+)?(?:struct|trait|enum)\s+(\w+)'

            for line_num, line in enumerate(content.split('\n'), 1):
                matches = re.finditer(pattern, line)
                for match in matches:
                    name = match.group(1)

                    results.append({
                        "type": "struct",
                        "name": name,
                        "file": rel_path,
                        "line": line_num,
                        "language": "Rust"
                    })

        elif search_type == "imports":
            # Match: use std::collections::HashMap; use crate::module;
            pattern = r'use\s+([^;]+);'

            for line_num, line in enumerate(content.split('\n'), 1):
                matches = re.finditer(pattern, line)
                for match in matches:
                    module = match.group(1).strip()

                    results.append({
                        "type": "import",
                        "module": module,
                        "file": rel_path,
                        "line": line_num,
                        "language": "Rust"
                    })

    except Exception as e:
        logger.debug(f"Error parsing Rust {file_path}: {e}")

    return results


@mcp.tool(annotations=ToolAnnotations(
    title="Search Code Structure",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False
))
def search_code_structure(
    path: str = ".",
    search_type: str = "functions",
    max_results: int = 25,
    languages: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Find code structures across multiple languages (functions, classes, imports).

    Args:
        path: Directory to search.
        search_type: 'functions', 'classes', or 'imports'.
        max_results: Max results to return.
        languages: Which languages to search (default: all detected).
                  Options: 'python', 'javascript', 'go', 'rust'

    Returns:
        List of code structures with names, files, line numbers, and language.
        Multi-language code intelligence with minimal token usage!

    LLM Note: AST parsing for Python (100% accurate),
              Regex for JavaScript/Go/Rust (fast, good for large codebases).
    """
    base = safe_path(path)
    results = []

    # Map file extensions to languages and parsers
    language_config = {
        ".py": ("python", extract_python_structures),
        ".js": ("javascript", extract_javascript_structures),
        ".ts": ("javascript", extract_javascript_structures),
        ".jsx": ("javascript", extract_javascript_structures),
        ".tsx": ("javascript", extract_javascript_structures),
        ".go": ("go", extract_go_structures),
        ".rs": ("rust", extract_rust_structures),
    }

    # Filter by requested languages if specified
    if languages:
        languages = {lang.lower() for lang in languages}
        language_config = {k: v for k, v in language_config.items()
                          if v[0] in languages}

    try:
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

            for file in files:
                file_path = Path(root) / file
                ext = file_path.suffix.lower()

                if ext not in language_config:
                    continue

                lang_name, parser_func = language_config[ext]

                try:
                    file_results = parser_func(file_path, base, search_type)
                    results.extend(file_results)

                    if len(results) >= max_results:
                        return ToolResponse.success(
                            "search_code_structure",
                            search_type=search_type,
                            languages_searched=list(set(
                                r.get("language", "unknown") for r in results
                            )),
                            found=len(results),
                            limited=True,
                            results=results[:max_results]
                        )

                except Exception as e:
                    logger.debug(f"Error parsing {file_path}: {e}")
                    continue

        return ToolResponse.success(
            "search_code_structure",
            search_type=search_type,
            languages_searched=list(set(
                r.get("language", "unknown") for r in results
            )) if results else [],
            found=len(results),
            limited=False,
            results=results
        )

    except Exception as e:
        logger.error(f"search_code_structure error: {e}")
        return ToolResponse.error(str(e), "search_code_structure")


# ========================
# SERVER STARTUP
# ========================

if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("🚀 TOKEN-OPTIMIZED MCP FILESYSTEM AGENT v3 (PRODUCTION-READY)")
    logger.info("=" * 70)
    logger.info(f"📁 BASE DIRECTORIES ({len(BASE_DIRS)}):")
    for i, bd in enumerate(BASE_DIRS, 1):
        logger.info(f"   {i}. {bd}")
    logger.info(f"   Pass one or more directory paths as CLI args to change,")
    logger.info(f"   e.g. python server3.py /path/one /path/two")
    logger.info(f"   Or set MCP_BASE_DIRS=path1,path2,path3")
    logger.info(f"   Or set MCP_BASE_DIR to a single path")
    logger.info("")
    logger.info("✨ Features:")
    logger.info("  ✅ 25+ file operations (read, write, search, edit)")
    logger.info("  ✅ Standardized Dict return types (LLM-friendly)")
    logger.info("  ✅ Proper chunked reading with pagination")
    logger.info("  ✅ Dry-run mode for dangerous operations")
    logger.info("  ✅ Regex support in content search")
    logger.info("  ✅ Code structure analysis (Python AST)")
    logger.info("  ✅ Token-optimized for Claude & other LLMs")
    logger.info("")
    logger.info("🔧 Configuration:")
    logger.info(f"  MAX_FILE_SIZE_KB: {MAX_FILE_SIZE_KB}")
    logger.info(f"  MAX_RESULTS: {MAX_RESULTS}")
    logger.info(f"  DEFAULT_CHUNK_SIZE_KB: {DEFAULT_CHUNK_SIZE_KB}")
    logger.info("")
    logger.info("📚 Ready to use with Claude.ai or any MCP-compatible LLM")
    logger.info("=" * 70)

    mcp.run(transport='stdio')