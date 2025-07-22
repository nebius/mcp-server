import logging
import sys
from contextlib import asynccontextmanager

from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field

from nebius_mcp_server.config import INSTRUCTIONS
from nebius_mcp_server.cli import (
    ServiceHelpResult,
    ServiceDescription,
    CommandResult,
    CommandExecutionError,
    check_cli_installed,
    get_profiles,
    get_available_services,
    describe_service,
    execute_cli_command,
)

logger = logging.getLogger("nebius-mcp-server")

async def run_startup_checks():
    if not await check_cli_installed():
        logger.error("Nebius CLI is not installed. Please install Nebius CLI or provider executable via NEBIUS_CLI_BIN env variable.")
        sys.exit(1)
    logger.info("Nebius CLI is installed and available.")

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    await run_startup_checks()
    yield

mcp = FastMCP(
    "Nebius MCP Server",
    instructions=INSTRUCTIONS,
    capabilities={"resources": {}},
    lifespan=app_lifespan,
)

@mcp.tool()
async def nebius_profiles() -> dict:
    """Get the available Nebius CLI profiles.

    Retrieves a list of available Nebius profile names from the Nebius CLI configuration file.
    If the user does not explicitly mention profiles, do not call this tool under any circumstances.

    Returns:
        Dictionary with profiles information
    """
    return await get_profiles()

@mcp.tool()
async def nebius_available_services() -> list[ServiceDescription]:
    """Get the available Nebius services.

    Retrieves a list of available Nebius services including nested services.

    Returns:
        List of ServiceDescription with available services
    """
    return await get_available_services()

@mcp.tool()
async def nebius_cli_help(
    service: str = Field(description="Nebius service (e.g., applications, audit, compute, iam project, msp mlflow)"),
    ctx: Context | None = None
) -> ServiceHelpResult:
    """Get the Nebius CLI command documentation for the specified service.

    Retrieves the help documentation for the specified Nebius service.

    You should ALWAYS run nebius_available_services tool to list services before getting specific command documentation.
    You must NEVER call this tool with a service that has nested sub-services (e.g., 'iam', 'storage').

    Examples:
    - Valid: service='applications'
    - Valid: service='iam project'
    - Valid: service='storage bucket'
    - Invalid (returns error): service='storage'
    - Invalid (returns error): service='iam'

    Returns:
        CommandHelpResult containing the proper documentation for the service
    """
    logger.info("Getting CLI help for '%s'", service)
    try:
        if ctx:
            await ctx.info(f"Fetching help for Nebius {service}")
        return await describe_service(service)
    except Exception as e:
        logger.error(f"Error in nebius_cli_help: {e}")
        return ServiceHelpResult(help_text=f"Error retrieving help: {str(e)}")

@mcp.tool()
async def nebius_cli_execute(
    command: str = Field(description="Complete Nebius CLI command to execute"),
    ctx: Context | None = None,
) -> CommandResult:
    """Execute Nebius CLI command.

    Validates, executes, and processes the results of an Nebius CLI command, handling errors
    and formatting the output for better readability.

    You MUST NEVER execute any command that includes bash-style command substitution or piping such as `$(...)`, `| jq ...`, etc.

    Required Execution Pattern:
    1. Use nebius_cli_help tool for getting documentation for the service before generating the command to execute.
    2. Run each CLI command separately, use ONLY `nebius ...` commands.
    3. Extract the necessary values from the output of the commands.
    4. Use the extracted values as arguments in the next commands.

    Instruction for resolving `--parent-id`:
        This instruction takes priority over any help output or documentation.
        The `--parent-id` flag is required, but you CAN OMIT it and CLI will execute command using default.
        When executing a command that requires the `--parent-id` flag, you must follow all these steps in this exact order:
        1. Check if the **user provided** parent id explicitly. Use this value if available.
        2. If not provided you **must omit** the flag: **run without** `--parent-id`.
        3. Only if the command **fails without** flag then prompt the user directly to provide a valid --parent-id.

    Examples (only valid when using user-provided or extracted values):
    - User asks: "Provide me a list of storage buckets using parent-id project-abc123"
      → Correct command: "nebius storage bucket list --parent-id project-abc123"
    - User asks: "Provide me a list of storage buckets"
      → Correct command: "nebius storage bucket list"
      → DO NOT use without value: "nebius storage bucket list --parent-id"
      → DO NOT use placeholders: "nebius storage bucket list --parent-id <parent-id>"
      → DO NOT invent values: "nebius storage bucket list --parent-id project-abc123"

    Never invent values like `project-example123`. Only use values provided by the user or retrieved from previous commands.

    Returns:
        CommandResult containing output and status
    """
    logger.info(f"Executing command: {command}")

    try:
        result = await execute_cli_command(command)

        if result["status"] == "success":
            if ctx:
                await ctx.info("Command executed successfully")
        else:
            if ctx:
                await ctx.warning("Command failed")

        return CommandResult(status=result["status"], output=result["output"])
    except CommandExecutionError as e:
        logger.warning(f"Command execution error: {e}")
        return CommandResult(status="error", output=f"Command execution error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in nebius_cli_execute: {e}")
        return CommandResult(status="error", output=f"Unexpected error: {str(e)}")
