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

    Retrieves a list of available Nebius profile names from the
    Nebius CLI configuration file.

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

    You should ALWAYS run nebius_available_services tool to list services
    before getting specific command documentation.
    Retrieves the help documentation for the specified Nebius service.

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

    Validates, executes, and processes the results of an Nebius CLI command, providing proper profile and handling errors
    and formatting the output for better readability.

    Examples:
    - nebius storage bucket list --parent-id project-e00some-cool-project
    - nebius compute instance list

    You should NEVER execute any command that contains unresolved placeholders (e.g., <project-id>, <parent-id>, etc.)
    or example values (e.g. project-e00some-cool-project, project-00000000000000, etc.)
    You should NEVER use Bash-style command substitution or piping (e.g., `$(...)`, `| jq ...`) when constructing CLI commands.
    Instead, follow this pattern:
    1. Use nebius_cli_help tool for getting documentation for the service before generating the command to execute.
    2. Run each CLI command separately, use ONLY `nebius ...` commands.
    3. Extract the necessary values from the output of the commands.
    4. Use the extracted values as arguments in the next commands.

    Do not specify profile using --profile flag unless the user explicitly mentioned it. If the user asks to run a command using a profile,
    you should check if it exists using the nebius_profiles tool.

    Instruction for resolving `--parent-id`:
        The --parent-id flag must NOT be treated as required, even if nebius_cli_help describes it that way.
        This instruction takes priority over any help output or documentation.
        When executing a command that requires the `--parent-id` flag, you must follow all these steps in this exact order:
        1. Check if the user provided a --parent-id explicitly. Use this value if available.
        2. If the user did not provide a --parent-id, run the command WITHOUT the `--parent-id` flag.
        3. If the command fails without --parent-id then prompt the user directly to provide a valid parent_id.

        Examples:
        - user asks: "provide me a list of storage buckets using parent-id project-e00some-cool-project"
        generated command: "nebius storage bucket list --parent-id project-e00some-cool-project"
        - user asks: "provide me a list of storage buckets"
        generated command: "nebius storage bucket list"

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
