# [Beta] Nebius MCP Server

This service allows AI agents and assistants to fetch documentation for the Nebius services and execute Nebius CLI commands through the Model Context Protocol.

## Disclaimer

**Important**: This is a beta version. Use it carefully and at your own risk. There are no guarantees provided regarding stability, safety, or correctness.

In the current implementation, the MCP server allows execution of any Nebius CLI commands, which may lead to destructive and insecure consequences. Always double-check the command suggested by the assistant before executing it. Never use the **Allow always** option for the **nebius_cli_execute** tool.

## Scenarios

There are 2 main scenarios for this MCP server:
1. Get and analyze the documentation for every service

    Examples (queries to the AI agent):
    - How to create a compute instance at Nebius?
    - How to create a storage bucket at Nebius?

2. Execute commands and get results

    Examples:
    - Provide me a list of all storage buckets within the project: project-e00some-cool-project
    - Get me a list of the available compute platforms
    - Show the details about the compute instance by name: some-cool-instance

## Requirements

- Python (version >=3.13) with [uv package manager](https://github.com/astral-sh/uv) installed
- [Nebius CLI](https://docs.nebius.com/cli) (version >=0.12.65) installed locally with at least one profile configured

On macOS, it’s recommended to install `uv` via Homebrew: `brew install uv`.

## Installation

Update to the latest version of Nebius CLI:
```bash
nebius update
```

Use the next command to configure your MCP-compatible client (see examples below):
```bash
uvx --refresh-package nebius-mcp-server "nebius-mcp-server@git+https://github.com/nebius/mcp-server@main"
```

### Restricted actions and safe mode

For safety reasons Nebius MCP server **always forbids** execution of any commands that either accept tokens or access keys as an argument or return them as a result.

**Safe mode**: by default MCP server also does not allow to execute commands that can make "update", "delete" and other commands that can make potentially dangerous changes. We don't recommend changing the default behavior. However it can be controlled using the `SAFE_MODE=true|false` environment variable for the MCP server.

### Using Claude Desktop

0. Install Claude Desktop: https://claude.ai/download

1. Open the Claude Desktop configuration file: *Claude -> Settings -> Developer -> Edit Config*

2. Edit the configuration file to include the Nebius MCP Server:
   ```json
   {
        "mcpServers": {
            "Nebius MCP Server": {
                "command": "uvx",
                "args": [
                    "--refresh-package",
                    "nebius-mcp-server",
                    "nebius-mcp-server@git+https://github.com/nebius/mcp-server@main"
                ],
                "env": {}
            }
        }
    }
   ```

3. Restart Claude Desktop:
   - After restarting, click "Search and tools" icon in the bottom left corner of the input box
   - You should see Nebius MCP Server is available for use

### Using VSCode Copilot

0. Ensure you have the Copilot extension installed and are logged in

1. Open the Command Palette (Cmd+Shift+P / Ctrl+Shift+P) and run **mcp: Add Server**

2. Choose `Command (stdio)` and enter the following command: `uvx --refresh-package nebius-mcp-server "nebius-mcp-server@git+https://github.com/nebius/mcp-server@main"`

3. Open the Chat panel and select **Agent** mode
    - You will now see the new MCP and its available tools by clicking the  :hammer_and_wrench:  button

## Tools

- **nebius_profiles** - Information about configured Nebius CLI profiles
- **nebius_available_services** - List of the available Nebius services
- **nebius_cli_help** - Detailed help documentation for the Nebius CLI commands for the specified service
- **nebius_cli_execute** - Generate and execute Nebius CLI command and return the result

## Trademarks

"Model Context Protocol", "MCP", and the MCP logo are trademarks of Anthropic.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Nebius B.V.
