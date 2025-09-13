import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import logging
from utils.config import load_config_from_yaml, MCPServerConfig
from utils.protocols import MCPClientManager

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        # Load configuration
        logger.info("Loading configuration...")
        settings = load_config_from_yaml("config/config.yaml")
        
        # Initialize MCP client manager
        logger.info("Initializing MCP client manager...")
        mcp_manager = MCPClientManager(config=settings.mcp_servers)
        
        # Test Hyperbrowser MCP server
        server_name = "hyperbrowser"
        logger.info(f"Testing {server_name} MCP server...")
        
        # Get session and list tools
        logger.info(f"Getting session for {server_name}...")
        session = await mcp_manager.get_session(server_name)
        
        logger.info(f"Listing tools for {server_name}...")
        tools = await mcp_manager.list_tools(server_name)
        logger.info(f"Available tools: {tools}")
        
        # Test a simple navigation
        logger.info("Testing navigation to Google...")
        result = await mcp_manager.call_tool(
            server_name, 
            "navigate", 
            {"url": "https://www.google.com"}
        )
        logger.info(f"Navigation result: {result}")
        
        # Take a screenshot
        logger.info("Taking a screenshot...")
        screenshot = await mcp_manager.call_tool(
            server_name,
            "screenshot",
            {}
        )
        logger.info(f"Screenshot taken: {len(screenshot)} bytes")
        
        # Save the screenshot
        with open("google_screenshot.png", "wb") as f:
            f.write(screenshot)
        logger.info("Screenshot saved to google_screenshot.png")
        
        # Close all sessions
        logger.info("Closing all sessions...")
        await mcp_manager.close_all()
        
        logger.info("Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
        
if __name__ == "__main__":
    asyncio.run(main())
