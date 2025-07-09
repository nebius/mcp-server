import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field
from config import (
    TRANSPORT,
    INSTRUCTIONS,
)

from cli import (
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler(sys.stderr)])
logger = logging.getLogger("nebius-mcp-server")

def run_startup_checks():
    if not asyncio.run(check_cli_installed()):
        logger.error("Nebius CLI is not installed. Please install Nebius CLI or provider executable via NEBIUS_CLI_BIN env variable.")
        sys.exit(1)
    logger.info("Nebius CLI is installed and available.")

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    run_startup_checks()
    yield

mcp = FastMCP(
    "Nebius MCP Server",
    instructions=INSTRUCTIONS,
    capabilities={"resources": {}},
    lifespan=app_lifespan,
)

@mcp.tool()
async def nebius_profiles(ctx: Context | None = None) -> dict:
    """Get the available Nebius CLI profiles.

    Retrieves a list of available Nebius profile names from the
    Nebius CLI configuration file.

    Returns:
        Dictionary with profiles information
    """
    return await get_profiles()

@mcp.tool()
async def nebius_available_services(
    service_group: str | None = Field(default=None, description="Nebius service group (e.g., iam, msp)"),
    ctx: Context | None = None
) -> list[ServiceDescription]:
    """Get the available Nebius services.

    Retrieves a list of available Nebius services and service groups.
    If service_group is specified - returns services in this group.

    Returns:
        List of ServiceDescription with available services and service groups
    """
    return await get_available_services(service_group)

@mcp.tool()
async def nebius_cli_help(
    service: str = Field(description="Nebius service (e.g., applications, audit, compute, iam project, msp mlflow)"),
    ctx: Context | None = None
) -> ServiceHelpResult:
    """Get the Nebius CLI command documentation for the specified service.

    Retrieves the help documentation for the specified Nebius service.

    Returns:
        CommandHelpResult containing the proper documentation for the service
    """

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

    Validates, executes, and processes the results of an Nebius CLI command, providing proper profile and handling errors
    and formatting the output for better readability.

    Examples:
    - nebius storage bucket list --parent-id project-e00...
    - nebius compute instance list --parent-id project-e00...

    You should ALWAYS run nebius_cli_help tool for getting documentation for the service before generating the command to execute.

    Do not specify profile using --profile flag unless the user explicitly mentioned it. If the user asks to run a command using a profile,
    you should check if it exists using the nebius_profiles tool.

    You should NEVER specify --parent-id flag for the command unless the user has explicitly mentioned parent-id value.

    Examples:
    - user asks: "provide me a list of storage buckets using testing profile"
      generated command: "nebius storage bucket list --profile testing"
    - user asks: "provide me a list of storage buckets using parent-id project-e00some-cool-project"
      generated command: "nebius storage bucket list --parent-id project-e00some-cool-project"

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

if __name__ == "__main__":
    from config import TRANSPORT

    if TRANSPORT not in ("stdio", "sse"):
        logger.error(f"Invalid transport protocol: {TRANSPORT}. Must be 'stdio' or 'sse'")
        sys.exit(1)

    logger.info(f"Starting server with transport protocol: {TRANSPORT}")
    mcp.run(transport=TRANSPORT)
