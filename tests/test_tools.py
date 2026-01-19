'''
To run tests use uv + pytest command in terminal:

> uv run --with pytest --with pytest-asyncio pytest test_tools.py
'''

import asyncio
import os
from unittest.mock import AsyncMock, Mock, call, patch
import pytest

from pydantic import validate_call

from nebius_mcp_server.config import (
  NEBIUS_CLI_BIN,
  NEBIUS_CLI_NAME,
  CLI_FORBIDDEN_COMMANDS,
  CLI_FORBIDDEN_ERROR,
  CLI_UNSAFE_COMMANDS,
  CLI_UNSAFE_ERROR,
)
from nebius_mcp_server.server import (
    nebius_profiles,
    nebius_available_services,
    nebius_cli_help,
    nebius_cli_execute,
)

TEST_PROFILES = b'''profile1 [default]
profile2
'''

TEST_HELP_ALL = b'''Usage:
  nebius [flags]
  nebius [command]

Available Commands:
  applications
  help         Help about any command
  iam          All service related to IAM.

Flags:
      --color [=<true|false>] (bool)      Enable colored output.
  -c, --config <value> (string)           Provide path to config file.
'''

TEST_HELP_GROUP = b'''Usage:
  nebius iam [flags]
  nebius iam [command]

Available Commands:
  access-key                          [deprecated: supported until 2025-09-01] Access keys API v1 is deprecated, use the v2 version instead. Keys produced by API v1 are available using v2.
                                      Access keys API v1 is depricated. It's known to malfunction under certain conditions.
                                      Use Access keys API v2 instead. Access keys create by API v1 are available using Access keys API v2.
  access-permit

Global Flags:
      --color [=<true|false>] (bool)      Enable colored output.
  -c, --config <value> (string)           Provide path to config file.
'''

TEST_CLI_HELP_HEAD = '''nebius
  - applications
  - iam
  - profile - Manage configuration profiles
'''
TEST_CLI_HELP_APPLICATIONS = '''
nebius applications
  - v1alpha1

nebius applications v1alpha1
  - k-8-s-release

nebius applications v1alpha1 k-8-s-release
  - create
  - delete
  - get
  - list
  - operation - Manage operations for K8SRelease service.

nebius applications v1alpha1 k-8-s-release create
  Metadata:                                                    Common resource metadata.
    --resource-version <value> (int64)                         Version of the resource for safe concurrent modifications and consistent reads.
                                                               Positive and monotonically increases on each resource spec change (but *not* on each change of the
    --labels <[key1=value1[,key2=value2...]]> (string->string) Labels associated with the resource.
  Spec:
    --product-slug <value> (string) [required]

nebius applications v1alpha1 k-8-s-release delete
  --id <value> (string) [required]
'''
TEST_CLI_HELP_IAM_ACCESS_PERMIT = '''
nebius iam access-permit
  - create - Creates access permit for provided resource with provided role.
Subject of access permit is also a parent of access permit.
  - list - Lists access permits for provided parent.

nebius iam access-permit create - Creates access permit for provided resource with provided role.
Subject of access permit is also a parent of access permit.
  Metadata:                                                    Common resource metadata.
    --resource-version <value> (int64)                         Version of the resource for safe concurrent modifications and consistent reads.
                                                               Positive and monotonically increases on each resource spec change (but *not* on each change of the
    --labels <[key1=value1[,key2=value2...]]> (string->string) Labels associated with the resource.
  Spec:
    --resource-id <value> (string) Resource for granting access permit.

nebius iam access-permit delete - Delete access permit by id.
  --id <value> (string)
'''
TEST_CLI_HELP_IAM_AUTH_PUBLIC_KEY = '''
nebius iam auth-public-key
  - activate

nebius iam auth-public-key activate
  --id <value> (string)
'''

@pytest.mark.asyncio
async def test_nebius_profiles():
    cli_process = AsyncMock()
    cli_process.communicate.return_value = (TEST_PROFILES, b'')
    cli_process.returncode = 0

    with patch('asyncio.create_subprocess_exec', return_value=cli_process) as cli_mock:
        result = await nebius_profiles()
        cli_mock.assert_called_once_with(
            NEBIUS_CLI_BIN, "profile", "list",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        assert result == {
            "profile1": {"is_active": True,"name": "profile1"},
            "profile2": {"is_active": False,"name": "profile2"},
        }


@pytest.mark.asyncio
async def test_nebius_available_services():
    env = os.environ.copy()
    env["NEBIUS_OLD_HELP"] = "1"

    async def subsequent_calls(*args, **kwargs):
        cli_process = AsyncMock()
        cli_process.returncode = 0
        cli_process.communicate.return_value = (TEST_HELP_ALL, b'')
        if args == (NEBIUS_CLI_BIN, "help", "iam"):
            cli_process.communicate.return_value = (TEST_HELP_GROUP, b'')
        return cli_process

    with patch('asyncio.create_subprocess_exec') as cli_mock:
        cli_mock.side_effect = subsequent_calls
        result = await validate_call(nebius_available_services)()
        cli_mock.assert_has_calls([
            call.create_subprocess_exec(
                NEBIUS_CLI_BIN, "--help",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            ),
            call.create_subprocess_exec(
                NEBIUS_CLI_BIN, "help", "iam",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
        ], any_order=False)

        assert result == [
            {'name': 'applications', 'description': None, 'nested_services': []},
            {'name': 'iam', 'description': "All service related to IAM.", "nested_services": [
                {
                    'name': 'iam access-key',
                    'description': '[deprecated: supported until 2025-09-01] Access keys API v1 is deprecated, use the v2 version instead. Keys produced by API v1 are available using v2.',
                    'nested_services': []
                },
                {'name': 'iam access-permit', 'description': None, 'nested_services': []}
            ]},
        ]


@pytest.mark.asyncio
async def test_nebius_cli_help():
    test_output = (
        TEST_CLI_HELP_HEAD +
        TEST_CLI_HELP_APPLICATIONS +
        TEST_CLI_HELP_IAM_ACCESS_PERMIT +
        TEST_CLI_HELP_IAM_AUTH_PUBLIC_KEY
    ).encode()
    cli_process = AsyncMock()
    cli_process.communicate.return_value = (test_output, b'')
    cli_process.returncode = 0

    env = os.environ.copy()
    env["NEBIUS_OLD_HELP"] = "1"

    with patch('asyncio.create_subprocess_exec', return_value=cli_process) as cli_mock:
        ctx = AsyncMock()
        result = await nebius_cli_help(ctx, "applications")
        cli_mock.assert_called_once_with(
            NEBIUS_CLI_BIN, "docs", "mcp",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        ctx.info.assert_called()

        assert result == dict(help_text=TEST_CLI_HELP_APPLICATIONS.strip())

    with patch('asyncio.create_subprocess_exec', return_value=cli_process) as cli_mock:
        ctx = AsyncMock()
        result = await nebius_cli_help(ctx, "iam")
        assert result == dict(help_text="iam is a service group. Please specify a service within this group.")
        ctx.info.assert_called()

    with patch('asyncio.create_subprocess_exec', return_value=cli_process) as cli_mock:
        ctx = AsyncMock()
        result = await nebius_cli_help(ctx, "iam access-permit")
        cli_mock.assert_called_once_with(
            NEBIUS_CLI_BIN, "docs", "mcp",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        assert result == dict(help_text=TEST_CLI_HELP_IAM_ACCESS_PERMIT.strip())
        ctx.info.assert_called()

    with patch('asyncio.create_subprocess_exec', return_value=cli_process) as cli_mock:
        ctx = AsyncMock()
        result = await nebius_cli_help(ctx, "msp missing")
        cli_mock.assert_called_once_with(
            NEBIUS_CLI_BIN, "docs", "mcp",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        assert result == dict(help_text="")
        ctx.info.assert_called()

@pytest.mark.asyncio
async def test_nebius_cli_execute():
    command = ["iam", "access-permit", "list", "--parent-id", "fake-id"]
    test_output = b'Test command output'

    cli_process = AsyncMock()
    cli_process.communicate.return_value = (test_output, b'')
    cli_process.returncode = 0

    with patch('asyncio.create_subprocess_exec', return_value=cli_process) as cli_mock:
        ctx = AsyncMock()
        result = await nebius_cli_execute(ctx, " ".join([NEBIUS_CLI_NAME, *command]))
        cli_mock.assert_called_once_with(
            NEBIUS_CLI_BIN, *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        assert result == dict(status="success", output=test_output.decode())
        ctx.info.assert_called()

    cli_process.communicate.return_value = (test_output, b'')
    cli_process.returncode = 1
    with patch('asyncio.create_subprocess_exec', return_value=cli_process) as cli_mock:
        ctx = AsyncMock()
        result = await nebius_cli_execute(ctx, " ".join([NEBIUS_CLI_NAME, *command]))
        cli_mock.assert_called_once_with(
            NEBIUS_CLI_BIN, *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        assert result == dict(status="error", output='Command failed with no error output')
        ctx.warning.assert_called()

    cli_process.communicate.return_value = (test_output, test_output)
    cli_process.returncode = 1
    with patch('asyncio.create_subprocess_exec', return_value=cli_process) as cli_mock:
        ctx = AsyncMock()
        result = await nebius_cli_execute(ctx, " ".join([NEBIUS_CLI_NAME, *command]))
        cli_mock.assert_called_once_with(
            NEBIUS_CLI_BIN, *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        assert result == dict(status="error", output=test_output.decode())
        ctx.warning.assert_called()

    with patch('asyncio.create_subprocess_exec', return_value=cli_process) as cli_mock:
        ctx = AsyncMock()
        result = await nebius_cli_execute(ctx, " ".join(["wrong_command", *command]))
        assert result == dict(output="Wrong command", status="error")
        cli_mock.assert_not_called()
        ctx.warning.assert_called()

    test_timeout = 0.1
    with patch('asyncio.create_subprocess_exec', return_value=cli_process) as cli_mock, \
            patch('nebius_mcp_server.cli.EXECUTION_TIMEOUT', test_timeout):

        async def slow_communicate():
            await asyncio.sleep(test_timeout * 2)
            return test_output, b''

        cli_process.communicate.side_effect = slow_communicate
        cli_process.returncode = 0

        cli_process.kill = Mock()

        ctx = AsyncMock()
        result = await nebius_cli_execute(ctx, " ".join([NEBIUS_CLI_NAME, *command]))
        cli_mock.assert_called_once_with(
            NEBIUS_CLI_BIN, *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        cli_process.kill.assert_called_once()
        output = f'Command execution error: Failed to execute command: Command timed out after {test_timeout} seconds'
        assert result == dict(status="error", output=output)

    for cmd in CLI_UNSAFE_COMMANDS:
        cli_process = AsyncMock()
        cli_process.communicate.return_value = (b'', test_output)
        cli_process.returncode = 1

        with patch('asyncio.create_subprocess_exec', return_value=cli_process) as cli_mock, \
                patch('nebius_mcp_server.cli.SAFE_MODE', True):
            ctx = AsyncMock()
            result = await nebius_cli_execute(ctx, " ".join([NEBIUS_CLI_NAME, cmd]))
            expected_error = f"{CLI_UNSAFE_ERROR}: {cmd}, provide manual instructions instead."
            assert result == dict(output=expected_error, status="error")
            cli_mock.assert_not_called()
            ctx.warning.assert_called()

        cli_process = AsyncMock()
        cli_process.communicate.return_value = (test_output, b'')
        cli_process.returncode = 0

        with patch('asyncio.create_subprocess_exec', return_value=cli_process) as cli_mock, \
                patch('nebius_mcp_server.cli.SAFE_MODE', False):
            ctx = AsyncMock()
            result = await nebius_cli_execute(ctx, " ".join([NEBIUS_CLI_NAME, cmd]))
            expected_error = f"{CLI_UNSAFE_ERROR}: {cmd}"
            assert result == dict(status="success", output=test_output.decode())
            cli_mock.assert_called_once_with(
                NEBIUS_CLI_BIN, cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            ctx.info.assert_called()

    for cmd in CLI_FORBIDDEN_COMMANDS:
        cli_process = AsyncMock()
        cli_process.communicate.return_value = (test_output, b'')
        cli_process.returncode = 0

        with patch('asyncio.create_subprocess_exec', return_value=cli_process) as cli_mock, \
                patch('nebius_mcp_server.cli.SAFE_MODE', True):
            ctx = AsyncMock()
            result = await nebius_cli_execute(ctx, " ".join([NEBIUS_CLI_NAME, cmd]))
            expected_error = f"{CLI_FORBIDDEN_ERROR}: {cmd}, provide manual instructions instead."
            assert result == dict(output=expected_error, status="error")
            cli_mock.assert_not_called()
            ctx.warning.assert_called()

        with patch('asyncio.create_subprocess_exec', return_value=cli_process) as cli_mock, \
                patch('nebius_mcp_server.cli.SAFE_MODE', False):
            ctx = AsyncMock()
            result = await nebius_cli_execute(ctx, " ".join([NEBIUS_CLI_NAME, cmd]))
            expected_error = f"{CLI_FORBIDDEN_ERROR}: {cmd}, provide manual instructions instead."
            assert result == dict(output=expected_error, status="error")
            cli_mock.assert_not_called()
            ctx.warning.assert_called()
