# Changelog

All notable changes to MCP Filesystem Agent are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

### v3.1.0 (Planned)
- [ ] Additional language support (C#, Java, C++)
- [ ] Git integration (history, blame)
- [ ] Performance optimizations
- [ ] Better error recovery
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
| 3.0.0 | 2024-01-19 | ✅ Current (Production) |
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

- 📖 [README.md](README.md) - Overview
- 📝 [INSTALLATION.md](INSTALLATION.md) - Setup guide
- 🤝 [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute
- 🔒 [SECURITY.md](SECURITY.md) - Security policy
- 💬 [GitHub Issues](https://github.com/Mdskun/mcp-fs-agent/issues)

---

**Last Updated:** January 19, 2024
