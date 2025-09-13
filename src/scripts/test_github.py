import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import logging
import argparse
import json
from utils.config import load_config_from_yaml
from utils.protocols import MCPClientManager
from utils.github_manager import GitHubManager

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        # Parse arguments
        parser = argparse.ArgumentParser(description="Test GitHub MCP server")
        parser.add_argument("--action", default="list",
                          choices=["list", "get-repo", "list-repos", "create-issue", "list-issues", "create-pr", "list-prs"],
                          help="Action to perform")
        parser.add_argument("--owner", help="Repository owner")
        parser.add_argument("--repo", help="Repository name")
        parser.add_argument("--title", help="Title for issue or PR")
        parser.add_argument("--body", help="Body for issue or PR")
        parser.add_argument("--base", default="main", help="Base branch for PR")
        parser.add_argument("--head", help="Head branch for PR")
        args = parser.parse_args()

        # Load configuration
        logger.info("Loading configuration...")
        settings = load_config_from_yaml("config/config.yaml")

        # Initialize MCP client manager
        logger.info("Initializing MCP client manager...")
        mcp_manager = MCPClientManager(config=settings.mcp_servers)

        # Initialize GitHub manager
        logger.info("Initializing GitHub manager...")
        github_manager = GitHubManager(mcp_manager)

        # Test GitHub MCP server
        server_name = "github"
        logger.info(f"Testing {server_name} MCP server...")

        # List available tools
        logger.info(f"Listing tools for {server_name}...")
        tools = await mcp_manager.list_tools(server_name)
        logger.info(f"Available tools: {tools}")

        # Perform requested action
        if args.action == "list":
            logger.info("Listing available tools...")
            # Already done above

        elif args.action == "get-repo":
            if not args.owner or not args.repo:
                logger.error("Owner and repo are required for get-repo action")
                return

            logger.info(f"Getting repository {args.owner}/{args.repo}...")
            result = await github_manager.get_repository(args.owner, args.repo)
            logger.info(f"Repository details: {json.dumps(result, indent=2)}")

        elif args.action == "list-repos":
            if not args.owner:
                logger.error("Owner is required for list-repos action")
                return

            logger.info(f"Listing repositories for {args.owner}...")
            result = await github_manager.list_repositories(args.owner)
            logger.info(f"Repositories: {json.dumps(result, indent=2)}")

        elif args.action == "create-issue":
            if not args.owner or not args.repo or not args.title:
                logger.error("Owner, repo, and title are required for create-issue action")
                return

            logger.info(f"Creating issue in {args.owner}/{args.repo}...")
            result = await github_manager.create_issue(
                owner=args.owner,
                repo=args.repo,
                title=args.title,
                body=args.body
            )
            logger.info(f"Created issue: {json.dumps(result, indent=2)}")

        elif args.action == "list-issues":
            if not args.owner or not args.repo:
                logger.error("Owner and repo are required for list-issues action")
                return

            logger.info(f"Listing issues in {args.owner}/{args.repo}...")
            result = await github_manager.list_issues(args.owner, args.repo)
            logger.info(f"Issues: {json.dumps(result, indent=2)}")

        elif args.action == "create-pr":
            if not args.owner or not args.repo or not args.title or not args.head:
                logger.error("Owner, repo, title, and head are required for create-pr action")
                return

            logger.info(f"Creating PR in {args.owner}/{args.repo}...")
            result = await github_manager.create_pull_request(
                owner=args.owner,
                repo=args.repo,
                title=args.title,
                body=args.body,
                base=args.base,
                head=args.head
            )
            logger.info(f"Created PR: {json.dumps(result, indent=2)}")

        elif args.action == "list-prs":
            if not args.owner or not args.repo:
                logger.error("Owner and repo are required for list-prs action")
                return

            logger.info(f"Listing PRs in {args.owner}/{args.repo}...")
            result = await github_manager.list_pull_requests(args.owner, args.repo)
            logger.info(f"PRs: {json.dumps(result, indent=2)}")

        # Close all sessions
        logger.info("Closing all sessions...")
        await mcp_manager.close_all()

        logger.info("Test completed successfully!")

    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
