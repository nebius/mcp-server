# Nebius MCP (Model Context Protocol) Server

This service allows AI agents and assistants to fetch documentation for the Nebius services and execute Nebius CLI commands through the Model Context Protocol.

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

### Using Claude Desktop

1. Open the Claude Desktop configuration file: Claude -> Settings -> Developer -> Edit Config.

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

## Tools

- **nebius_profiles** - Information about configured Nebius CLI profiles
- **nebius_available_services** - List of the available Nebius services  
- **nebius_cli_help** - Detailed help documentation for the Nebius CLI commands for the specified service
- **nebius_cli_execute** - Generate and execute Nebius CLI command and return the result
