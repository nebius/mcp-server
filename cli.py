import asyncio
import logging
import shlex
import re
from typing import TypedDict, List

from config import (
    EXECUTION_TIMEOUT,
    NEBIUS_CLI_BIN,
    NEBIUS_CLI_NAME,
    SAFE_MODE,
    CLI_SYSTEM_SERVICES,
    CLI_SERVICE_GROUPS,
    CLI_FORBIDDEN_COMMANDS,
    CLI_FORBIDDEN_ERROR,
    CLI_UNSAFE_COMMANDS,
    CLI_UNSAFE_ERROR,
)

logger = logging.getLogger(__name__)

class CommandHelpResult(TypedDict):
    """Type definition for the command help results."""

    help_text: str

class ServiceDescription(TypedDict):
    """Type definition for service description."""
    name: str
    description: str | None
    nested_services: list['ServiceDescription']

class ServiceHelpResult(TypedDict):
    """Type definition for the service help results."""

    help_text: str

class CommandResult(TypedDict):
    """Type definition for command execution results."""

    status: str
    output: str

class CommandExecutionError(Exception):
    """Exception raised when a command fails to execute.

    This exception is raised when there's an error during command
    execution, such as timeouts or subprocess failures.
    """

    pass

async def check_cli_installed() -> bool:
    logger.info("Checking nebius cli installed at: " + NEBIUS_CLI_BIN)
    try:
        cmd_parts = [NEBIUS_CLI_BIN, "--help"]
        process = await asyncio.create_subprocess_exec(*cmd_parts, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.communicate()
        return process.returncode == 0
    except Exception:
        return False

async def get_profiles() -> dict:
    logger.info("Getting cli profiles")
    try:
        cmd_parts = [NEBIUS_CLI_BIN, "profile", "list"]
        process = await asyncio.create_subprocess_exec(*cmd_parts, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"CLI error: {stderr.decode().strip()}")
            return {}

        output = stdout.decode().strip()
        profiles = {}

        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue

            if "[default]" in line:
                name = line.replace("[default]", "").strip()
                is_active = True
            else:
                name = line
                is_active = False

            profiles[name] = {
                "name": name,
                "is_active": is_active,
            }

        return profiles

    except Exception:
        logger.exception("Failed to get CLI profiles")
        return {}

async def get_available_services() -> list[ServiceDescription]:
    logger.info("Getting available root services")
    return await _get_available_services()

async def _get_available_services(command: str | None = None) -> list[ServiceDescription]:
    if command:
        cmd_parts = [NEBIUS_CLI_BIN, "help", command]
    else:
        cmd_parts = [NEBIUS_CLI_BIN, "--help"]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd_parts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        help_text = stdout.decode()

        if process.returncode != 0:
            logger.error(f"CLI error: {stderr.decode().strip()}")
            return []

        return await _parse_available_services(help_text, command)

    except Exception:
        logger.exception("Failed to get available services")
        return []

async def _parse_available_services(help_text: str, parent_name: str | None = None) -> list[ServiceDescription]:
    match = re.search(
        r"^Available Commands:\n"
        r"((?:^(?:[ \t]+.+\n|\n))+)",
        help_text,
        flags=re.MULTILINE,
    )
    if not match:
        logger.error(f"CLI unexpected output: {help_text.strip()}")
        return []

    block = match.group(1)
    cmds = []
    for line in block.splitlines():
        if re.match(r"^[ \t]{1,2}\w+", line):
            chunks = line.strip().split()

            name = chunks[0]
            if name in CLI_SYSTEM_SERVICES:
                continue

            name = f'{parent_name} {name}' if parent_name else name
            description = " ".join(chunks[1:]).strip()
            if not description:
                description = None

            services = []
            if name in CLI_SERVICE_GROUPS:
                services = await _get_available_services(name)

            cmds.append(ServiceDescription(name=name, description=description, nested_services=services))

    return cmds


async def execute_cli_command(command: str) -> CommandResult:
    logger.debug(f"Executing Nebius CLI command: {command}")

    try:
        cmd_parts = shlex.split(command)
        if cmd_parts[0] != NEBIUS_CLI_NAME:
            logger.error(f"Command does not start with {NEBIUS_CLI_NAME}: {command}")
            return CommandResult(status="error", output="Wrong command")
        cmd_parts[0] = NEBIUS_CLI_BIN

        forbidden_parts = [x for x in cmd_parts[1:] if x in CLI_FORBIDDEN_COMMANDS]
        if forbidden_parts:
            forbidden_parts = ", ".join(forbidden_parts)
            logger.error("The command contains forbidden parts: %s", forbidden_parts)
            return CommandResult(
                status="error",
                output=f"{CLI_FORBIDDEN_ERROR}: {forbidden_parts}, provide manual instructions instead."
            )

        unsafe_parts = [x for x in cmd_parts[1:] if x in CLI_UNSAFE_COMMANDS]
        if SAFE_MODE and unsafe_parts:
            unsafe_parts = ", ".join(unsafe_parts)
            logger.error("Safe mode is on and the command contains unsafe parts: %s", unsafe_parts)
            return CommandResult(
                status="error",
                output=f"{CLI_UNSAFE_ERROR}: {unsafe_parts}, provide manual instructions instead."
            )

        process = await asyncio.create_subprocess_exec(
            *cmd_parts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), EXECUTION_TIMEOUT)
            logger.debug(f"Command completed with return code: {process.returncode}")
        except asyncio.TimeoutError as timeout_error:
            logger.warning(f"Command timed out after {EXECUTION_TIMEOUT} seconds: {command}")
            try:
                process.kill()
            except Exception as e:
                logger.error(f"Error killing process: {e}")
            raise CommandExecutionError(f"Command timed out after {EXECUTION_TIMEOUT} seconds") from timeout_error

        stdout_str = stdout.decode("utf-8", errors="replace")
        stderr_str = stderr.decode("utf-8", errors="replace")

        if process.returncode != 0:
            logger.warning(f"Command failed with return code {process.returncode}: {command}")
            logger.debug(f"Command error output: {stderr_str}")
            return CommandResult(status="error", output=stderr_str or "Command failed with no error output")

        return CommandResult(status="success", output=stdout_str)

    except asyncio.CancelledError:
        raise

    except Exception as e:
        raise CommandExecutionError(f"Failed to execute command: {str(e)}") from e

async def _get_full_docs() -> str | None:
    try:
        cmd = [NEBIUS_CLI_BIN, "docs", "mcp"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), EXECUTION_TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            logger.warning("timeout on: %s", " ".join(cmd))
            return None
    except Exception as exc:
        logger.error("cannot start %s - %s", " ".join(cmd), exc)
        return None

    if proc.returncode != 0:
        logger.warning("%s exited %s - %s",
                       " ".join(cmd), proc.returncode, stderr.decode().strip())
        return None

    return stdout.decode(errors="replace")

async def describe_service(service: str) -> ServiceHelpResult:
    if service in CLI_SERVICE_GROUPS:
        return ServiceHelpResult(
            help_text=f"{service} is a service group. Please specify a service within this group."
        )

    docs = await _get_full_docs()
    if docs is None:
        return ServiceHelpResult(help_text="")

    out_lines: List[str] = []
    capturing = False
    service_parts = service.split()

    for line in docs.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(NEBIUS_CLI_NAME + " "):
            parts = stripped.split()
            if len(parts) >= 2:
                capturing = (parts[1:len(service_parts)+1] == service_parts)
            else:
                capturing = False

        if capturing:
            out_lines.append(line)

    return ServiceHelpResult(help_text="\n".join(out_lines).rstrip())
