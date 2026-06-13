# Setup server2.py with MCPHub / MCPJam for Testing

MCPHub and MCPJam are web-based tools for testing MCP servers without needing Claude Desktop.

## Quick Start

### Option 1: Using MCPHub (Web UI)

1. Go to https://mcphub.io (or your MCPHub instance)

2. Click "Add New MCP Server"

3. Fill in the form:
   ```
   Name: filesystem-agent
   Command: python
   Arguments: /home/hp/Data/Sandbox/mcp-fs-agent/server2.py
   Environment Variables:
     MCP_BASE_DIR=/home/hp/Data/Sandbox
   ```

4. Click "Connect"

5. The UI will show all available tools and you can call them directly

### Option 2: Using MCPJam CLI

Install MCPJam (if not already installed):
```bash
pip install mcpjam
```

Create a config file `mcp-config.json`:
```json
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
```

Start MCPJam:
```bash
mcpjam start -c mcp-config.json
```

MCPJam will give you a URL to access the testing interface (usually http://localhost:3000)

### Option 3: Direct Stdio Test

Test the server directly:
```bash
cd /home/hp/Data/Sandbox/mcp-fs-agent
python server2.py
```

You can now send MCP protocol messages via stdin. The server reads from stdin and outputs to stdout.

### Test Message Example:

Send this JSON (followed by Enter):
```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0"}}}
```

The server should respond with its capabilities and available tools.

## Testing Tools Directly

Once connected via MCPHub/MCPJam, you can test these:

### Test 1: Health Check
```
Method: ping()
Expected: "pong"
```

### Test 2: List Directory
```
Method: list_directory
Parameters: {"path": "mcp-fs-agent"}
Expected: List of files (server2.py, test.py, requirements.txt, etc)
```

### Test 3: File Summary (token-efficient)
```
Method: file_summary
Parameters: {"path": "mcp-fs-agent/server2.py"}
Expected: File info with line count, size, first 10 lines
```

### Test 4: Search Files
```
Method: search_files
Parameters: {"query": "server", "path": "."}
Expected: Files containing "server" in name
```

### Test 5: Read File
```
Method: read_file
Parameters: {"path": "mcp-fs-agent/requirements.txt"}
Expected: Full file content
```

### Test 6: Search Code Structure
```
Method: search_code_structure
Parameters: {"path": "mcp-fs-agent", "search_type": "functions"}
Expected: List of functions in Python files
```

### Test 7: Write File
```
Method: write_file
Parameters: {
  "path": "mcp-fs-agent/test_output.txt",
  "content": "Hello from MCP test!"
}
Expected: "✓ File written: mcp-fs-agent/test_output.txt"
```

## Troubleshooting

### Server not starting?
Check Python path:
```bash
python --version
which python
```

### Missing tools?
Verify server2.py has all @mcp.tool() decorators. Count them:
```bash
grep -c "@mcp.tool()" server2.py
```
Should be 20+

### Conda environment?
Make sure ML310 is activated:
```bash
conda activate ML310
which python
# Should show path ending in /ML310/bin/python
```

### Permission denied?
Fix permissions:
```bash
chmod +x /home/hp/Data/Sandbox/mcp-fs-agent/server2.py
```

### Can't find BASE_DIR?
Set environment variable explicitly:
```bash
export MCP_BASE_DIR="/home/hp/Data/Sandbox"
python server2.py
```

## Live Testing Scenario

1. Start server with MCPJam
2. In MCPJam interface, call `list_directory` with path="mcp-fs-agent"
3. Get list of files
4. Call `read_file` with path="mcp-fs-agent/server2.py"
5. See the source code
6. Call `search_code_structure` with path="mcp-fs-agent", search_type="functions"
7. See all available functions
8. Call `write_file` to test writing
9. Call `read_file` again to verify it was written

## Connecting to Claude API

If you want to test with Claude API directly (not Desktop):

```python
import anthropic

client = anthropic.Anthropic()

# Call Claude with MCP tools
response = client.messages.create(
    model="claude-opus-4-20250805",
    max_tokens=1024,
    tools=[
        {
            "type": "mcp",
            "name": "filesystem-agent",
            "uri": "stdio:///home/hp/Data/Sandbox/mcp-fs-agent/server2.py"
        }
    ],
    messages=[
        {
            "role": "user",
            "content": "List files in the mcp-fs-agent directory"
        }
    ]
)

print(response)
```

## Summary

- **MCPHub**: Web-based testing, easiest for beginners
- **MCPJam**: CLI-based testing, scriptable
- **Direct stdio**: Raw testing, for debugging
- **Claude Desktop**: Production use with full integration
- **Claude API**: Programmatic use in Python

Start with MCPHub for fastest results! 🚀
