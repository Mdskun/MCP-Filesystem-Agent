# Installation & Setup Guide

Complete setup instructions for all platforms.

---

## Quick Setup (All Platforms)

```bash
# 1. Clone repository
git clone https://github.com/Mdskun/mcp-fs-agent.git
cd mcp-fs-agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run server (pass an allowed directory as an argument)
python server3.py /path/to/your/projects
```

---

## Platform-Specific Setup

### Linux/macOS

#### Install Python

```bash
# Using Homebrew (macOS)
brew install python3.11

# Or using apt (Ubuntu/Debian)
sudo apt-get install python3.11 python3.11-venv
```

#### Create Virtual Environment (Recommended)

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Configure Base Directory

```bash
# Edit ~/.bashrc or ~/.zshrc
export MCP_BASE_DIR="/home/username/projects"

# Or set per session
export MCP_BASE_DIR="/path/to/your/projects"
```

#### Run Server

```bash
python server3.py
```

#### Run as Systemd Service (Optional)

Create `/etc/systemd/system/mcp-fs-agent.service`:

```ini
[Unit]
Description=MCP Filesystem Agent
After=network.target

[Service]
Type=simple
User=your-username
Environment="MCP_BASE_DIR=/home/your-username/projects"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/your-username/mcp-fs-agent/venv/bin/python /home/your-username/mcp-fs-agent/server3.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-fs-agent
sudo systemctl start mcp-fs-agent
sudo systemctl status mcp-fs-agent
```

---

### Windows

#### Install Python

1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer
3. **Important:** Check "Add Python to PATH"
4. Click "Install Now"

#### Create Virtual Environment

```cmd
python -m venv venv
venv\Scripts\activate
```

#### Install Dependencies

```cmd
pip install -r requirements.txt
```

#### Configure Base Directory

```cmd
# Option 1: Permanent (System Variables)
# Search "Environment Variables" → Add:
# Variable: MCP_BASE_DIR
# Value: C:\Users\YourName\Projects

# Option 2: Session only
set MCP_BASE_DIR=C:\Users\YourName\Projects
```

#### Run Server

```cmd
python server3.py
```

#### Run as Windows Service (Optional)

Using `nssm` (Non-Sucking Service Manager):

```cmd
# Download nssm from https://nssm.cc/download
# Extract and add to PATH

nssm install mcp-fs-agent "C:\path\to\venv\Scripts\python.exe" "C:\path\to\server3.py"
nssm set mcp-fs-agent AppEnvironmentExtra MCP_BASE_DIR=C:\Users\YourName\Projects
nssm start mcp-fs-agent
```

---

### Docker

#### Using Docker Compose (Easiest)

```bash
# 1. Clone repository
git clone https://github.com/Mdskun/mcp-fs-agent.git
cd mcp-fs-agent

# 2. Set workspace path (optional)
export MCP_WORKSPACE_PATH="$HOME/projects"

# 3. Run
docker-compose up -d

# 4. Check logs
docker-compose logs -f

# 5. Stop
docker-compose down
```

#### Using Docker Directly

```bash
# 1. Build image
docker build -t mcp-filesystem-agent:latest .

# 2. Run container
docker run -it \
  -e MCP_BASE_DIR=/workspace \
  -v $HOME/projects:/workspace \
  mcp-filesystem-agent:latest

# 3. For background operation
docker run -d \
  --name mcp-fs \
  -e MCP_BASE_DIR=/workspace \
  -v $HOME/projects:/workspace \
  --restart unless-stopped \
  mcp-filesystem-agent:latest
```

#### Docker Multi-Path Setup

```bash
# Create docker-compose override
cat > docker-compose.override.yml << EOF
version: '3.8'
services:
  mcp-filesystem-agent:
    volumes:
      - /path/to/projects:/workspace/projects:ro
      - /path/to/documents:/workspace/documents:ro
      - /data/external:/workspace/external:ro
    environment:
      - MCP_BASE_DIRS=/workspace/projects,/workspace/documents,/workspace/external
EOF

docker-compose up -d
```

---

## Claude Desktop Setup

### macOS

1. Open Claude Desktop
2. Click menu → **Settings** → **Developer**
3. Click **Add MCP Server**
4. Fill in:
   - **Name:** `filesystem-agent`
   - **Command:** `python`
   - **Arguments:** `["/Users/yourname/mcp-fs-agent/server3.py", "/Users/yourname/projects"]`
5. Click **Save**
6. Restart Claude Desktop

### Windows

1. Open Claude Desktop
2. Click menu → **Settings** → **Developer**
3. Click **Add MCP Server**
4. Fill in:
   - **Name:** `filesystem-agent`
   - **Command:** `python`
   - **Arguments:** `["C:\\Users\\YourName\\mcp-fs-agent\\server3.py", "C:\\Users\\YourName\\projects"]`
5. Click **Save**
6. Restart Claude Desktop

### Linux

1. Open Claude Desktop
2. Click menu → **Settings** → **Developer**
3. Click **Add MCP Server**
4. Fill in:
   - **Name:** `filesystem-agent`
   - **Command:** `python`
   - **Arguments:** `["/home/username/mcp-fs-agent/server3.py", "/home/username/projects"]`
5. Click **Save**
6. Restart Claude Desktop

---

## Claude.ai (Web) Setup

### Method 1: Running Locally

1. Start server on your machine:
   ```bash
   python server3.py
   ```

2. In Claude.ai settings, add MCP server:
   - **Type:** Local
   - **Path:** Depends on where you cloned it

### Method 2: Cloud Deployment

Deploy to cloud (AWS, Heroku, etc.) and use cloud URL instead of localhost.

**Note:** Ensure MCP_BASE_DIR is set to accessible location in cloud.

---

## Verification

After setup, verify everything works:

### 1. Check Server Startup

You should see:
```
============================================================
🚀 MCP FILESYSTEM AGENT v3 (PRODUCTION-READY)
============================================================
📁 BASE DIRECTORIES (1):
   1. /path/to/your/projects

✨ 25 file operations ready
============================================================
```

### 2. Test with Python

```python
from pathlib import Path
import subprocess

result = subprocess.run(
    ["python", "server3.py"],
    capture_output=True,
    text=True,
    timeout=5
)

if "MCP FILESYSTEM AGENT" in result.stderr:
    print("✅ Server starts successfully")
else:
    print("❌ Server failed to start")
```

### 3. Test with Claude

In Claude, say:
> "List the files in my workspace"

Claude should respond with file listing using the agent.

---

## Troubleshooting

### Issue: "No module named 'mcp'"

**Solution:**
```bash
pip install -r requirements.txt
# Or update pip first
pip install --upgrade pip
pip install -r requirements.txt
```

### Issue: "Path outside base directory"

**Solution:** Ensure `MCP_BASE_DIR` is set correctly:
```bash
export MCP_BASE_DIR="/actual/path/to/projects"
python server3.py
```

Verify it shows in startup output.

### Issue: "Permission denied" on Linux/macOS

**Solution:**
```bash
chmod +x server3.py
python server3.py
```

### Issue: Docker container exits immediately

**Solution:**
```bash
# Check logs
docker logs mcp-fs

# Run interactively to see errors
docker run -it mcp-filesystem-agent:latest
```

### Issue: Claude doesn't see the server

**Solution:**
1. Verify server is running
2. Check server path is correct
3. Restart Claude completely (not just reload)
4. Verify environment variables are set

### Issue: Out of memory with large files

**Solution:** Use chunked reading:
```
Claude: Read the first chunk of this large file
```

Or configure smaller chunk size in `server3.py`:
```python
DEFAULT_CHUNK_SIZE_KB = 25  # Smaller chunks
```

---

## Multi-Path Configuration

### Simplest: Command-Line Arguments

```bash
python server3.py /home/user/projects /home/user/research /data/shared
```

### Single Path (env var)

```bash
export MCP_BASE_DIR="/home/user/projects"
```

### Multiple Paths (env var)

```bash
export MCP_BASE_DIRS="/home/user/projects,/home/user/research,/data/shared"
```

Then in Claude: Use any path within those directories.

### Claude Desktop with Multi-Path

```json
{
  "mcpServers": {
    "filesystem-agent": {
      "command": "python",
      "args": [
        "/path/to/server3.py",
        "/path/to/projects",
        "/path/to/docs",
        "/data/external"
      ]
    }
  }
}
```

---

## Performance Optimization

### For Large Codebases

1. **Narrow search scope:**
   ```
   Claude: Search for functions in /app/src/ directory only
   ```

2. **Use file extensions:**
   ```
   Claude: Find all Python files with "config" in the name
   ```

3. **Use preview mode:**
   ```
   Claude: Show me the first 50 lines of main.py
   ```

### For Large Files

1. **Use chunked reading:**
   ```
   Claude: Read chunk 0 of this 10MB log file
   ```

2. **Search instead of reading:**
   ```
   Claude: Search for "ERROR" in the log file
   ```

### For Batch Operations

1. **Limit number of files:**
   ```
   Claude: Read these 3 specific files
   ```

---

## Next Steps

- 📖 Read [README.md](README.md) for overview
- 🤝 Check [CONTRIBUTING.md](CONTRIBUTING.md) to contribute
- 🔒 Review [SECURITY.md](SECURITY.md) for security details
- 📝 See [CHANGELOG.md](CHANGELOG.md) for updates

---

## Support

- 📖 Check this guide first
- 🐛 [Open an issue](https://github.com/Mdskun/mcp-fs-agent/issues)
- 💬 Check [existing issues](https://github.com/Mdskun/mcp-fs-agent/issues)
- 🔒 For security: See [SECURITY.md](SECURITY.md)

Happy coding! 🚀
