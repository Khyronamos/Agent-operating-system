import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import logging
import argparse
import json
from utils.config import load_config_from_yaml
from utils.protocols import MCPClientManager
from utils.slack_manager import SlackManager

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        # Parse arguments
        parser = argparse.ArgumentParser(description="Test Slack MCP server")
        parser.add_argument("--action", default="list",
                          choices=["list", "send-message", "list-channels", "list-users", "get-channel-history"],
                          help="Action to perform")
        parser.add_argument("--channel", help="Channel ID or name")
        parser.add_argument("--message", help="Message text")
        parser.add_argument("--user", help="User ID or name")
        parser.add_argument("--limit", type=int, default=10, help="Limit for history")
        args = parser.parse_args()

        # Load configuration
        logger.info("Loading configuration...")
        settings = load_config_from_yaml("config/config.yaml")

        # Initialize MCP client manager
        logger.info("Initializing MCP client manager...")
        mcp_manager = MCPClientManager(config=settings.mcp_servers)

        # Initialize Slack manager
        logger.info("Initializing Slack manager...")
        slack_manager = SlackManager(mcp_manager)

        # Test Slack MCP server
        server_name = "slack"
        logger.info(f"Testing {server_name} MCP server...")

        # List available tools
        logger.info(f"Listing tools for {server_name}...")
        tools = await mcp_manager.list_tools(server_name)
        logger.info(f"Available tools: {tools}")

        # Perform requested action
        if args.action == "list":
            logger.info("Listing available tools...")
            # Already done above

        elif args.action == "send-message":
            if not args.channel or not args.message:
                logger.error("Channel and message are required for send-message action")
                return

            logger.info(f"Sending message to channel {args.channel}...")
            result = await slack_manager.send_message(args.channel, args.message)
            logger.info(f"Message sent: {json.dumps(result, indent=2)}")

        elif args.action == "list-channels":
            logger.info("Listing channels...")
            result = await slack_manager.list_channels()
            logger.info(f"Channels: {json.dumps(result, indent=2)}")

        elif args.action == "list-users":
            logger.info("Listing users...")
            result = await slack_manager.list_users()
            logger.info(f"Users: {json.dumps(result, indent=2)}")

        elif args.action == "get-channel-history":
            if not args.channel:
                logger.error("Channel is required for get-channel-history action")
                return

            logger.info(f"Getting history for channel {args.channel}...")
            result = await slack_manager.get_channel_history(args.channel, args.limit)
            logger.info(f"Channel history: {json.dumps(result, indent=2)}")

        # Close all sessions
        logger.info("Closing all sessions...")
        await mcp_manager.close_all()

        logger.info("Test completed successfully!")

    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
