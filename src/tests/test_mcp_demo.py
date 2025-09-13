import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
from utils.config import MCPServerConfig
from utils.protocols import MCPClientManager

async def main():
    # Configure a mock MCP server
    cfg = [MCPServerConfig(name="mock", connection_type="stdio")]
    mgr = MCPClientManager(cfg)

    # Test the 'add' tool
    result = await mgr.call_tool("mock", "add", {"a": 5, "b": 7})
    print(f"MCP add test: 5 + 7 = {result}")

    # Clean up
    await mgr.close_all()

if __name__ == "__main__":
    asyncio.run(main())
