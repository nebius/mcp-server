This is official guide to setup Nebius MCP server and Nebius Agent Skills for AI agents.
Read this document and configure the latest Nebius MCP Server (https://github.com/nebius/mcp-server) and Nebius Agent Skills (https://github.com/nebius/skills) locally for specific AI agent.

## Before starting: check Claude environment
If you are Claude, check that you are running locally in Claude Code (terminal or desktop app's Code tab). If not, stop and ask the user to switch to a local Claude Code session and provide this guide there. This check does not apply to other agents.

## 1. Detect the environment
Determine:
- Operating system: macOS, Linux, Windows, or WSL
- Active shell
Run version checks without failing the entire workflow:
```
codex --version
claude --version
python3 --version
python --version
uv --version
uvx --version
nebius version
node --version
npx --version
```
The Nebius MCP Server requires Python 3.13 or newer.
If Python is missing or older, resolve a separate runtime in step 2; do not stop setup or change the user's default Python.
Node.js and npx are only needed to install Nebius Agent Skills for some agents (step 6). Do not stop if they are missing.
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

### Python runtime
Run `uv python find --system --no-python-downloads ">=3.13"` to find a compatible interpreter outside project virtual environments.
If none is found, ask the user to choose, even if they already requested MCP installation:
- **Install Python 3.13 with uv (recommended):** after explicit approval, run `uv python install 3.13` without `--default`, preserving their default Python, then repeat the check.
- **Skip MCP for now:** keep their Python and continue installing the CLI and skills.

If approval is declined or unavailable, or installation fails, defer step 5 and continue steps 3, 4, and 6. Do not bypass the Python requirement or repeatedly request an upgrade.
Reference: https://docs.astral.sh/uv/guides/install-python/

## 3. Install and configure Nebius CLI
First run: `nebius version`
If Nebius CLI is installed but its version is lower than 0.12.277, run: `nebius update` and proceed with the next step.
If it fails, install Nebius CLI on macOS, Ubuntu, or WSL Ubuntu using:
`curl -sSL https://storage.eu-north1.nebius.cloud/cli/install.sh | bash`
Reload the relevant shell configuration or update PATH for the current session without replacing the running agent shell.
Verify: `nebius version`. Stop if the command still cannot be found.

## 4. Configure and verify Nebius login
Check the existing configuration:
- `nebius profile list`
- `nebius profile active`
Reuse the intended existing profile. If no suitable profile exists, run `nebius profile create` interactively and let the user choose the profile, tenant, and other account-specific values. Do not invent identifiers or credentials.
Verify authentication with `nebius --profile "<profile-name>" iam whoami`, replacing the placeholder with the selected profile name. Reuse a valid session; an expired session requires sign-in, not recreating the profile.

For user-account sign-in, let the CLI open the laptop's default external browser. Do not open the authorization URL in an embedded Codex or Claude browser or use browser automation for sign-in.
If automatic opening fails, open the authorization URL using the operating system's default-browser launcher. If the CLI has exited, rerun the same command with `--no-browser` to obtain a fresh URL first. If the launcher also fails, show the URL as plain text for the user to copy into their external browser.
Keep the authentication command running while the user signs in; do not start parallel login attempts. After it completes, verify authentication again with the selected profile. If the agent cannot keep the process running, give the user the exact command to run in their own terminal on the same laptop, then resume verification afterward.
If sign-in is postponed or fails, continue independent installation steps and report account authentication as pending or failed. Do not display tokens or private keys.

## 5. Install the Nebius MCP Server for AI agent
If step 2 found no compatible Python, leave existing MCP configuration unchanged and continue to step 6.
For every `uvx` launch below, insert `--python ">=3.13" --no-python-downloads` before the package arguments, including as separate strings in JSON `args` or `command` arrays. This selects a compatible runtime without automatic Python downloads; if that runtime is later removed, restore it before retrying.
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

### Verify the MCP connection
Use the client's MCP diagnostics or an available MCP Inspector to confirm a connection and list tools using the saved configuration. Configuration listings alone do not prove connectivity. If verification requires a restart, report **configured; connection pending**; if it fails, report the error without credentials and continue to step 6. Report MCP as ready only after successful verification.

## 6. Install Nebius Agent Skills
Nebius Agent Skills (https://github.com/nebius/skills) provide Nebius CLI workflows for inventory, capacity and quotas, provisioning, serverless jobs and endpoints, devlabs, and billing. They are installed independently and do not require the Nebius MCP Server.
They use the Nebius CLI and the profile configured in steps 3 and 4, and follow a three-tier safety model: read, gated write, refuse.
Install Nebius Agent Skills as a required part of setup without asking whether to install them.
If the commands below disagree with the README of https://github.com/nebius/skills, the README wins.

### Claude Code
Register the Nebius marketplace from its GitHub repository, then install its `nebius-cloud` plugin.
```
claude plugin marketplace add https://github.com/nebius/skills.git
claude plugin install nebius-cloud@nebius
```

Verify the installation: `claude plugin list`

### Codex
Register the Nebius marketplace from its GitHub repository, then install its `nebius-cloud` plugin.
```
codex plugin marketplace add https://github.com/nebius/skills.git
codex plugin add nebius-cloud@nebius
```

If `codex plugin add` is not available, ask the user to restart Codex and enable the `nebius-cloud` plugin from the `/plugins` browser.

### Cursor, GitHub Copilot (VS Code and CLI), OpenCode, Windsurf, and any other agent
Requires Node.js 22.20 or newer (`node --version`). Install with the `skills` CLI (https://github.com/vercel-labs/skills):
```
npx skills add nebius/skills --global --agent <agent-id> --yes
```
Use one of these agent IDs: `cursor`, `github-copilot`, `opencode`, `windsurf`. For any other agent, find its ID in https://github.com/vercel-labs/skills/blob/main/docs/agents.md.

If Node.js is unavailable or too old, copy `skills/*` from the https://github.com/nebius/skills repository into the agent's user-level skills directory. Tell the user that this method has no update path.

## 7. Final
Summarize each component’s status: installed, skipped by choice, failed, or deferred. For MCP, report whether connectivity was verified or remains pending. Report account authentication separately; a working MCP connection does not prove account access.

For failed or deferred components, explain the blocker and the specific action needed to continue. Ask once whether the user wants help completing those steps now. Do not repeat installation questions for components they explicitly declined.

If a restart is needed, ask the user to restart the AI agent to connect to configured MCP servers and load installed skills. Explain how to verify any pending connection afterward.

### Print scenarios examples for this MCP server (if configured):
Get and analyze the documentation for every service:
- How to create a compute instance at Nebius?
- How to create a storage bucket at Nebius?
Execute commands and get results:
- Provide me a list of all storage buckets within the project: project-e00some-cool-project
- Get me a list of the available compute platforms
- Show the details about the compute instance by name: some-cool-instance

### Print scenarios examples for Nebius Agent Skills (if installed):
- Can I launch 8×B200 in us-central1-b?
- How much will an H100 VM cost per month?
- Run this container as a batch job on one H100.
