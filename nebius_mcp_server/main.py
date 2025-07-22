import logging
import sys

from nebius_mcp_server.config import TRANSPORT
from nebius_mcp_server.server import mcp

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler(sys.stderr)])
logger = logging.getLogger("nebius-mcp-server")


def main():
    if TRANSPORT not in ("stdio", "sse"):
        logger.error(f"Invalid transport protocol: {TRANSPORT}. Must be 'stdio' or 'sse'")
        sys.exit(1)

    logger.info(f"Starting server with transport protocol: {TRANSPORT}")
    mcp.run(transport=TRANSPORT)


if __name__ == "__main__":
    main()
