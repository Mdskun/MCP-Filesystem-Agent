"""
Regression test for the path-traversal fix in safe_path().

Before the fix, safe_path() used a raw string-prefix check
(str(p).startswith(str(base_resolved))), which incorrectly allowed
access to sibling directories that merely share a name prefix with
the base directory (e.g. base_dir="/x/Data" would wrongly admit
"/x/Data-leak/secret.txt"). The fix uses Path.relative_to(), which is
segment-aware.

Run with: pytest tests/test_safe_path.py -v
"""
import importlib
import os
import sys
import pytest


@pytest.fixture
def server_module(tmp_path, monkeypatch):
    """Import server3 fresh with MCP_BASE_DIR pointed at a temp dir."""
    base_dir = tmp_path / "Data"
    base_dir.mkdir()

    # Sibling directory that shares a string prefix with base_dir but is
    # NOT inside it. This is exactly the case the old code got wrong.
    sibling_dir = tmp_path / "Data-leak"
    sibling_dir.mkdir()
    (sibling_dir / "secret.txt").write_text("should not be reachable")

    monkeypatch.setenv("MCP_BASE_DIR", str(base_dir))
    monkeypatch.delenv("MCP_BASE_DIRS", raising=False)
    # CLI args now take priority over env vars, so clear sys.argv to avoid
    # pytest's own invocation arguments (e.g. "-v", the test file path)
    # being mistaken for directory paths.
    monkeypatch.setattr(sys, "argv", ["server3.py"])

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if "server3" in sys.modules:
        del sys.modules["server3"]
    module = importlib.import_module("server3")

    return module, base_dir, sibling_dir


def test_rejects_sibling_directory_with_shared_prefix(server_module):
    """A directory like 'Data-leak' must NOT be treated as inside 'Data'."""
    module, base_dir, sibling_dir = server_module

    with pytest.raises(ValueError, match="Access denied"):
        module.safe_path(str(sibling_dir / "secret.txt"))


def test_allows_real_subdirectory(server_module):
    """A genuine subdirectory of the base dir must still work."""
    module, base_dir, sibling_dir = server_module

    sub = base_dir / "project" / "file.txt"
    sub.parent.mkdir(parents=True)
    sub.write_text("ok")

    resolved = module.safe_path(str(sub))
    assert resolved == sub.resolve()


def test_allows_base_dir_itself(server_module):
    """The base directory path itself should resolve without error."""
    module, base_dir, sibling_dir = server_module

    resolved = module.safe_path(".")
    assert resolved == base_dir.resolve()


def test_rejects_dotdot_traversal_out_of_base(server_module):
    """Classic ../.. traversal attempts must still be blocked."""
    module, base_dir, sibling_dir = server_module

    with pytest.raises(ValueError, match="Access denied"):
        module.safe_path("../Data-leak/secret.txt")
