import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import logging
import argparse
from utils.config import load_config_from_yaml
from utils.protocols import MCPClientManager
from utils.code_review_manager import CodeReviewManager

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def review_code(code_review_manager, code, language, review_type):
    """Review code using the code review manager."""
    logger.info(f"Reviewing {language} code with {review_type} review type...")
    result = await code_review_manager.review_code(code, language, review_type)
    return result

async def review_file(code_review_manager, file_path, review_type):
    """Review a file using the code review manager."""
    logger.info(f"Reviewing file {file_path} with {review_type} review type...")
    result = await code_review_manager.review_file(file_path, review_type)
    return result

async def suggest_improvements(code_review_manager, code, language):
    """Suggest improvements for code."""
    logger.info(f"Suggesting improvements for {language} code...")
    result = await code_review_manager.suggest_improvements(code, language)
    return result

async def check_security(code_review_manager, code, language):
    """Check code for security vulnerabilities."""
    logger.info(f"Checking {language} code for security vulnerabilities...")
    result = await code_review_manager.check_security(code, language)
    return result

async def analyze_complexity(code_review_manager, code, language):
    """Analyze code complexity."""
    logger.info(f"Analyzing complexity of {language} code...")
    result = await code_review_manager.analyze_complexity(code, language)
    return result

async def check_style(code_review_manager, code, language):
    """Check code style."""
    logger.info(f"Checking style of {language} code...")
    result = await code_review_manager.check_style(code, language)
    return result

async def main():
    try:
        # Parse arguments
        parser = argparse.ArgumentParser(description="Test Code Review MCP server")
        parser.add_argument("--file", help="Path to file to review")
        parser.add_argument("--language", default="python", help="Programming language")
        parser.add_argument("--review-type", default="general", help="Review type")
        parser.add_argument("--action", default="review",
                          choices=["review", "improve", "security", "complexity", "style"],
                          help="Action to perform")
        args = parser.parse_args()

        # Load configuration
        logger.info("Loading configuration...")
        settings = load_config_from_yaml("config/config.yaml")

        # Initialize MCP client manager
        logger.info("Initializing MCP client manager...")
        mcp_manager = MCPClientManager(config=settings.mcp_servers)

        # Initialize code review manager
        logger.info("Initializing code review manager...")
        code_review_manager = CodeReviewManager(mcp_manager)

        # Sample code to review if no file is provided
        sample_code = """
def calculate_sum(a, b):
    # This function calculates the sum of two numbers
    return a + b

def calculate_average(numbers):
    # This function calculates the average of a list of numbers
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)

# Example usage
result = calculate_sum(5, 10)
print(f"Sum: {result}")

numbers = [1, 2, 3, 4, 5]
average = calculate_average(numbers)
print(f"Average: {average}")
"""

        # Get code from file or use sample code
        if args.file:
            result = await review_file(code_review_manager, args.file, args.review_type)
        else:
            # Perform requested action
            if args.action == "review":
                result = await review_code(code_review_manager, sample_code, args.language, args.review_type)
            elif args.action == "improve":
                result = await suggest_improvements(code_review_manager, sample_code, args.language)
            elif args.action == "security":
                result = await check_security(code_review_manager, sample_code, args.language)
            elif args.action == "complexity":
                result = await analyze_complexity(code_review_manager, sample_code, args.language)
            elif args.action == "style":
                result = await check_style(code_review_manager, sample_code, args.language)

        # Print result
        logger.info(f"Result: {result}")

        # Close all sessions
        logger.info("Closing all sessions...")
        await mcp_manager.close_all()

        logger.info("Test completed successfully!")

    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
