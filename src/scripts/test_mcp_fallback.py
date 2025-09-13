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

class BrowserManager:
    """Manager for browser automation with fallback logic."""
    
    def __init__(self, mcp_manager):
        self.mcp_manager = mcp_manager
        self.primary_server = "hyperbrowser"
        self.fallback_server = "puppeteer"
    
    async def navigate(self, url):
        """Navigate to a URL with fallback logic."""
        try:
            logger.info(f"Attempting to navigate using {self.primary_server}...")
            result = await self.mcp_manager.call_tool(
                self.primary_server, 
                "navigate", 
                {"url": url}
            )
            logger.info(f"Navigation successful with {self.primary_server}")
            return result
        except Exception as e:
            logger.warning(f"Error with {self.primary_server}: {e}")
            logger.info(f"Falling back to {self.fallback_server}...")
            try:
                result = await self.mcp_manager.call_tool(
                    self.fallback_server, 
                    "navigate", 
                    {"url": url}
                )
                logger.info(f"Navigation successful with {self.fallback_server}")
                return result
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                raise
    
    async def screenshot(self):
        """Take a screenshot with fallback logic."""
        try:
            logger.info(f"Attempting to take screenshot using {self.primary_server}...")
            result = await self.mcp_manager.call_tool(
                self.primary_server,
                "screenshot",
                {}
            )
            logger.info(f"Screenshot successful with {self.primary_server}")
            return result
        except Exception as e:
            logger.warning(f"Error with {self.primary_server}: {e}")
            logger.info(f"Falling back to {self.fallback_server}...")
            try:
                result = await self.mcp_manager.call_tool(
                    self.fallback_server,
                    "screenshot",
                    {}
                )
                logger.info(f"Screenshot successful with {self.fallback_server}")
                return result
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                raise

async def main():
    try:
        # Load configuration
        logger.info("Loading configuration...")
        settings = load_config_from_yaml("config/config.yaml")
        
        # Initialize MCP client manager
        logger.info("Initializing MCP client manager...")
        mcp_manager = MCPClientManager(config=settings.mcp_servers)
        
        # Initialize browser manager with fallback logic
        browser_manager = BrowserManager(mcp_manager)
        
        # Test navigation with fallback
        logger.info("Testing navigation to Google with fallback logic...")
        await browser_manager.navigate("https://www.google.com")
        
        # Test screenshot with fallback
        logger.info("Taking a screenshot with fallback logic...")
        screenshot = await browser_manager.screenshot()
        
        # Save the screenshot
        with open("fallback_screenshot.png", "wb") as f:
            f.write(screenshot)
        logger.info("Screenshot saved to fallback_screenshot.png")
        
        # Close all sessions
        logger.info("Closing all sessions...")
        await mcp_manager.close_all()
        
        logger.info("Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
        
if __name__ == "__main__":
    asyncio.run(main())
