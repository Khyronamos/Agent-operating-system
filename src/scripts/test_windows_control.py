import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import logging
import argparse
import json
from utils.config import load_config_from_yaml
from utils.protocols import MCPClientManager
from utils.windows_control_manager import WindowsControlManager

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        # Parse arguments
        parser = argparse.ArgumentParser(description="Test Windows Control MCP server")
        parser.add_argument("--action", default="list",
                          choices=["list", "screenshot", "click", "type", "move", "drag", "key-combo"],
                          help="Action to perform")
        parser.add_argument("--x", type=int, help="X coordinate for mouse actions")
        parser.add_argument("--y", type=int, help="Y coordinate for mouse actions")
        parser.add_argument("--text", help="Text to type")
        parser.add_argument("--keys", help="Keys for key combination (comma-separated)")
        args = parser.parse_args()

        # Load configuration
        logger.info("Loading configuration...")
        settings = load_config_from_yaml("config/config.yaml")

        # Initialize MCP client manager
        logger.info("Initializing MCP client manager...")
        mcp_manager = MCPClientManager(config=settings.mcp_servers)

        # Initialize Windows Control manager
        logger.info("Initializing Windows Control manager...")
        windows_manager = WindowsControlManager(mcp_manager)

        # Test Windows Control MCP server
        server_name = "windows-control"
        logger.info(f"Testing {server_name} MCP server...")

        # List available tools
        logger.info(f"Listing tools for {server_name}...")
        tools = await mcp_manager.list_tools(server_name)
        logger.info(f"Available tools: {tools}")

        # Perform requested action
        if args.action == "list":
            logger.info("Listing available tools...")
            # Already done above

        elif args.action == "screenshot":
            logger.info("Taking screenshot...")
            result = await windows_manager.take_screenshot("screenshot.png")
            logger.info(f"Screenshot taken: {json.dumps(result, indent=2)}")

        elif args.action == "click":
            if not args.x or not args.y:
                logger.error("X and Y coordinates are required for click action")
                return

            logger.info(f"Clicking at coordinates ({args.x}, {args.y})...")
            result = await windows_manager.mouse_click(args.x, args.y)
            logger.info(f"Click result: {json.dumps(result, indent=2)}")

        elif args.action == "type":
            if not args.text:
                logger.error("Text is required for type action")
                return

            logger.info(f"Typing text: {args.text}")
            result = await windows_manager.type_text(args.text)
            logger.info(f"Type result: {json.dumps(result, indent=2)}")

        elif args.action == "move":
            if not args.x or not args.y:
                logger.error("X and Y coordinates are required for move action")
                return

            logger.info(f"Moving mouse to coordinates ({args.x}, {args.y})...")
            result = await windows_manager.mouse_move(args.x, args.y)
            logger.info(f"Move result: {json.dumps(result, indent=2)}")

        elif args.action == "drag":
            if not args.x or not args.y:
                logger.error("X and Y coordinates are required for drag action")
                return

            # For simplicity, we'll use current position as start
            # In a real scenario, you'd want to specify both start and end coordinates
            logger.info(f"Dragging mouse to coordinates ({args.x}, {args.y})...")
            result = await windows_manager.mouse_drag(0, 0, args.x, args.y)
            logger.info(f"Drag result: {json.dumps(result, indent=2)}")

        elif args.action == "key-combo":
            if not args.keys:
                logger.error("Keys are required for key-combo action")
                return

            keys = args.keys.split(",")
            logger.info(f"Pressing key combination: {keys}")
            result = await windows_manager.press_keys(keys)
            logger.info(f"Key combo result: {json.dumps(result, indent=2)}")

        # Close all sessions
        logger.info("Closing all sessions...")
        await mcp_manager.close_all()

        logger.info("Test completed successfully!")

    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
