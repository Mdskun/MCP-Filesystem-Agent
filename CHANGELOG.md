# Changelog

All notable changes to MCP Filesystem Agent are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.1.1] - 2026-07-11

### Fixed
- **`search_content` returned 0 results even for text that was definitely
  present.** A dynamically-created "Match" object used a zero-argument
  lambda for `.start()`, which raised `TypeError` when called as a bound
  method (Python auto-passes `self`). That exception was silently swallowed
  by a broad `except Exception: continue`, discarding every plain-text match
  found and abandoning the file mid-scan. Regex-mode searches were
  unaffected. Fixed by removing the dynamic Match object entirely in favor
  of direct position tracking. Covered by `tests/test_search_content.py`.

---

## [3.1.0] - 2026-07-11

### Fixed
- **Security:** `safe_path()` used a raw string-prefix check, which incorrectly
  allowed access to sibling directories sharing a name prefix with an allowed
  directory (e.g. `Data` would wrongly admit `Data-leak`). Replaced with
  `Path.relative_to()`, which is segment-aware. Covered by regression tests
  in `tests/test_safe_path.py`.
- Docker `HEALTHCHECK` previously always passed (`sys.exit(0)` unconditionally);
  now checks the actual server process via `pgrep`.
- Removed unused `fastapi`/`uvicorn` dependencies from `requirements.txt` —
  neither was ever imported by `server3.py`.

### Added
- **CLI-argument configuration:** directories can now be passed directly as
  command-line arguments (`python server3.py /path/one /path/two`), matching
  the connector config pattern used by the official filesystem MCP server.
  Priority order: CLI args → `MCP_BASE_DIRS` → `MCP_BASE_DIR` → default.
  Covered by `tests/test_cli_args.py`.
- **Tool annotations:** all 22 tools now declare `title`, `readOnlyHint`,
  `destructiveHint`, `idempotentHint`, and `openWorldHint`, so hosts (e.g.
  Claude Desktop) can group and gate tools by risk level.
- `manifest.json` (MCPB spec 0.3) for packaging as a Desktop Extension,
  including a `directory`-type, multi-select `allowed_directories` config.
- `PRIVACY.md` and a "Privacy Policy" section in `README.md`.
- `PACKAGING.md` documenting the steps to actually build a `.mcpb` bundle.
- `.mcpbignore` to exclude dev-only files from the packaged bundle.

### Changed
- `mcp` dependency pin updated from the stale `==0.4.0` to `>=1.9,<2`
  (consistent across `requirements.txt`, `manifest.json`, `claude_config.json`).
- README's self-graded "Quality Metrics" (e.g. "9.2/10", "Enterprise Grade")
  replaced with an honest "Quality Notes" section.

---

## [3.0.0] - 2024-01-19

### Added
- **Multi-path support:** Access files from multiple directories with `MCP_BASE_DIRS`
- **Configuration visibility tools:**
  - `get_config()` - View all settings and capabilities
  - `list_allowed_paths()` - See all accessible directories
  - `path_info()` - Get detailed path information
  - `validate_path()` - Check path accessibility before operations
- **Production-grade Docker support:**
  - Security hardening (non-root user)
  - Proper health checks
  - Resource limits in docker-compose
  - Comprehensive logging
- **Enterprise documentation:**
  - Professional README with badges
  - Comprehensive INSTALLATION guide
  - CONTRIBUTING guidelines
  - SECURITY policy
  - CHANGELOG
- **Improved dockerfile:**
  - Non-root user execution
  - Proper health checks
  - Version pinning
  - Security best practices

### Changed
- **Standardized responses:** All tools now return consistent Dict format
- **Updated `safe_path()` function:** Now supports multiple base directories
- **Enhanced `get_base_dir()` tool:** Returns all configured directories
- **Improved error messages:** Clearer, more actionable error text
- **Better logging:** Enhanced startup information and debugging

### Fixed
- Variable naming consistency (BASE_DIR → BASE_DIRS throughout codebase)
- Docstring updates to reflect multi-path support
- Docker health check reliability
- Missing `urllib3` dependency in requirements

### Security
- Non-root Docker execution
- Improved path validation logic
- Better error message sanitization
- Health check implementation

### Performance
- Optimized file traversal in `get_base_dir()`
- Better error handling prevents cascading failures
- Improved resource limits in Docker

---

## [2.0.0] - 2024-01-10

### Added
- **Standardized return types** - All tools return consistent Dict structure
- **Proper chunked pagination** - Handle files larger than context window
- **Dry-run mode** - Preview edits before committing (replace_text)
- **Regex search support** - search_content with use_regex=True
- **Better tool descriptions** - Optimized for LLM understanding
- **Comprehensive docstrings** - Every tool has clear documentation

### Changed
- Tool response format now standardized
- Improved error handling across all tools
- Better context in search results

### Fixed
- Path resolution edge cases
- Unicode handling in file content
- Search performance on large files

---

## [1.0.0] - 2024-01-01

### Added
- Initial release of MCP Filesystem Agent
- 10 core file operations
- Code structure analysis (Python)
- Token-optimized design
- Path security validation
- File size limits
- Binary file protection

### Features
- File reading (preview and full)
- File writing and appending
- File editing (find, insert, delete)
- Directory operations
- Content and file search
- Code analysis

---

## Roadmap

### v3.2.0 (Planned)
- [ ] Test coverage for write/edit tools (write_file, replace_text, delete_lines, etc.)
- [ ] Additional language support (C#, Java, C++)
- [ ] Git integration (history, blame)
- [ ] Performance optimizations
- [ ] Enhanced logging

### v4.0.0 (Future)
- [ ] Async/await support
- [ ] Database query support
- [ ] API server mode
- [ ] Streaming responses
- [ ] Advanced caching

---

## Notes for Contributors

When updating this file:
1. Keep entries grouped by version
2. Use categories: Added, Changed, Fixed, Removed, Security, Deprecated, Performance
3. Keep language clear and actionable
4. Link to related issues/PRs when available
5. Update version number consistently

---

## Version History

| Version | Date | Status |
|---------|------|--------|
| 3.1.1 | 2026-07-11 | ✅ Current |
| 3.1.0 | 2026-07-11 | ⚠️ Superseded (search_content bug) |
| 3.0.0 | 2024-01-19 | ⚠️ Deprecated |
| 2.0.0 | 2024-01-10 | ⚠️ Deprecated |
| 1.0.0 | 2024-01-01 | ⚠️ Deprecated |

---

## Upgrade Guide

### From 2.x to 3.0.0

#### Breaking Changes
- None! 3.0.0 is fully backward compatible

#### New Features
- Multi-path support (optional)
- Configuration visibility tools (new)
- Enhanced Docker support (optional)

#### Migration
No migration needed. Existing code continues to work.

To use new features:
```bash
# Set multiple paths
export MCP_BASE_DIRS="/path/1,/path/2,/path/3"

# Use new visibility tools
Claude: show me my configuration
```

---

## Support

- 📖 [README.md](README.md) - Overview, setup, and configuration
- 🤝 [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute
- 🔒 [SECURITY.md](SECURITY.md) - Security policy
- 💬 [GitHub Issues](https://github.com/Mdskun/mcp-fs-agent/issues)

---

**Last Updated:** July 11, 2026
