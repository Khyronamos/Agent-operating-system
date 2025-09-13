import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import logging
import argparse
import json
from utils.config import load_config_from_yaml
from utils.protocols import MCPClientManager
from utils.mcp_control_manager import MCPControlManager

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        # Parse arguments
        parser = argparse.ArgumentParser(description="Test MCP Control server")
        parser.add_argument("--action", default="list",
                          choices=["list", "list-servers", "start-server", "stop-server", "status", "orchestrate"],
                          help="Action to perform")
        parser.add_argument("--server", help="Server name to control")
        parser.add_argument("--workflow", help="Workflow to orchestrate")
        args = parser.parse_args()

        # Load configuration
        logger.info("Loading configuration...")
        settings = load_config_from_yaml("config/config.yaml")

        # Initialize MCP client manager
        logger.info("Initializing MCP client manager...")
        mcp_manager = MCPClientManager(config=settings.mcp_servers)

        # Initialize MCP Control manager
        logger.info("Initializing MCP Control manager...")
        control_manager = MCPControlManager(mcp_manager)

        # Test MCP Control server
        server_name = "mcp-control"
        logger.info(f"Testing {server_name} server...")

        # List available tools
        logger.info(f"Listing tools for {server_name}...")
        tools = await mcp_manager.list_tools(server_name)
        logger.info(f"Available tools: {tools}")

        # Perform requested action
        if args.action == "list":
            logger.info("Listing available tools...")
            # Already done above

        elif args.action == "list-servers":
            logger.info("Listing available MCP servers...")
            result = await control_manager.list_servers()
            logger.info(f"Available servers: {json.dumps(result, indent=2)}")

        elif args.action == "start-server":
            if not args.server:
                logger.error("Server name is required for start-server action")
                return

            logger.info(f"Starting server {args.server}...")
            result = await control_manager.start_server(args.server)
            logger.info(f"Start result: {json.dumps(result, indent=2)}")

        elif args.action == "stop-server":
            if not args.server:
                logger.error("Server name is required for stop-server action")
                return

            logger.info(f"Stopping server {args.server}...")
            result = await control_manager.stop_server(args.server)
            logger.info(f"Stop result: {json.dumps(result, indent=2)}")

        elif args.action == "status":
            if not args.server:
                logger.error("Server name is required for status action")
                return

            logger.info(f"Getting status for server {args.server}...")
            result = await control_manager.get_server_status(args.server)
            logger.info(f"Status: {json.dumps(result, indent=2)}")

        elif args.action == "orchestrate":
            if not args.workflow:
                logger.error("Workflow is required for orchestrate action")
                return

            logger.info(f"Orchestrating workflow {args.workflow}...")
            result = await control_manager.orchestrate_workflow(args.workflow)
            logger.info(f"Orchestration result: {json.dumps(result, indent=2)}")

        # Close all sessions
        logger.info("Closing all sessions...")
        await mcp_manager.close_all()

        logger.info("Test completed successfully!")

    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
