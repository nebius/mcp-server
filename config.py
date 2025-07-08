import os

EXECUTION_TIMEOUT = int(os.environ.get("NEBIUS_MCP_TIMEOUT", "300"))
TRANSPORT = os.environ.get("NEBIUS_MCP_TRANSPORT", "stdio")
NEBIUS_CLI_BIN = os.environ.get("NEBIUS_CLI_BIN", os.getenv("HOME") + "/.nebius/bin/nebius")
NEBIUS_CLI_NAME = os.environ.get("NEBIUS_CLI_NAME", "nebius")

CLI_SYSTEM_SERVICES = {"config", "profile", "help", "update", "version"}
CLI_SERVICE_GROUPS = {"iam", "msp"}

INSTRUCTIONS = """
Nebius MCP Server provides an interface to the Nebius CLI with guidance.
Don't rely on the existing knowledge about the Nebius services.
You should always run nebius_cli_help tool for getting documentation for service specified by user before generating the command to execute.
- Use the nebius_profiles tool to get Nebius CLI available profiles
- Use the nebius_available_services tool to get all available Nebius services
- Use the nebius_available_services tool with service_group parameter to get available Nebius services in the service group
- Use the nebius_cli_help tool to get Nebius CLI documentation for specified service. Never call this tool with a service group name
- Use the nebius_cli_execute tool to run Nebius CLI command based on the documentation and return it's output
"""
