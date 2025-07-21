import os

EXECUTION_TIMEOUT = int(os.environ.get("NEBIUS_MCP_TIMEOUT", "300"))
TRANSPORT = os.environ.get("NEBIUS_MCP_TRANSPORT", "stdio")
NEBIUS_CLI_BIN = os.environ.get("NEBIUS_CLI_BIN", os.getenv("HOME") + "/.nebius/bin/nebius")
NEBIUS_CLI_NAME = os.environ.get("NEBIUS_CLI_NAME", "nebius")
SAFE_MODE = os.environ.get("SAFE_MODE", "true").lower() == "true"

CLI_SYSTEM_SERVICES = {"config", "profile", "help", "update", "version"}
CLI_SERVICE_GROUPS = {"iam", "msp", "storage", "compute"}
CLI_FORBIDDEN_COMMANDS = {
    "get-token",
    "get-access-token",
    "auth-public-key",
    "static-key",
    "--destination-credentials-access-key-secret-access-key",
    "--source-credentials-access-key-secret-access-key",
    "--private-key-file",
}
CLI_FORBIDDEN_ERROR="Using or retrieving tokens is forbidden"
CLI_UNSAFE_COMMANDS = {"update", "delete", "purge", "deactivate"}
CLI_UNSAFE_ERROR = "MCP server is in safe mode and the command contains unsafe words"

INSTRUCTIONS = f"""
Nebius MCP Server provides an interface to the Nebius CLI with guidance.
Don't rely on the existing knowledge about the Nebius services.
You should always run nebius_available_services tool to list all available services.
You should always run nebius_cli_help tool for getting documentation for service specified by user before generating the command to execute.
- Use the nebius_profiles tool to get Nebius CLI available profiles.
- Use the nebius_available_services tool to get all available Nebius services.
- Always use the nebius_available_services tool **before first call** to nebius_cli_help.
- Use the nebius_cli_help tool to get Nebius CLI documentation for specified service.
- Always use the nebius_cli_help tool **before first call** to nebius_cli_execute to build command correctly.
- Use the nebius_cli_execute tool to run Nebius CLI command based on the documentation and return it's output.
- **NEVER** use nebius_cli_execute to obtain any tokens, instead reply with full command and explanation.
If server responds with "{CLI_FORBIDDEN_ERROR}":
- Do **not** retry the command with nebius_cli_execute.
    - Instead instruct user to run it manually.
"""

if SAFE_MODE:
    INSTRUCTIONS += f"""
Tool nebius_cli_execute is running in **safe mode**.
- Do **not** call nebius_cli_execute if command contains any of these words: "{'", "'.join(CLI_UNSAFE_COMMANDS)}".
    - Instead, fenerate instructions to execute a command manually.
If server responds with "{CLI_UNSAFE_ERROR}":
- Do **not** retry the command with nebius_cli_execute
    - Instead instruct user to run it manually.
To disable the safe mode MCP server config must set environment variable `SAFE_MODE=false`.
"""
