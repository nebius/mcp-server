# Nebius MCP Server

This service allows AI agents and assistants to fetch documentation for the Nebius services and execute Nebius CLI commands through the Model Context Protocol.

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

## Disclaimer

In the current implementation, the MCP server allows execution of any Nebius CLI commands, which may lead to destructive and insecure consequences. Always double-check the command suggested by the assistant before executing it. Never use the **Allow always** option for the **nebius_cli_execute** tool.

## Requirements

- Python (version >=3.13) with [uv package manager](https://github.com/astral-sh/uv) installed
- [Nebius CLI](https://docs.nebius.com/cli) (version >=0.12.65) installed locally with at least one profile configured

## Installation

```bash
// update to the latest version of Nebius CLI
nebius update

// clone mcp server repository
cd ~/.nebius
git clone git@github.com:nebius/mcp-server.git
```

Use the next command to configure your MCP-compatible client:
```bash
uv run --with fastmcp fastmcp run ~/.nebius/mcp-server/server.py
```

### Using Claude Desktop

0. Install Claude Desktop: https://claude.ai/download

1. Open the Claude Desktop configuration file: *Claude -> Settings -> Developer -> Edit Config*

2. Edit the configuration file to include the Nebius MCP Server:
   ```json
   {
        "mcpServers": {
            "Nebius MCP Server": {
                "command": "uv",
                "args": [
                    "run",
                    "--with",
                    "fastmcp",
                    "fastmcp",
                    "run",
                    "~/.nebius/mcp-server/server.py"
                ]
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

2. Choose `stdio` and and enter the following command: `uv run --with fastmcp fastmcp run ~/.nebius/mcp-server/server.py`

3. Open the Chat panel and select **Agent** mode
    - You will now see the new MCP and its available tools by clicking the  :hammer_and_wrench:  button

## Tools

- **nebius_profiles** - Information about configured Nebius CLI profiles
- **nebius_available_services** - List of the available Nebius services  
- **nebius_cli_help** - Detailed help documentation for the Nebius CLI commands for the specified service
- **nebius_cli_execute** - Generate and execute Nebius CLI command and return the result
