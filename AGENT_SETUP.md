This is official guide to setup Nebius MCP server for AI agents.
Read this document and configure the latest Nebius MCP Server (https://github.com/nebius/mcp-server) locally for specific AI agent.

## 1. Detect the environment
Determine:
- Operating system: macOS, Linux, Windows, or WSL
- Active shell
Run version checks without failing the entire workflow:
```
codex --version
python3 --version
python --version
uv --version
uvx --version
nebius version
```
The Nebius MCP Server requires Python 3.13 or newer.
Stop if version is lower than required and ask user to update python.
Nebius CLI is officially supported on macOS and Linux.
On native Windows, explain that Nebius CLI must run under WSL2 Ubuntu.

## 2. Ensure uv and uvx are installed
If uvx --version succeeds, keep the existing installation.
Otherwise, choose the first suitable method for the detected platform.
### macOS
Prefer Homebrew when it is already installed:
`brew install uv`
If Homebrew is unavailable, use the official standalone installer:
`curl -LsSf https://astral.sh/uv/install.sh | sh`
### Ubuntu, Linux, or WSL
Prefer the official standalone installer:
`curl -LsSf https://astral.sh/uv/install.sh | sh`
When pipx is already installed, this is an acceptable fallback:
`pipx install uv`
Reload the applicable shell configuration or add the installer’s binary directory to PATH for the current session. Do not replace the running agent shell with exec.
Verify both commands:
- `uv --version`
- `uvx --version`

## 3. Install and configure Nebius CLI
First run: `nebius version`
If Nebius CLI is installed but its version is lower than 0.12.65, run: `nebius update` and proceed with the next step.
If it fails, install Nebius CLI on macOS, Ubuntu, or WSL Ubuntu using:
`curl -sSL https://storage.eu-north1.nebius.cloud/cli/install.sh | bash`
Reload the relevant shell configuration or update PATH for the current session without replacing the running agent shell.
Verify: `nebius version`. Stop if the command still cannot be found.

## 4. Ensure a Nebius profile exists
Check the existing configuration:
- `nebius profile list`
- `nebius profile active`
If there is no configured, usable active profile, run:
`nebius profile create`
This command is interactive and may open a browser. Let the user complete authentication and choose the profile, tenant, and other account-specific values. Do not invent identifiers or credentials.
Afterward, verify:
- `nebius profile list`
- `nebius profile active`
Do not display authentication data. Profile names may be reported, but no tokens or private keys.

## 5. Install the Nebius MCP Server for AI agent
Use the correct section for the specific AI agent below.

### Codex
codex mcp add nebius \
  --env SAFE_MODE=true \
  -- uvx \
  --refresh-package nebius-mcp-server \
  "nebius-mcp-server@git+https://github.com/nebius/mcp-server@main"

Verify the configuration: `codex mcp list`
Codex stores user-level MCP configuration in: `~/.codex/config.toml`
Documentation for troubleshooting: https://learn.chatgpt.com/docs/extend/mcp

### Claude Code
claude mcp add \
  --env SAFE_MODE=true \
  --transport stdio \
  --scope user \
  nebius \
  -- uvx \
  --refresh-package nebius-mcp-server \
  "nebius-mcp-server@git+https://github.com/nebius/mcp-server@main"

Verify the configuration: `claude mcp list`
Claude Code stores user-scoped MCP configuration in: `~/.claude.json`
Documentation for troubleshooting: https://docs.anthropic.com/en/docs/claude-code/mcp

### Cursor
Configuration locations:
Global: `~/.cursor/mcp.json`
Project: `.cursor/mcp.json`

Merge the following entry into the top-level mcpServers object:
```
{
  "mcpServers": {
    "nebius": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--refresh-package",
        "nebius-mcp-server",
        "nebius-mcp-server@git+https://github.com/nebius/mcp-server@main"
      ],
      "env": {
        "SAFE_MODE": "true"
      }
    }
  }
}
```
Documentation for troubleshooting: https://cursor.com/docs/mcp

### GitHub Copilot in VS Code
Project configuration location: `.vscode/mcp.json`

Merge the following entry into the top-level servers object:
```
{
  "servers": {
    "nebius": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--refresh-package",
        "nebius-mcp-server",
        "nebius-mcp-server@git+https://github.com/nebius/mcp-server@main"
      ],
      "env": {
        "SAFE_MODE": "true"
      }
    }
  }
}
```
Documentation for troubleshooting: https://code.visualstudio.com/docs/copilot/customization/mcp-servers

### GitHub Copilot CLI
The recommended installation method is the Copilot CLI command:
```
copilot mcp add nebius \
  --env SAFE_MODE=true \
  -- uvx \
  --refresh-package nebius-mcp-server \
  "nebius-mcp-server@git+https://github.com/nebius/mcp-server@main"
```

Configuration locations:
Global: `~/.copilot/mcp-config.json`
Project-local: `.mcp.json`

For manual configuration, merge the following entry into the top-level mcpServers object:
```
{
  "mcpServers": {
    "nebius": {
      "type": "local",
      "command": "uvx",
      "args": [
        "--refresh-package",
        "nebius-mcp-server",
        "nebius-mcp-server@git+https://github.com/nebius/mcp-server@main"
      ],
      "env": {
        "SAFE_MODE": "true"
      }
    }
  }
}
```

### OpenCode
Configuration locations:
Global: `~/.config/opencode/opencode.json`
Project: `opencode.json`

Merge the nebius entry into the top-level mcp object:
```
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "nebius": {
      "type": "local",
      "command": [
        "uvx",
        "--refresh-package",
        "nebius-mcp-server",
        "nebius-mcp-server@git+https://github.com/nebius/mcp-server@main"
      ],
      "environment": {
        "SAFE_MODE": "true"
      },
      "enabled": true
    }
  }
}
```
Documentation for troubleshooting: https://opencode.ai/docs/mcp-servers

### Windsurf
Devin Local is the default agent in current Windsurf versions.
Configuration locations:
Global: `~/.config/devin/mcp_config.json`
Project: `.devin/mcp_config.json`

Windsurf Cascade (legacy) global configuration location: `~/.codeium/windsurf/mcp_config.json`

Merge the following entry into the top-level mcpServers object:
```
{
  "mcpServers": {
    "nebius": {
      "command": "uvx",
      "args": [
        "--refresh-package",
        "nebius-mcp-server",
        "nebius-mcp-server@git+https://github.com/nebius/mcp-server@main"
      ],
      "env": {
        "SAFE_MODE": "true"
      }
    }
  }
}
```
Documentation for troubleshooting: https://docs.windsurf.com/windsurf/cascade/mcp

### Any other MCP-compatible agent
1. Locate its official user-level or project-level MCP configuration file.
2. Confirm that it supports local MCP servers using the STDIO transport.
3. Determine the expected top-level field, such as mcpServers, servers, or mcp.
4. Determine whether the client expects:
  - command and args as separate fields;
  - a single command array;
  - env or environment;
  - an explicit transport type such as stdio or local.
5. Configure the equivalent of:
```
{
  "nebius": {
    "command": "uvx",
    "args": [
      "--refresh-package",
      "nebius-mcp-server",
      "nebius-mcp-server@git+https://github.com/nebius/mcp-server@main"
    ],
    "env": {
      "SAFE_MODE": "true"
    }
  }
}
```
If the agent does not support local STDIO MCP servers, explain that the Nebius MCP Server cannot be configured using this local installation method.

## 6. Final
Ask user to restart the AI agent to connect to the Nebius MCP Server.

### Print scenarios examples for this MCP server:
Get and analyze the documentation for every service:
- How to create a compute instance at Nebius?
- How to create a storage bucket at Nebius?
Execute commands and get results:
- Provide me a list of all storage buckets within the project: project-e00some-cool-project
- Get me a list of the available compute platforms
- Show the details about the compute instance by name: some-cool-instance
