import asyncio
import logging
from utils.config   import load_config_from_yaml, MCPServerConfig
from utils.protocols import StdioServerParameters, TcpServerParameters


log = logging.getLogger(__name__)

async def main():
    settings = load_config_from_yaml()
    for svr in settings.mcp_servers:
        log.info(f"starting MCP server {svr.name}")
        if svr.connection_type == "stdio":
            params = StdioServerParameters(command=svr.command, args=svr.args, env=svr.env)
            # await start_stdio_server(params)
        else:
            params = TcpServerParameters(host=svr.host, port=svr.port)
            # await start_tcp_server(params)
    # keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())