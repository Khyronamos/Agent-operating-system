import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import logging
import argparse
from utils.config import load_config_from_yaml
from utils.protocols import MCPClientManager
from utils.browser_manager import BrowserManager

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_browser_test(url):
    try:
        # Load configuration
        logger.info("Loading configuration...")
        settings = load_config_from_yaml("config/config.yaml")
        
        # Initialize MCP client manager
        logger.info("Initializing MCP client manager...")
        mcp_manager = MCPClientManager(config=settings.mcp_servers)
        
        # Initialize browser manager
        logger.info("Initializing browser manager...")
        browser_manager = BrowserManager(mcp_manager)
        
        # Navigate to URL
        logger.info(f"Navigating to {url}...")
        await browser_manager.navigate_to_url(url)
        
        # Take a screenshot
        logger.info("Taking a screenshot...")
        screenshot = await browser_manager.take_screenshot()
        
        # Save the screenshot
        screenshot_path = f"screenshot_{url.replace('://', '_').replace('/', '_').replace('.', '_')}.png"
        with open(screenshot_path, "wb") as f:
            f.write(screenshot)
        logger.info(f"Screenshot saved to {screenshot_path}")
        
        # Extract text
        logger.info("Extracting text from page...")
        text = await browser_manager.extract_text()
        logger.info(f"Extracted text (first 200 chars): {text[:200]}...")
        
        # Extract links
        logger.info("Extracting links from page...")
        links = await browser_manager.extract_links()
        logger.info(f"Found {len(links)} links")
        
        # Close browser
        logger.info("Closing browser...")
        await browser_manager.close()
        
        logger.info("Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)

def main():
    parser = argparse.ArgumentParser(description="Run Hyperbrowser test")
    parser.add_argument("--url", default="https://www.google.com", help="URL to navigate to")
    args = parser.parse_args()
    
    asyncio.run(run_browser_test(args.url))

if __name__ == "__main__":
    main()
