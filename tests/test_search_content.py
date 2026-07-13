"""
Regression test for the search_content matching bug: a dynamically-created
"Match" object used a zero-argument lambda for .start(), which raised
TypeError when called as a bound method (implicit self). That exception
was silently swallowed by the enclosing try/except and treated as a file
read error, discarding every plain-text match found — so search_content
returned 0 results even when the query string was clearly present.

Run with: pytest tests/test_search_content.py -v
"""
import importlib
import os
import sys
import pytest


@pytest.fixture
def server_module(tmp_path, monkeypatch):
    base_dir = tmp_path / "repo"
    base_dir.mkdir()
    (base_dir / "sample.py").write_text(
        "def hello():\n    return 'world'\n\ndef search_content_demo():\n    pass\n"
    )

    monkeypatch.setattr(sys, "argv", ["server3.py", str(base_dir)])
    monkeypatch.delenv("MCP_BASE_DIR", raising=False)
    monkeypatch.delenv("MCP_BASE_DIRS", raising=False)

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if "server3" in sys.modules:
        del sys.modules["server3"]
    module = importlib.import_module("server3")

    return module


def test_plain_text_search_finds_existing_match(server_module):
    """A substring that is definitely present must be found, not silently
    discarded (this is the exact bug: it used to always return 0)."""
    result = server_module.search_content(query="def search_content_demo")

    assert result["status"] == "success"
    assert result["found"] == 1
    assert result["results"][0]["file"] == "sample.py"
    assert "search_content_demo" in result["results"][0]["match"]


def test_plain_text_search_no_match_returns_zero(server_module):
    """A genuinely absent string should still correctly report 0."""
    result = server_module.search_content(query="this_string_does_not_exist_anywhere")

    assert result["status"] == "success"
    assert result["found"] == 0


def test_regex_search_still_works(server_module):
    """The regex path didn't have the buggy Match object and should be
    unaffected, but verify it wasn't broken by the fix either."""
    result = server_module.search_content(query=r"def \w+\(\)", use_regex=True)

    assert result["status"] == "success"
    assert result["found"] >= 1
