import asyncio
import json

import pytest


async def wait_until_ready(proc: asyncio.subprocess.Process, timeout: int=10):
    deadline = asyncio.get_event_loop().time() + timeout
    while True:
        if proc.returncode is not None:
            raise RuntimeError("server exited with code", proc.returncode)
        if asyncio.get_event_loop().time() > deadline:
            raise RuntimeError("Timeout waiting for server readiness")

        line = await proc.stderr.readline()
        if not line:
            continue

        decoded = line.decode().strip()
        if "Nebius CLI is installed and available." in decoded:
            break


async def send(proc: asyncio.subprocess.Process, msg: str) -> None:
    line = json.dumps(msg) + '\n'
    proc.stdin.write(line.encode())
    await proc.stdin.drain()


async def receive(proc: asyncio.subprocess.Process) -> str:
    line = await proc.stdout.readline()
    return json.loads(line.decode())


@pytest.mark.asyncio
async def test_all_tools():
    proc = await asyncio.create_subprocess_exec(
        'uv', 'run', '--active', '--with', 'fastmcp', 'fastmcp', 'run', 'server.py',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    await wait_until_ready(proc)
    # init
    msg_id = 1
    await send(proc, {"jsonrpc": "2.0", "method": "initialize", "id": msg_id, "params": {
        "protocolVersion": "2025-03-26",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "0.1.0"}
    }})
    response = await receive(proc)
    assert response["result"]["serverInfo"]["name"] == "Nebius MCP Server"
    await send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})

    # ping
    msg_id += 1
    await send(proc, {"jsonrpc": "2.0", "method": "ping", "id": msg_id})
    response = await receive(proc)
    assert response == {"jsonrpc": "2.0", "id": msg_id, "result":{}}

    # get tools
    msg_id += 1
    await send(proc, {"jsonrpc": "2.0", "id": msg_id, "method": "tools/list", "params": {}})
    response = await receive(proc)
    assert len(response["result"]["tools"]) == 4

    # call nebius_profiles
    msg_id += 1
    await send(proc, {"jsonrpc": "2.0", "id": msg_id, "method":"tools/call", "params": {"name": "nebius_profiles", "arguments": {}}})
    response = await receive(proc)
    assert not response["result"]["isError"]

    # call nebius_available_services
    msg_id += 1
    await send(proc, {"jsonrpc": "2.0", "id": msg_id, "method":"tools/call", "params": {"name": "nebius_available_services", "arguments": {}}})
    response = await receive(proc)
    assert not response["result"]["isError"]

    # call nebius_cli_help
    msg_id += 1
    await send(proc, {"jsonrpc": "2.0", "id": msg_id, "method":"tools/call", "params": {"name": "nebius_cli_help", "arguments": {"service": "applications"}}})
    response = await receive(proc)
    assert not response["result"]["isError"]

    proc.terminate()
    await proc.wait()
