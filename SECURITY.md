# Security Policy

This document outlines the security features and best practices for MCP Filesystem Agent.

---

## Security Features

### ✅ Path Validation

All file operations are restricted to configured `BASE_DIR` or `BASE_DIRS`:

```python
# ✅ ALLOWED
read_file("documents/file.txt")

# ❌ BLOCKED
read_file("../../etc/passwd")
read_file("/etc/password")
read_file("~/../../secret.key")
```

**Implementation:** All paths are resolved and validated before operations.

### ✅ Symlink Safety

Symlinks are safely resolved and validated:

```python
# If /tmp/link → /tmp/target/data.txt
# ✅ ALLOWED if /tmp/target is in BASE_DIR
# ❌ BLOCKED if /tmp/target is outside BASE_DIR
```

**Implementation:** Using Path.resolve() which follows symlinks, then validates target.

### ✅ Binary File Protection

Binary files are automatically skipped:

- ✅ Detects `.exe`, `.dll`, `.pdf`, `.zip`, `.png`, `.jpg`, `.so`, `.dylib`, etc.
- ✅ Won't attempt to read as text
- ✅ Returns appropriate error message

**Configuration:** Edit `BINARY_EXTENSIONS` in server3.py to customize.

### ✅ File Size Limits

Prevents memory exhaustion:

```python
MAX_FILE_SIZE_KB = 2000          # 2MB max file
DEFAULT_CHUNK_SIZE_KB = 50       # 50KB chunks
TOTAL_BATCH_SIZE_KB = 5000       # 5MB max batch
```

**Usage:** Automatically enforced, chunked reading available for larger files.

### ✅ Search Limits

Prevents runaway operations:

```python
MAX_RESULTS = 50                 # Max search results
MAX_LINES_TO_SEARCH = 10000      # Stop after 10K lines
```

**Usage:** Returns error if limits exceeded, guides user to narrow search.

### ✅ Input Validation

All user inputs are validated:

- ✅ Path parameters sanitized
- ✅ Regex patterns validated
- ✅ File content checked before modification
- ✅ Numeric parameters bounds checked

---

## Docker Security

### ✅ Non-Root User

Container runs as unprivileged user:

```dockerfile
RUN useradd -m -u 1000 mcp
USER mcp
```

**Benefit:** Even if container is compromised, attacker cannot modify system files.

### ✅ Read-Only Filesystem (Optional)

```bash
docker run --read-only \
  -v /workspace:rw \
  mcp-filesystem-agent
```

**Benefit:** Only /workspace is writable, rest of filesystem is protected.

### ✅ No Privileged Mode

Never run with `--privileged` flag.

### ✅ Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 512M
```

**Benefit:** Prevents DoS attacks consuming all resources.

---

## Network Security

### ✅ Local-Only Operations

- ✅ No network calls made
- ✅ No data sent to external servers
- ✅ No telemetry or reporting
- ✅ Pure file operations only

**Exception:** When connecting to Claude Desktop or claude.ai, only file operation results are sent (not file contents).

---

## Code Execution

### ✅ No Code Execution

This tool **does NOT execute code**:

- ✅ No `eval()` or `exec()`
- ✅ No shell command execution
- ✅ No Python package installation
- ✅ No binary execution

**Safe to use with:** Any files, including untrusted code.

---

## Data Privacy

### ✅ Local Storage

All data stays on your machine:

- ✅ No cloud storage
- ✅ No remote logging
- ✅ No analytics
- ✅ No tracking

### ✅ When Using Claude

When connected to Claude Desktop/Web:

- ✅ Only **operation results** are sent
- ✅ **File contents** stay local
- ✅ **Filenames** may be visible to Claude
- ✅ **Paths** are relative to BASE_DIR

**Example:**
```
User: Search for "password" in config files
Claude receives: "Found 3 matches in config.py (line 23, 45, 67)"
Claude does NOT receive: Full file content
```

---

## Recommendations

### 1. Use Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Benefit:** Isolates dependencies from system Python.

### 2. Limit BASE_DIR Scope

```bash
# ✅ Good
export MCP_BASE_DIR="/home/user/projects"

# ❌ Avoid
export MCP_BASE_DIR="/"
```

**Benefit:** Restricts access to only necessary files.

### 3. Use Read-Only Volumes (Docker)

```bash
docker run -v /source:/workspace:ro \
  mcp-filesystem-agent
```

**Benefit:** Prevents accidental or malicious file modifications.

### 4. Run Behind Firewall (If Cloud-Deployed)

```bash
# Only allow from trusted IPs
sudo ufw allow from 192.168.1.0/24 to any port 8000
```

**Benefit:** Prevents unauthorized access if exposed.

### 5. Use Strong Umask (Linux/macOS)

```bash
umask 0077  # Only user can read files
python server3.py
```

**Benefit:** Protects file contents from other local users.

### 6. Regularly Update Dependencies

```bash
pip install --upgrade -r requirements.txt
```

**Benefit:** Gets security patches for dependencies.

---

## Known Limitations

### ⚠️ NOT Protected Against

- ❌ Malicious input in file operations (mitigated by validation)
- ❌ Compromised system Python (use virtual environment)
- ❌ Local privilege escalation (OS responsibility)
- ❌ Physical access to machine (OS responsibility)
- ❌ Social engineering (user responsibility)

### ⚠️ Requires Care

- ⚠️ MCP_BASE_DIR should not be `/` (user responsibility)
- ⚠️ Don't expose over untrusted networks (user responsibility)
- ⚠️ Docker images should be built from trusted source (user responsibility)

---

## Reporting Security Issues

### DO NOT Open Public Issue

**Do not** report security vulnerabilities as public GitHub issues.

### Report Privately

Email: **manthandsoni@gmail.com**

Include:
- Description of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

**Expected Response:** Within 48 hours acknowledgment, within 7 days fix or security notice.

### Security Advisory Process

1. You report vulnerability privately
2. We investigate and confirm
3. We develop fix
4. We release patch version
5. We publish security advisory
6. You receive credit (if desired)

---

## Responsible Disclosure

We follow responsible disclosure practices:

✅ Private reporting encouraged  
✅ Reasonable disclosure period  
✅ Credit to reporters  
✅ Transparency in security issues  
✅ Regular security audits  

---

## Compliance

### Standards Met

- ✅ OWASP Top 10 secure coding practices
- ✅ CWE-22 prevented (path traversal)
- ✅ CWE-434 mitigated (unrestricted file upload)
- ✅ No hardcoded secrets
- ✅ Input validation on all user inputs

### Future Improvements

- [ ] Formal security audit
- [ ] SBOM (Software Bill of Materials)
- [ ] CVE tracking
- [ ] Automated dependency scanning

---

## Security Checklist

Before deployment, verify:

- [ ] Dockerfile uses non-root user
- [ ] Resource limits are set
- [ ] MCP_BASE_DIR is scoped appropriately
- [ ] No hardcoded secrets in config
- [ ] requirements.txt is up to date
- [ ] No debug mode enabled in production
- [ ] Proper file permissions (umask)
- [ ] Firewall configured (if cloud-deployed)
- [ ] Virtual environment used (if local)
- [ ] PYTHONUNBUFFERED=1 for better error tracking

---

## Security Updates

Versions with security fixes:

| Version | Issue | Fix Date |
|---------|-------|----------|
| 3.0.0 | Initial release | - |

---

## References

- [OWASP: Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
- [CWE-22: Improper Limitation of a Pathname to a Restricted Directory](https://cwe.mitre.org/data/definitions/22.html)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [Python Security](https://python.readthedocs.io/en/latest/library/security_warnings.html)

---

## Support

- 📖 Read [README.md](README.md)
- 📝 Check [INSTALLATION.md](INSTALLATION.md)
- 🐛 Report issues [responsibly](#reporting-security-issues)
- 🤝 Contribute via [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Last Updated:** January 19, 2024

**Policy Version:** 1.0

For questions about security, email: manthandsoni@gmail.com
