# Privacy Policy — MCP Filesystem Agent

_Last updated: 2026-07-10_

## Data collection practices

MCP Filesystem Agent does not collect, transmit, or telemetry-report any data
to the author, to Anthropic, or to any third party. The server has no network
client code — it never makes outbound HTTP requests. All it does is read and
write files on the local filesystem, scoped to the directories you configure
via the `MCP_BASE_DIR` / `MCP_BASE_DIRS` environment variables.

## Usage and storage

- All file content the server reads or writes stays on your local machine.
- Nothing is cached, logged to a remote service, or persisted outside the
  files you explicitly ask it to read, write, or modify.
- Local diagnostic logs (timestamps, tool names, error messages) are written
  only to `stderr` on your own machine for debugging; they are never sent
  anywhere and contain no file contents.

## Third-party sharing

None. This server does not integrate with, or send data to, any third-party
service, API, or analytics provider.

## Data retention

The server itself retains nothing between requests — it has no database and
no persistent state beyond the files already on your disk. Any file created,
edited, or deleted through the server persists exactly as any normal file
you'd created yourself, until you remove it.

## Contact information

For privacy questions, security reports, or concerns about this connector,
open an issue at the project repository:
https://github.com/Mdskun/mcp-fs-agent/issues

<!--
  TODO (repo owner): replace the contact line above with a direct email
  address if you'd prefer that over GitHub Issues for private/security reports.
-->
