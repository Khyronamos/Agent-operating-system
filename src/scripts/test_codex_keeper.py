import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import logging
import argparse
from utils.config import load_config_from_yaml
from utils.protocols import MCPClientManager
from utils.codex_keeper_manager import CodexKeeperManager

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        # Parse arguments
        parser = argparse.ArgumentParser(description="Test Codex Keeper MCP server")
        parser.add_argument("--action", default="list",
                          choices=["list", "create", "retrieve", "update", "delete", "search"],
                          help="Action to perform")
        parser.add_argument("--name", help="Name of the codex")
        parser.add_argument("--content", help="Content of the codex")
        parser.add_argument("--tags", help="Tags for the codex (comma-separated)")
        parser.add_argument("--id", help="ID of the codex")
        parser.add_argument("--query", help="Search query")
        args = parser.parse_args()

        # Load configuration
        logger.info("Loading configuration...")
        settings = load_config_from_yaml("config/config.yaml")

        # Initialize MCP client manager
        logger.info("Initializing MCP client manager...")
        mcp_manager = MCPClientManager(config=settings.mcp_servers)

        # Initialize Codex Keeper manager
        logger.info("Initializing Codex Keeper manager...")
        codex_manager = CodexKeeperManager(mcp_manager)

        # Perform requested action
        if args.action == "list":
            logger.info("Listing all codices...")
            result = await codex_manager.list_codices()
            logger.info(f"Codices: {result}")

        elif args.action == "create":
            if not args.name or not args.content:
                logger.error("Name and content are required for create action")
                return

            tags = args.tags.split(",") if args.tags else []

            logger.info(f"Creating codex '{args.name}'...")
            result = await codex_manager.create_codex(args.name, args.content, tags)
            logger.info(f"Created codex: {result}")

        elif args.action == "retrieve":
            if not args.id:
                logger.error("ID is required for retrieve action")
                return

            logger.info(f"Retrieving codex {args.id}...")
            result = await codex_manager.get_codex(args.id)
            logger.info(f"Retrieved codex: {result}")

        elif args.action == "update":
            if not args.id:
                logger.error("ID is required for update action")
                return

            tags = args.tags.split(",") if args.tags else None

            logger.info(f"Updating codex {args.id}...")
            result = await codex_manager.update_codex(
                args.id,
                name=args.name,
                content=args.content,
                tags=tags
            )
            logger.info(f"Updated codex: {result}")

        elif args.action == "delete":
            if not args.id:
                logger.error("ID is required for delete action")
                return

            logger.info(f"Deleting codex {args.id}...")
            result = await codex_manager.delete_codex(args.id)
            logger.info(f"Deleted codex: {result}")

        elif args.action == "search":
            if not args.query:
                logger.error("Query is required for search action")
                return

            logger.info(f"Searching codices with query '{args.query}'...")
            result = await codex_manager.search_codices(args.query)
            logger.info(f"Search results: {result}")

        # Close all sessions
        logger.info("Closing all sessions...")
        await mcp_manager.close_all()

        logger.info("Test completed successfully!")

    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
