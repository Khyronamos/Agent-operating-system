import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import logging
import argparse
import json
from utils.config import load_config_from_yaml
from utils.protocols import MCPClientManager
from utils.sequential_thinking_manager import SequentialThinkingManager

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        # Parse arguments
        parser = argparse.ArgumentParser(description="Test Sequential Thinking MCP server")
        parser.add_argument("--action", default="list",
                          choices=["list", "solve-problem", "analyze-code", "design-system", "custom"],
                          help="Action to perform")
        parser.add_argument("--problem", help="Problem to solve")
        parser.add_argument("--code", help="Code to analyze")
        parser.add_argument("--system", help="System to design")
        parser.add_argument("--custom-prompt", help="Custom prompt for sequential thinking")
        parser.add_argument("--steps", type=int, default=5, help="Number of steps for sequential thinking")
        args = parser.parse_args()

        # Load configuration
        logger.info("Loading configuration...")
        settings = load_config_from_yaml("config/config.yaml")

        # Initialize MCP client manager
        logger.info("Initializing MCP client manager...")
        mcp_manager = MCPClientManager(config=settings.mcp_servers)

        # Initialize Sequential Thinking manager
        logger.info("Initializing Sequential Thinking manager...")
        thinking_manager = SequentialThinkingManager(mcp_manager)

        # Test Sequential Thinking MCP server
        server_name = "sequential-thinking"
        logger.info(f"Testing {server_name} MCP server...")

        # List available tools
        logger.info(f"Listing tools for {server_name}...")
        tools = await mcp_manager.list_tools(server_name)
        logger.info(f"Available tools: {tools}")

        # Perform requested action
        if args.action == "list":
            logger.info("Listing available tools...")
            # Already done above

        elif args.action == "solve-problem":
            if not args.problem:
                # Use default problem if none provided
                problem = "How can we optimize a website's loading time while maintaining all its functionality?"
            else:
                problem = args.problem

            logger.info(f"Solving problem: {problem}")
            result = await thinking_manager.solve_problem(problem, args.steps)
            logger.info(f"Solution: {json.dumps(result, indent=2)}")

        elif args.action == "analyze-code":
            if not args.code:
                # Use default code if none provided
                code = """
def fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]

    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])

    return fib
"""
            else:
                code = args.code

            logger.info(f"Analyzing code: {code}")
            result = await thinking_manager.analyze_code(code, args.steps)
            logger.info(f"Analysis: {json.dumps(result, indent=2)}")

        elif args.action == "design-system":
            if not args.system:
                # Use default system if none provided
                system = "Design a microservice architecture for an e-commerce platform"
            else:
                system = args.system

            logger.info(f"Designing system: {system}")
            result = await thinking_manager.design_system(system, args.steps)
            logger.info(f"Design: {json.dumps(result, indent=2)}")

        elif args.action == "custom":
            if not args.custom_prompt:
                logger.error("Custom prompt is required for custom action")
                return

            logger.info(f"Running custom sequential thinking: {args.custom_prompt}")
            result = await thinking_manager.sequential_thinking(args.custom_prompt, args.steps)
            logger.info(f"Result: {json.dumps(result, indent=2)}")

        # Close all sessions
        logger.info("Closing all sessions...")
        await mcp_manager.close_all()

        logger.info("Test completed successfully!")

    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
