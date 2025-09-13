import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import logging
import argparse
import json
from utils.config import load_config_from_yaml
from utils.protocols import MCPClientManager
from utils.e2b_manager import E2BManager

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        # Parse arguments
        parser = argparse.ArgumentParser(description="Test E2B MCP server")
        parser.add_argument("--action", default="list",
                          choices=["list", "run-python", "run-node", "run-bash", "filesystem"],
                          help="Action to perform")
        parser.add_argument("--code", help="Code to execute")
        parser.add_argument("--file", help="File to read or write")
        parser.add_argument("--content", help="Content to write to file")
        args = parser.parse_args()

        # Load configuration
        logger.info("Loading configuration...")
        settings = load_config_from_yaml("config/config.yaml")

        # Initialize MCP client manager
        logger.info("Initializing MCP client manager...")
        mcp_manager = MCPClientManager(config=settings.mcp_servers)

        # Initialize E2B manager
        logger.info("Initializing E2B manager...")
        e2b_manager = E2BManager(mcp_manager)

        # Test E2B MCP server
        server_name = "e2b"
        logger.info(f"Testing {server_name} MCP server...")

        # List available tools
        logger.info(f"Listing tools for {server_name}...")
        tools = await mcp_manager.list_tools(server_name)
        logger.info(f"Available tools: {tools}")

        # Perform requested action
        if args.action == "list":
            logger.info("Listing available tools...")
            # Already done above

        elif args.action == "run-python":
            if not args.code:
                # Use default Python code if none provided
                code = """
import math

def calculate_circle_area(radius):
    return math.pi * radius ** 2

# Calculate area of a circle with radius 5
radius = 5
area = calculate_circle_area(radius)
print(f"The area of a circle with radius {radius} is {area:.2f}")

# Calculate area of a circle with radius 10
radius = 10
area = calculate_circle_area(radius)
print(f"The area of a circle with radius {radius} is {area:.2f}")
"""
            else:
                code = args.code

            logger.info("Running Python code...")
            result = await e2b_manager.run_python(code)
            logger.info(f"Python execution result: {json.dumps(result, indent=2)}")

        elif args.action == "run-node":
            if not args.code:
                # Use default Node.js code if none provided
                code = """
function calculateCircleArea(radius) {
    return Math.PI * radius ** 2;
}

// Calculate area of a circle with radius 5
const radius1 = 5;
const area1 = calculateCircleArea(radius1);
console.log(`The area of a circle with radius ${radius1} is ${area1.toFixed(2)}`);

// Calculate area of a circle with radius 10
const radius2 = 10;
const area2 = calculateCircleArea(radius2);
console.log(`The area of a circle with radius ${radius2} is ${area2.toFixed(2)}`);
"""
            else:
                code = args.code

            logger.info("Running Node.js code...")
            result = await e2b_manager.run_node(code)
            logger.info(f"Node.js execution result: {json.dumps(result, indent=2)}")

        elif args.action == "run-bash":
            if not args.code:
                # Use default Bash code if none provided
                code = """
#!/bin/bash
echo "Current directory:"
pwd

echo "Files in current directory:"
ls -la

echo "System information:"
uname -a

echo "Memory usage:"
free -h

echo "Disk usage:"
df -h
"""
            else:
                code = args.code

            logger.info("Running Bash code...")
            result = await e2b_manager.run_bash(code)
            logger.info(f"Bash execution result: {json.dumps(result, indent=2)}")

        elif args.action == "filesystem":
            if not args.file:
                logger.error("File path is required for filesystem action")
                return

            if args.content:
                # Write to file
                logger.info(f"Writing to file {args.file}...")
                result = await e2b_manager.write_file(args.file, args.content)
                logger.info(f"Write result: {json.dumps(result, indent=2)}")

                # Read the file back
                logger.info(f"Reading file {args.file}...")
                result = await e2b_manager.read_file(args.file)
                logger.info(f"Read result: {json.dumps(result, indent=2)}")
            else:
                # Read file
                logger.info(f"Reading file {args.file}...")
                result = await e2b_manager.read_file(args.file)
                logger.info(f"Read result: {json.dumps(result, indent=2)}")

        # Close all sessions
        logger.info("Closing all sessions...")
        await mcp_manager.close_all()

        logger.info("Test completed successfully!")

    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
