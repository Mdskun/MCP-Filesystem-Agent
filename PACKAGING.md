# Packaging as a .mcpb bundle

This repo is set up for MCPB packaging (`manifest.json`, `.mcpbignore`), but
turning it into an actual `.mcpb` file — and submitting it to the Connectors
Directory as a Desktop Extension — requires running commands on your own
machine. These steps can't be done through this filesystem-only tool, so
here's exactly what to run:

## 1. Bundle the `mcp` dependency

The manifest declares `server.type: "python"`, which means all dependencies
must ship inside the bundle (end users should not need to run `pip install`).
From the repo root:

```bash
pip install "mcp>=1.9,<2" --target=server/lib
```

Then add `PYTHONPATH` pointing at `server/lib` to the `mcp_config.env` block
in `manifest.json`, e.g.:

```json
"env": {
  "MCP_BASE_DIR": "${user_config.base_dir}",
  "PYTHONPATH": "${__dirname}/server/lib"
}
```

(Alternative: switch `server.type` to `"uv"` — manifest_version 0.4+ — and
declare the `mcp` dependency in a `pyproject.toml` instead. This lets the
host app manage the Python environment instead of vendoring `server/lib`
yourself, and avoids bundling compiled dependencies. See the MCPB spec's
"UV Runtime" section for the exact layout.)

## 2. Install the MCPB CLI

```bash
npm install -g @anthropic-ai/mcpb
```

## 3. Validate the manifest

```bash
mcpb validate manifest.json
```

Fix anything it flags before continuing.

## 4. Pack the bundle

```bash
mcpb pack .
```

This produces a `.mcpb` file (a zip archive) in the current directory.

## 5. Add an icon (optional but recommended)

The manifest has no `icon` field yet because there's no `icon.png` in the
repo. A 128x128 (or larger, square) PNG dropped at the repo root, referenced
as `"icon": "icon.png"` in `manifest.json`, will show up in the extension
list and directory listing.

## 6. Submit

Desktop extensions use a separate submission form from the Connectors
Directory portal (the portal is for remote HTTPS servers only). Have ready:
the `.mcpb` file, your documentation URL, privacy policy URL (already have:
`PRIVACY.md`), and an icon.
