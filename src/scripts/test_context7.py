import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import logging
import argparse
import json
from utils.config import load_config_from_yaml
from utils.protocols import MCPClientManager
from utils.context7_manager import Context7Manager

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        # Parse arguments
        parser = argparse.ArgumentParser(description="Test Context7 MCP server")
        parser.add_argument("--action", default="list",
                          choices=["list", "create", "get", "update", "delete", "search", "query"],
                          help="Action to perform")
        parser.add_argument("--name", help="Name of the context")
        parser.add_argument("--content", help="Content to store in the context")
        parser.add_argument("--id", help="ID of the context")
        parser.add_argument("--query", help="Query for searching or querying contexts")
        parser.add_argument("--metadata", help="Metadata for the context (JSON string)")
        args = parser.parse_args()

        # Load configuration
        logger.info("Loading configuration...")
        settings = load_config_from_yaml("config/config.yaml")

        # Initialize MCP client manager
        logger.info("Initializing MCP client manager...")
        mcp_manager = MCPClientManager(config=settings.mcp_servers)

        # Initialize Context7 manager
        logger.info("Initializing Context7 manager...")
        context_manager = Context7Manager(mcp_manager)

        # Perform requested action
        if args.action == "list":
            logger.info("Listing all contexts...")
            result = await context_manager.list_contexts()
            logger.info(f"Contexts: {json.dumps(result, indent=2)}")

        elif args.action == "create":
            if not args.name or not args.content:
                logger.error("Name and content are required for create action")
                return

            # Parse metadata if provided
            metadata = {}
            if args.metadata:
                try:
                    metadata = json.loads(args.metadata)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON in metadata")
                    return

            logger.info(f"Creating context '{args.name}'...")
            result = await context_manager.create_context(
                name=args.name,
                content=args.content,
                metadata=metadata
            )
            logger.info(f"Created context: {json.dumps(result, indent=2)}")

        elif args.action == "get":
            if not args.id:
                logger.error("ID is required for get action")
                return

            logger.info(f"Getting context {args.id}...")
            result = await context_manager.get_context(args.id)
            logger.info(f"Context: {json.dumps(result, indent=2)}")

        elif args.action == "update":
            if not args.id:
                logger.error("ID is required for update action")
                return

            # Parse metadata if provided
            metadata = None
            if args.metadata:
                try:
                    metadata = json.loads(args.metadata)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON in metadata")
                    return

            logger.info(f"Updating context {args.id}...")
            result = await context_manager.update_context(
                context_id=args.id,
                name=args.name,
                content=args.content,
                metadata=metadata
            )
            logger.info(f"Updated context: {json.dumps(result, indent=2)}")

        elif args.action == "delete":
            if not args.id:
                logger.error("ID is required for delete action")
                return

            logger.info(f"Deleting context {args.id}...")
            result = await context_manager.delete_context(args.id)
            logger.info(f"Deleted context: {json.dumps(result, indent=2)}")

        elif args.action == "search":
            if not args.query:
                logger.error("Query is required for search action")
                return

            logger.info(f"Searching contexts with query '{args.query}'...")
            result = await context_manager.search_contexts(args.query)
            logger.info(f"Search results: {json.dumps(result, indent=2)}")

        elif args.action == "query":
            if not args.query:
                logger.error("Query is required for query action")
                return

            logger.info(f"Querying contexts with query '{args.query}'...")
            result = await context_manager.query_contexts(args.query)
            logger.info(f"Query results: {json.dumps(result, indent=2)}")

        # Close all sessions
        logger.info("Closing all sessions...")
        await mcp_manager.close_all()

        logger.info("Test completed successfully!")

    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
