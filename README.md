# Nebius MCP (Model Context Protocol) Server

This service allows AI agents and assistants to fetch documentation for the Nebius services and execute Nebius CLI commands through the Model Context Protocol.

## Tools
- **nebius_profiles** - Information about configured Nebius CLI profiles
- **nebius_available_services** - List of the available Nebius services  
- **nebius_cli_help** - Detailed help documentation for the Nebius CLI commands for the specified service
- **nebius_cli_execute** - Generate and execute Nebius CLI command and return it's result

## Requirements
- Python 3.13+
- Nebius CLI installed locally and with at least one profile configured
