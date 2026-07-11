"""
Tests for CLI-argument base directory configuration, added to match the
official filesystem MCP server's connector config pattern: directories are
passed as positional command-line arguments rather than only via env vars.

Run with: pytest tests/test_cli_args.py -v
"""
import importlib
import os
import sys
import pytest


def _fresh_import():
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if "server3" in sys.modules:
        del sys.modules["server3"]
    return importlib.import_module("server3")


def test_cli_args_become_base_dirs(tmp_path, monkeypatch):
    """Directories passed as CLI args should become BASE_DIRS, like
    `python server3.py /path/one /path/two`."""
    dir_one = tmp_path / "one"
    dir_two = tmp_path / "two"
    dir_one.mkdir()
    dir_two.mkdir()

    monkeypatch.setattr(sys, "argv", ["server3.py", str(dir_one), str(dir_two)])
    monkeypatch.delenv("MCP_BASE_DIR", raising=False)
    monkeypatch.delenv("MCP_BASE_DIRS", raising=False)

    module = _fresh_import()

    assert module.BASE_DIRS == [dir_one.resolve(), dir_two.resolve()]


def test_cli_args_take_priority_over_env_vars(tmp_path, monkeypatch):
    """If both CLI args and env vars are set, CLI args win."""
    cli_dir = tmp_path / "from_cli"
    env_dir = tmp_path / "from_env"
    cli_dir.mkdir()
    env_dir.mkdir()

    monkeypatch.setattr(sys, "argv", ["server3.py", str(cli_dir)])
    monkeypatch.setenv("MCP_BASE_DIR", str(env_dir))

    module = _fresh_import()

    assert module.BASE_DIRS == [cli_dir.resolve()]


def test_no_cli_args_falls_back_to_env_var(tmp_path, monkeypatch):
    """With no CLI args, MCP_BASE_DIR should still work as before."""
    env_dir = tmp_path / "from_env"
    env_dir.mkdir()

    monkeypatch.setattr(sys, "argv", ["server3.py"])
    monkeypatch.setenv("MCP_BASE_DIR", str(env_dir))
    monkeypatch.delenv("MCP_BASE_DIRS", raising=False)

    module = _fresh_import()

    assert module.BASE_DIRS == [env_dir.resolve()]
