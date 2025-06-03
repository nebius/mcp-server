# Nebius MCP Server

This service allows AI agents and assistants to fetch documentation for the Nebius services and execute Nebius CLI commands through the Model Context Protocol.

## Scenarios

There are 2 main scenario for that MCP server:
1. Get and analyze the documentation for every service:
    Examples (queries to the AI agent):
    - How to create a compute instance at Nebius?
    - How to create a storage bucket at Nebius?
2. Execute commands and get results:
    Examples:
    - Provide me a list of all storage buckets within the project: project-e00some-cool-project
    - Get me a list of the available compute platforms
    - Show the details about the compute instance by name: some-cool-instance

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
