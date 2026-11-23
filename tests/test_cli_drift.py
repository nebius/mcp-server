"""CLI-drift canary.

daily_check.yml installs the *latest* nebius CLI and runs this file, so this is
the detector for the one risk CLI delegation carries: the CLI moving underneath
the server.

Why this is not in tests/test_server.py
---------------------------------------
tests.yml runs test_server.py on every push and pull request. A drift failure
there would block the merge queue on a change nobody in this repo made. Drift
should page, not block -- so these assertions live in their own file, wired only
to the scheduled job and its Slack notification.

Why isError is not enough
-------------------------
Several paths turn a CLI failure into an empty success -- get_profiles returns
{} (cli.py:73, cli.py:99), and describe_service returns help_text="". Against a
CLI that produced no usable output at all, every tool call still came back
green. These assertions look at the payload instead.

Why the floors are sizes and counts, not truthiness
---------------------------------------------------
`assert help_text` and `assert services` are both too weak to be useful.
describe_service captures any line whose lstrip() starts with "nebius ", which
includes indented usage lines, not just section headers. A docs-format change
that rewrites the headers but leaves the usage lines intact yields ~95 bytes of
leftover stub per service -- non-empty, so a truthiness check reports green on
real drift. Same for the service list: collapsing 21 services to 1 is still
truthy. So both assertions carry a floor with roughly 2-5x headroom over
today's smallest healthy value.

These are still deliberately shallow: they check that a plausible amount of
something came back, never the shape of it, which would break whenever the CLI
legitimately rewords its output.
"""

import asyncio

import pytest

from test_server import receive, send, wait_until_ready

# GA services only. `applications` is v1alpha1, so it is a poor anchor -- an
# upstream promotion or rename would page the team about their own success.
# N-of-M rather than all-of-M for the same reason: one service being renamed is
# ordinary churn, whereas a help-format change shrinks all of them at once, and
# only the second is worth a 12:00 CET Slack alert.
HELP_ANCHORS = [
    "compute instance",
    "compute disk",
    "iam project",
    "iam service-account",
    "vpc network",
]
MIN_ANCHORS_WITH_HELP = 4

# Smallest healthy anchor today is `iam project` at ~5,400 bytes, so this leaves
# about 5x headroom for the CLI legitimately trimming its help text.
MIN_HELP_BYTES = 1000

# 21 top-level services today, so this leaves about 2x headroom.
MIN_SERVICES = 10

# Three GA top-level names that should not vanish in a non-breaking CLI release.
EXPECTED_SERVICES = {"compute", "iam", "vpc"}


async def _call(proc, msg_id, name, arguments):
    await send(proc, {"jsonrpc": "2.0", "id": msg_id, "method": "tools/call",
                      "params": {"name": name, "arguments": arguments}})
    response = await receive(proc)
    assert not response["result"]["isError"], f"{name} returned isError"
    return response["result"].get("structuredContent") or {}


@pytest.mark.asyncio
async def test_cli_still_produces_usable_output():
    # asyncio's StreamReader defaults to a 64 KiB readline limit, and a single
    # JSON-RPC response can exceed that: nebius_cli_help(service="compute
    # instance") is ~66 KB today and service="billing" is ~234 KB. Without a
    # raised limit the read fails with ValueError("Separator is not found, and
    # chunk exceed the limit") before any assertion runs -- a crash, not a
    # drift signal.
    proc = await asyncio.create_subprocess_exec(
        'uv', 'run', 'nebius_mcp_server/main.py',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        limit=8 * 1024 * 1024,
    )
    try:
        await wait_until_ready(proc)
        await send(proc, {"jsonrpc": "2.0", "method": "initialize", "id": 1, "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "drift-canary", "version": "0.1.0"}
        }})
        await receive(proc)
        await send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})

        msg_id = 1

        # nebius_profiles is intentionally absent from this file. On a runner
        # with no ~/.nebius/config.yaml, `nebius profile list` exits 4 and
        # cli.py:73 correctly returns {} -- there is no payload to assert on.

        msg_id += 1
        structured = await _call(proc, msg_id, "nebius_available_services", {})
        services = structured.get("result") or []
        names = {s.get("name") for s in services if isinstance(s, dict)}
        assert len(services) >= MIN_SERVICES, (
            f"nebius_available_services returned {len(services)} services, expected "
            f"at least {MIN_SERVICES} -- the CLI may have changed its output format. "
            f"Got: {sorted(names)}"
        )
        assert EXPECTED_SERVICES <= names, (
            f"nebius_available_services is missing {sorted(EXPECTED_SERVICES - names)} "
            f"-- the CLI may have renamed or dropped a top-level service. "
            f"Got: {sorted(names)}"
        )

        found = {}
        for service in HELP_ANCHORS:
            msg_id += 1
            structured = await _call(proc, msg_id, "nebius_cli_help", {"service": service})
            found[service] = len((structured.get("help_text") or "").strip())

        with_help = [s for s, n in found.items() if n >= MIN_HELP_BYTES]
        assert len(with_help) >= MIN_ANCHORS_WITH_HELP, (
            f"only {len(with_help)} of {len(HELP_ANCHORS)} GA services returned at "
            f"least {MIN_HELP_BYTES} bytes of help -- the CLI docs format has "
            f"probably changed. Lengths: {found}"
        )
    finally:
        proc.terminate()
        await proc.wait()
