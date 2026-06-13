# Exact Config Files You Need

## For Claude Desktop

### File Location:
```
~/.config/Claude/claude_desktop_config.json
```

### Content (Copy & Paste):
```json
{
  "mcpServers": {
    "filesystem-agent": {
      "command": "python",
      "args": ["/home/hp/Data/Sandbox/mcp-fs-agent/server2.py"],
      "env": {
        "MCP_BASE_DIR": "/home/hp/Data/Sandbox"
      }
    }
  }
}
```

### Instructions:
1. Open file manager
2. Press Ctrl+H to show hidden files
3. Navigate to `.config/Claude/`
4. Open `claude_desktop_config.json` with text editor
5. Replace content with above
6. Save
7. Restart Claude Desktop

---

## For MCPJam

### Create File: `mcp-config.json`

In your project folder:
```bash
cat > mcp-config.json << 'EOF'
{
  "servers": {
    "filesystem-agent": {
      "command": "python",
      "args": ["/home/hp/Data/Sandbox/mcp-fs-agent/server2.py"],
      "env": {
        "MCP_BASE_DIR": "/home/hp/Data/Sandbox"
      }
    }
  }
}
EOF
```

### Run:
```bash
mcpjam start -c mcp-config.json
```

Then open http://localhost:3000 in browser.

---

## For Conda Users (ML310)

### Claude Desktop Config (with Conda):
```json
{
  "mcpServers": {
    "filesystem-agent": {
      "command": "/home/hp/miniconda3/envs/ML310/bin/python",
      "args": ["/home/hp/Data/Sandbox/mcp-fs-agent/server2.py"],
      "env": {
        "MCP_BASE_DIR": "/home/hp/Data/Sandbox"
      }
    }
  }
}
```

Find your conda path:
```bash
conda activate ML310
which python
# Copy the output and use as "command"
```

---

## Validate Your Config

### Check JSON syntax:
```bash
python -m json.tool mcp-config.json
```

If no error, it's valid. If error, fix the JSON and try again.

### Test server directly:
```bash
python /home/hp/Data/Sandbox/mcp-fs-agent/server2.py
```

Should see logs like:
```
2024-XX-XX XX:XX:XX - __main__ - INFO - 🚀 MCP Filesystem Agent starting...
2024-XX-XX XX:XX:XX - __main__ - INFO - 📁 BASE_DIR: /home/hp/Data/Sandbox
```

Then it waits for input (that's normal). Press Ctrl+C to exit.

---

## Quick Checklist

- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Config file created with correct paths
- [ ] Paths point to `/home/hp/Data/Sandbox/mcp-fs-agent/server2.py`
- [ ] MCP_BASE_DIR is `/home/hp/Data/Sandbox`
- [ ] JSON is valid (no trailing commas, proper quotes)
- [ ] Claude Desktop restarted (not just chat window, full app restart)
- [ ] Server test passed: `python server2.py` runs without errors

---

## What Happens When You Connect

1. Claude Desktop/MCPHub connects to server via stdio
2. Server responds with capabilities (20+ tools)
3. Claude sees all tools available
4. You can ask Claude to use any tool
5. Claude calls the tool, server executes, returns result
6. Claude shows result in chat

---

Done! Follow the checklist and you're ready! 🎉
