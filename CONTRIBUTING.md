# Contributing to MCP Filesystem Agent

Thank you for your interest in contributing! This document provides guidelines and instructions.

---

## Code of Conduct

Be respectful, inclusive, and professional. Treat everyone with dignity.

---

## How to Contribute

### 1. Reporting Issues

Found a bug? Have a suggestion?

1. **Check existing issues** - Avoid duplicates
2. **Open a new issue** with:
   - Clear title
   - Detailed description
   - Steps to reproduce (for bugs)
   - Expected vs. actual behavior
   - Your environment (OS, Python version, etc.)

### 2. Feature Requests

Have an idea? We'd love to hear it!

1. **Check existing discussions** - Someone might have suggested it
2. **Open an issue** with:
   - Clear title starting with "[Feature Request]"
   - Description of the feature
   - Why it's useful
   - Example usage (if applicable)

### 3. Code Contributions

### Fork & Clone

```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/mcp-fs-agent.git
cd mcp-fs-agent

# 3. Add upstream remote
git remote add upstream https://github.com/Mdskun/mcp-fs-agent.git
```

### Set Up Development Environment

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install pytest black ruff mypy

# Verify setup
python server3.py  # Should start without errors
```

### Make Changes

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes
# Test thoroughly!

# Format code
black server3.py
ruff check --fix server3.py

# Type check
mypy server3.py

# Commit
git add .
git commit -m "feat: brief description of change"
```

### Push & Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Open Pull Request on GitHub
# - Clear title
# - Link related issues
# - Describe your changes
# - Note any breaking changes
```

---

## Development Guidelines

### Code Style

We follow PEP 8 with Black formatting:

```bash
# Format your code
black server3.py

# Check style
ruff check server3.py
```

### Type Hints

Use type hints for all functions:

```python
def my_function(param: str) -> Dict[str, Any]:
    """Description.
    
    Args:
        param: What this does.
    
    Returns:
        What it returns.
    """
    pass
```

### Docstrings

Follow Google-style docstrings:

```python
def search_code_structure(
    path: str = ".",
    search_type: str = "functions",
    max_results: int = 25
) -> Dict[str, Any]:
    """Find code structures (functions, classes, imports) in files.
    
    Args:
        path: Starting directory to search.
        search_type: Type of structures ('functions', 'classes', 'imports').
        max_results: Maximum number of results to return.
    
    Returns:
        Dictionary with search results and metadata.
    
    Raises:
        ValueError: If search_type is invalid.
    """
    pass
```

### Comments

Write clear, concise comments:

```python
# Good
# Validate path is within BASE_DIRS before operations
validated_path = safe_path(user_input)

# Bad
# Check path
p = Path(user_input)
```

---

## Adding New Tools

### Tool Structure

```python
@mcp.tool(annotations=ToolAnnotations(
    title="My New Tool",
    readOnlyHint=True,       # False if it writes/modifies anything
    destructiveHint=False,   # True if it can overwrite or delete data
    idempotentHint=True,     # True if calling it twice has the same effect as once
    openWorldHint=False      # False for local-only tools (no external services)
))
def my_new_tool(param: str) -> Dict[str, Any]:
    """Short description visible to LLMs.
    
    Args:
        param: Parameter description.
    
    Returns:
        Tool result in standardized format.
    """
    try:
        # Your logic here
        result = process(param)
        
        return ToolResponse.success(
            "my_new_tool",
            result=result,
            metadata="optional info"
        )
    except ValueError as e:
        return ToolResponse.error(str(e), "my_new_tool")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return ToolResponse.error(str(e), "my_new_tool")
```

**Every tool needs annotations** — this isn't optional. The Claude Desktop
connector UI groups tools into "Read-only" vs. write/destructive sections
based on these hints, and marketplace submission requires them.

### Response Format

All tools must return standardized format:

```python
# Success
{
    "status": "success",
    "action": "tool_name",
    "result": "the result",
    "metadata": "optional"
}

# Error
{
    "status": "error",
    "action": "tool_name",
    "error": "error message"
}
```

### Update Tool Count

Update mentions of "22 tools" if you add or remove tools:
- README.md
- server3.py startup message
- claude_config.json
- manifest.json (the `tools` array, plus `compatibility` if relevant)

---

## Testing

### Manual Testing

```bash
# 1. Start server
python server3.py

# 2. Test in Python
python
>>> from server3 import my_new_tool
>>> result = my_new_tool("test")
>>> print(result)

# 3. Test with Claude
# Create a chat and test the tool
```

### Automated Testing

```bash
pytest tests/ -v
pytest tests/ --cov=server3  # Coverage report
```

Existing tests cover path-safety (`test_safe_path.py`), CLI argument
handling (`test_cli_args.py`), and content search (`test_search_content.py`).
Write/edit tools (`write_file`, `replace_text`, `delete_lines`, etc.) don't
have coverage yet — contributions there are especially welcome.

---

## Documentation Updates

When contributing code:

1. **Update docstrings** - Keep descriptions current
2. **Update README.md** - If new features, breaking changes, or setup steps change
3. **Update CHANGELOG.md** - Describe your changes
4. **Update comments** - Explain non-obvious logic

---

## Commit Message Guidelines

Follow conventional commits:

```
feat: add new tool for code analysis
fix: resolve path validation issue
docs: update installation guide
refactor: optimize rglob() performance
test: add unit tests for safe_path()
chore: update dependencies
```

### Format

```
type(scope): subject

body

footer
```

Examples:

```
feat(tools): add search_code_structure tool

Add new tool for analyzing Python code structure using AST parsing.
Supports functions, classes, and imports detection.

Fixes #123
```

---

## Pull Request Process

1. **Update from upstream:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Format code:**
   ```bash
   black server3.py
   ruff check --fix server3.py
   mypy server3.py
   ```

3. **Test changes:**
   ```bash
   python server3.py  # Should start
   # Manual testing in Claude
   ```

4. **Create PR:**
   - Clear title
   - Reference issues with "Fixes #123"
   - Describe changes
   - Note any breaking changes

5. **Code review:**
   - Address feedback
   - Keep commits clean
   - Update from main if needed

---

## Areas for Contribution

### Code

- [ ] Additional language support (C#, Java, etc.)
- [ ] Performance optimizations
- [ ] Error handling improvements
- [ ] Test coverage for write/edit tools (write_file, replace_text, delete_lines, insert_at_line, append_file, create_directory)
- [ ] Async support

### Documentation

- [ ] Video tutorials
- [ ] More examples
- [ ] Architecture documentation
- [ ] API reference documentation
- [ ] Troubleshooting guide expansions

### Integration

- [ ] Ruff integration
- [ ] Git integration
- [ ] Database support
- [ ] API server mode
- [ ] GitHub Actions

### Infrastructure

- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Automated testing
- [ ] Release automation
- [ ] Docker image optimization

---

## Maintainers

The project is maintained by:
- **Manthan** (@Mdskun) - Creator & maintainer

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## Recognition

Contributors will be recognized in:
- CHANGELOG.md
- GitHub contributors page
- Project documentation (if requested)

---

## Questions?

- 📖 Check [README.md](README.md)
- 🐛 Open an issue
- 💬 Check existing discussions

---

Thank you for contributing! 🙏
