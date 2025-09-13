import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import logging
import argparse
import json
from utils.config import load_config_from_yaml
from utils.protocols import MCPClientManager
from utils.starwind_ui_manager import StarwindUIManager

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        # Parse arguments
        parser = argparse.ArgumentParser(description="Test Starwind UI MCP server")
        parser.add_argument("--action", default="list",
                          choices=["list", "generate", "preview"],
                          help="Action to perform")
        parser.add_argument("--component", default="landing-page",
                          help="Component type to generate")
        parser.add_argument("--business-name", help="Business name")
        parser.add_argument("--business-type", help="Business type")
        parser.add_argument("--description", help="Business description")
        parser.add_argument("--color-scheme", default="blue",
                          help="Color scheme (blue, green, red, purple, etc.)")
        parser.add_argument("--output", default="output.html",
                          help="Output file path")
        args = parser.parse_args()

        # Load configuration
        logger.info("Loading configuration...")
        settings = load_config_from_yaml("config/config.yaml")

        # Initialize MCP client manager
        logger.info("Initializing MCP client manager...")
        mcp_manager = MCPClientManager(config=settings.mcp_servers)

        # Initialize Starwind UI manager
        logger.info("Initializing Starwind UI manager...")
        ui_manager = StarwindUIManager(mcp_manager)

        # Perform requested action
        if args.action == "list":
            logger.info("Listing available components...")
            result = await ui_manager.list_components()
            logger.info(f"Available components: {result}")

        elif args.action == "generate":
            if not args.business_name or not args.business_type:
                logger.error("Business name and type are required for generate action")
                return

            logger.info(f"Generating {args.component} for {args.business_name}...")

            if args.component == "landing-page":
                result = await ui_manager.generate_landing_page(
                    business_name=args.business_name,
                    business_type=args.business_type,
                    description=args.description,
                    color_scheme=args.color_scheme
                )
            else:
                # For other component types
                component_params = {
                    "businessName": args.business_name,
                    "businessType": args.business_type,
                    "colorScheme": args.color_scheme
                }

                if args.description:
                    component_params["description"] = args.description

                result = await ui_manager.generate_component(
                    component_type=args.component,
                    params=component_params
                )

            # Save the generated HTML
            await ui_manager.save_component(result, args.output)

            logger.info(f"Generated component saved to {args.output}")

            # Print component details
            logger.info(f"Component details: {json.dumps(result, indent=2)}")

        elif args.action == "preview":
            if not os.path.exists(args.output):
                logger.error(f"Output file {args.output} does not exist")
                return

            logger.info(f"Previewing {args.output}...")

            # Read the HTML file
            with open(args.output, "r", encoding="utf-8") as f:
                html_content = f.read()

            # Generate a preview URL
            result = await ui_manager.preview_component(html_content)

            logger.info(f"Preview URL: {result['previewUrl']}")

        # Close all sessions
        logger.info("Closing all sessions...")
        await mcp_manager.close_all()

        logger.info("Test completed successfully!")

    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
