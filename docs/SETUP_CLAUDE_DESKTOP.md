# Setup server2.py with Claude Desktop

## Step 1: Find Claude Desktop Config File

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Mac:**
```
~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

## Step 2: Edit claude_desktop_config.json

Open the config file and add your MCP server. Here's the template:

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

### Full Example Config:

```json
{
  "mcpServers": {
    "filesystem-agent": {
      "command": "python",
      "args": ["/home/hp/Data/Sandbox/mcp-fs-agent/server2.py"],
      "env": {
        "MCP_BASE_DIR": "/home/hp/Data/Sandbox"
      }
    },
    "other-server": {
      "command": "python",
      "args": ["/path/to/other/server.py"]
    }
  }
}
```

## Step 3: Install Dependencies

```bash
cd /home/hp/Data/Sandbox/mcp-fs-agent
pip install -r requirements.txt
```

## Step 4: Restart Claude Desktop

Close and reopen Claude Desktop completely. The MCP will auto-connect.

## Step 5: Test It Out

In Claude Desktop chat, ask:
```
What files are in the mcp-fs-agent directory?
```

Or use tools directly:
```
Use the ping tool to verify the server is running
```

## Troubleshooting

### Server won't connect?
1. Check config file syntax (use JSON validator)
2. Verify file path is correct
3. Make sure Python is in PATH: `python --version`

### Tools not appearing?
- Restart Claude Desktop completely
- Clear cache if needed

### Permission issues?
Make sure the directory is readable:
```bash
ls -la /home/hp/Data/Sandbox/mcp-fs-agent/
```

### Using Conda Python?

If you use conda, specify the full Python path:

```json
{
  "command": "/home/hp/miniconda3/envs/ML310/bin/python",
  "args": ["/home/hp/Data/Sandbox/mcp-fs-agent/server2.py"]
}
```

Find your conda python path:
```bash
conda activate ML310
which python
```

## Available Tools (20+)

**File Operations:**
- `list_directory` - List files in folder
- `read_file` - Read full file
- `write_file` - Create/overwrite file
- `append_file` - Add to file
- `create_directory` - Make folder

**Search:**
- `search_files` - Find by name
- `search_content` - Find text in files
- `search_files_by_ext` - Find by extension

**Edit:**
- `replace_text` - Find & replace
- `insert_at_line` - Insert at line
- `delete_lines` - Delete lines

**Code:**
- `search_code_structure` - Find Python functions/classes/imports

**Utilities:**
- `file_summary` - Quick file info
- `get_tree` - Directory structure
- `ping` - Health check

## Example Prompts

```
Show me all Python files in the mcp-fs-agent directory
```

```
Find all function definitions in server2.py
```

```
What does requirements.txt contain?
```

```
List the directory structure of the mcp-fs-agent folder
```

Done! 🚀
