# agents/implemtations/browser_use.py
import logging
from typing import Optional

from utils.protocols import A2ATaskContext, A2ATaskResult
from utils.models import A2AArtifact, A2ATextPart, A2ADataPart, A2AMessage
from agents.specialized import APIA_SpecializedAgent

logger = logging.getLogger(__name__)

class APIA_BrowserUseAgent(APIA_SpecializedAgent):
    """
    Browser Use Agent for interacting with web content.

    This agent specializes in browser automation tasks such as:
    - Web searching and information gathering
    - Navigating to websites
    - Extracting content from web pages
    - Interacting with web elements
    - Taking screenshots of web pages
    """

    async def _initialize_domain_resources(self):
        """Initialize browser resources."""
        # MCP server name for Puppeteer
        self.mcp_server = "puppeteer"
        self.mcp_available = False

        # Check if MCP server is available
        try:
            # Check if Puppeteer MCP server is configured
            mcp_servers = self.a2a_client.mcp.get_servers()

            if self.mcp_server not in mcp_servers:
                logger.warning(f"{self.mcp_server} MCP server not found in configuration")
                logger.info("Adding Puppeteer MCP server configuration")

                # Add Puppeteer MCP server configuration
                self.a2a_client.mcp.add_server(
                    self.mcp_server,
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-puppeteer"]
                )

            # Test connection to MCP server
            result = await self.a2a_client.mcp.call_tool(
                self.mcp_server,
                "getVersion",
                {}
            )
            logger.info(f"Connected to Puppeteer MCP server: {result}")
            self.mcp_available = True
        except Exception as e:
            logger.error(f"Failed to connect to Puppeteer MCP server: {e}")
            logger.warning("BrowserUseAgent will have limited functionality without Puppeteer MCP server")

        logger.info(f"BrowserUseAgent ({self.id}) initialized domain resources (MCP available: {self.mcp_available})")

        # Initialize fallback responses for when MCP is not available
        self._fallback_responses = {
            "search_web": "I'm unable to search the web at the moment as the browser service is not available.",
            "navigate_to_url": "I'm unable to navigate to the URL as the browser service is not available.",
            "extract_content": "I'm unable to extract content as the browser service is not available.",
            "interact_with_page": "I'm unable to interact with the page as the browser service is not available.",
            "take_screenshot": "I'm unable to take a screenshot as the browser service is not available."
        }

    async def _register_skills(self):
        """Register browser-specific skills."""
        await super()._register_skills()

        # Register browser-specific skills
        self._skill_registry.update({
            "search_web": {
                "name": "Search Web",
                "description": "Search the web for information",
                "examples": [
                    "Search for information about artificial intelligence",
                    "Find the latest news about climate change"
                ]
            },
            "navigate_to_url": {
                "name": "Navigate to URL",
                "description": "Navigate to a specific URL",
                "examples": [
                    "Navigate to https://www.example.com",
                    "Go to the Wikipedia page for quantum computing"
                ]
            },
            "extract_content": {
                "name": "Extract Content",
                "description": "Extract content from a web page",
                "examples": [
                    "Extract the main article text from the current page",
                    "Get all links from the navigation menu"
                ]
            },
            "interact_with_page": {
                "name": "Interact with Page",
                "description": "Interact with elements on a web page",
                "examples": [
                    "Click the login button",
                    "Fill out the contact form"
                ]
            },
            "take_screenshot": {
                "name": "Take Screenshot",
                "description": "Take a screenshot of a web page",
                "examples": [
                    "Take a screenshot of the entire page",
                    "Capture an image of the pricing table"
                ]
            }
        })

    async def _handle_domain_task(self, context: A2ATaskContext, subtask_id: str,
                                 subtask_description: str) -> A2ATaskResult:
        """
        Handle browser-related tasks.

        Args:
            context: Task context
            subtask_id: ID of the subtask
            subtask_description: Description of the subtask

        Returns:
            Task result with browser operation results
        """
        # Determine the skill to use based on context
        skill_id = context.metadata.get("skill_id") if context.metadata else None

        if not skill_id:
            # Try to determine skill from description
            if "search" in subtask_description.lower():
                skill_id = "search_web"
            elif "navigate" in subtask_description.lower() or "go to" in subtask_description.lower():
                skill_id = "navigate_to_url"
            elif "extract" in subtask_description.lower() or "get content" in subtask_description.lower():
                skill_id = "extract_content"
            elif "interact" in subtask_description.lower() or "click" in subtask_description.lower() or "fill" in subtask_description.lower():
                skill_id = "interact_with_page"
            elif "screenshot" in subtask_description.lower() or "capture" in subtask_description.lower():
                skill_id = "take_screenshot"
            else:
                # Default to search if we can't determine
                skill_id = "search_web"

        # Call the appropriate handler based on the skill
        if skill_id == "search_web":
            return await self._handle_search_web(context, subtask_id, subtask_description)
        elif skill_id == "navigate_to_url":
            return await self._handle_navigate_to_url(context, subtask_id, subtask_description)
        elif skill_id == "extract_content":
            return await self._handle_extract_content(context, subtask_id, subtask_description)
        elif skill_id == "interact_with_page":
            return await self._handle_interact_with_page(context, subtask_id, subtask_description)
        elif skill_id == "take_screenshot":
            return await self._handle_take_screenshot(context, subtask_id, subtask_description)
        else:
            return A2ATaskResult(
                status="failed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text=f"Unknown skill: {skill_id}")]
                )
            )

    async def _handle_search_web(self, context: A2ATaskContext, subtask_id: str,
                               subtask_description: str) -> A2ATaskResult:
        """Handle web search tasks."""
        # Check if MCP is available
        if not self.mcp_available:
            return A2ATaskResult(
                status="failed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text=self._fallback_responses["search_web"])]
                )
            )

        # Extract search query
        query = None

        if context.get_text_parts():
            query = context.get_text_parts()[0]
        elif context.get_data_parts():
            data = context.get_data_parts()[0]
            if "query" in data:
                query = data["query"]

        if not query:
            # Try to extract query from description
            if "search for" in subtask_description.lower():
                query = subtask_description.lower().split("search for", 1)[1].strip()
            elif "find" in subtask_description.lower():
                query = subtask_description.lower().split("find", 1)[1].strip()
            else:
                query = subtask_description

        await context.update_status("working", message_text=f"Searching for: {query}")

        try:
            # Use Puppeteer MCP to perform search
            search_results = await self.a2a_client.mcp.call_tool(
                self.mcp_server,
                "searchWeb",
                {"query": query, "numResults": 5}
            )

            # Format search results
            formatted_results = f"# Search Results for: {query}\n\n"

            if isinstance(search_results, list):
                for i, result in enumerate(search_results, 1):
                    title = result.get("title", "No title")
                    url = result.get("url", "#")
                    snippet = result.get("snippet", "No description available")

                    formatted_results += f"## {i}. [{title}]({url})\n\n"
                    formatted_results += f"{snippet}\n\n"
            else:
                formatted_results += "No results found or invalid response format."

            return A2ATaskResult(
                status="completed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text=f"Completed search for: {query}")]
                ),
                artifacts=[
                    A2AArtifact(
                        name=f"search_results_{subtask_id}",
                        description=f"Search results for: {query}",
                        parts=[
                            A2ATextPart(text=formatted_results),
                            A2ADataPart(data=search_results)
                        ]
                    )
                ]
            )
        except Exception as e:
            logger.error(f"Error during web search: {e}")
            return A2ATaskResult(
                status="failed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text=f"Failed to search for '{query}': {e}")]
                )
            )

    async def _handle_navigate_to_url(self, context: A2ATaskContext, subtask_id: str,
                                    subtask_description: str) -> A2ATaskResult:
        """Handle URL navigation tasks."""
        # Check if MCP is available
        if not self.mcp_available:
            return A2ATaskResult(
                status="failed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text=self._fallback_responses["navigate_to_url"])]
                )
            )

        # Extract URL
        url = None

        if context.get_text_parts():
            url = context.get_text_parts()[0]
        elif context.get_data_parts():
            data = context.get_data_parts()[0]
            if "url" in data:
                url = data["url"]

        if not url:
            # Try to extract URL from description
            import re
            url_match = re.search(r'https?://\S+', subtask_description)
            if url_match:
                url = url_match.group(0)
            elif "navigate to" in subtask_description.lower():
                url = subtask_description.lower().split("navigate to", 1)[1].strip()
            elif "go to" in subtask_description.lower():
                url = subtask_description.lower().split("go to", 1)[1].strip()
            else:
                return A2ATaskResult(
                    status="failed",
                    message=A2AMessage(
                        role="agent",
                        parts=[A2ATextPart(text="No URL provided")]
                    )
                )

        # Ensure URL has protocol
        if not url.startswith("http"):
            url = "https://" + url

        await context.update_status("working", message_text=f"Navigating to: {url}")

        try:
            # Use Puppeteer MCP to navigate to URL
            navigation_result = await self.a2a_client.mcp.call_tool(
                self.mcp_server,
                "navigateTo",
                {"url": url}
            )

            # Take a screenshot of the page
            screenshot_result = await self.a2a_client.mcp.call_tool(
                self.mcp_server,
                "takeScreenshot",
                {}
            )

            # Get page title and content
            page_info = await self.a2a_client.mcp.call_tool(
                self.mcp_server,
                "getPageInfo",
                {}
            )

            return A2ATaskResult(
                status="completed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text=f"Successfully navigated to: {url}")]
                ),
                artifacts=[
                    A2AArtifact(
                        name=f"navigation_result_{subtask_id}",
                        description=f"Navigation to {url}",
                        parts=[
                            A2ATextPart(text=f"# Page: {page_info.get('title', url)}\n\nSuccessfully navigated to {url}"),
                            A2ADataPart(data={
                                "url": url,
                                "title": page_info.get("title"),
                                "screenshot": screenshot_result.get("screenshot"),
                                "navigation_info": navigation_result
                            })
                        ]
                    )
                ]
            )
        except Exception as e:
            logger.error(f"Error during navigation to {url}: {e}")
            return A2ATaskResult(
                status="failed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text=f"Failed to navigate to '{url}': {e}")]
                )
            )

    async def _handle_extract_content(self, context: A2ATaskContext, subtask_id: str,
                                    subtask_description: str) -> A2ATaskResult:
        """Handle content extraction tasks."""
        # Check if MCP is available
        if not self.mcp_available:
            return A2ATaskResult(
                status="failed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text=self._fallback_responses["extract_content"])]
                )
            )

        # Extract selectors
        selectors = {}

        if context.get_data_parts():
            data = context.get_data_parts()[0]
            if "selectors" in data:
                selectors = data["selectors"]

        # If no selectors provided, extract common content
        if not selectors:
            selectors = {
                "title": "title",
                "headings": "h1, h2, h3",
                "main_content": "main, article, .content, #content",
                "links": "a"
            }

        await context.update_status("working", message_text="Extracting content from page...")

        try:
            # Use Puppeteer MCP to extract content
            extraction_results = {}

            for name, selector in selectors.items():
                try:
                    result = await self.a2a_client.mcp.call_tool(
                        self.mcp_server,
                        "extractContent",
                        {"selector": selector}
                    )
                    extraction_results[name] = result
                except Exception as e:
                    logger.warning(f"Failed to extract {name} with selector '{selector}': {e}")
                    extraction_results[name] = {"error": str(e)}

            # Format extraction results
            formatted_results = "# Extracted Content\n\n"

            for name, result in extraction_results.items():
                formatted_results += f"## {name.replace('_', ' ').title()}\n\n"

                if "error" in result:
                    formatted_results += f"Error: {result['error']}\n\n"
                elif "content" in result:
                    if isinstance(result["content"], list):
                        for item in result["content"]:
                            formatted_results += f"- {item}\n"
                    else:
                        formatted_results += f"{result['content']}\n\n"
                else:
                    formatted_results += "No content extracted\n\n"

            return A2ATaskResult(
                status="completed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text="Content extraction completed")]
                ),
                artifacts=[
                    A2AArtifact(
                        name=f"extracted_content_{subtask_id}",
                        description="Extracted web page content",
                        parts=[
                            A2ATextPart(text=formatted_results),
                            A2ADataPart(data=extraction_results)
                        ]
                    )
                ]
            )
        except Exception as e:
            logger.error(f"Error during content extraction: {e}")
            return A2ATaskResult(
                status="failed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text=f"Failed to extract content: {e}")]
                )
            )

    async def _handle_interact_with_page(self, context: A2ATaskContext, subtask_id: str,
                                       subtask_description: str) -> A2ATaskResult:
        """Handle page interaction tasks."""
        # Check if MCP is available
        if not self.mcp_available:
            return A2ATaskResult(
                status="failed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text=self._fallback_responses["interact_with_page"])]
                )
            )

        # Extract actions
        actions = []

        if context.get_data_parts():
            data = context.get_data_parts()[0]
            if "actions" in data:
                actions = data["actions"]

        if not actions:
            # Try to determine action from description
            if "click" in subtask_description.lower():
                element = subtask_description.lower().split("click", 1)[1].strip()
                actions = [{"type": "click", "selector": f"text={element}"}]
            elif "type" in subtask_description.lower() or "fill" in subtask_description.lower():
                parts = subtask_description.lower().replace("type", "fill").split("fill", 1)[1].strip()
                if " with " in parts:
                    element, text = parts.split(" with ", 1)
                    actions = [{"type": "fill", "selector": f"text={element}", "text": text}]

            # If still no actions, return error
            if not actions:
                return A2ATaskResult(
                    status="failed",
                    message=A2AMessage(
                        role="agent",
                        parts=[A2ATextPart(text="No interaction actions provided")]
                    )
                )

        await context.update_status("working", message_text="Interacting with page...")

        try:
            # Use Puppeteer MCP to perform interactions
            interaction_results = []

            for action in actions:
                action_type = action.get("type")
                selector = action.get("selector")

                if action_type == "click":
                    result = await self.a2a_client.mcp.call_tool(
                        self.mcp_server,
                        "clickElement",
                        {"selector": selector}
                    )
                    interaction_results.append({
                        "type": "click",
                        "selector": selector,
                        "result": result
                    })
                elif action_type == "fill":
                    text = action.get("text", "")
                    result = await self.a2a_client.mcp.call_tool(
                        self.mcp_server,
                        "fillForm",
                        {"selector": selector, "text": text}
                    )
                    interaction_results.append({
                        "type": "fill",
                        "selector": selector,
                        "text": text,
                        "result": result
                    })
                elif action_type == "select":
                    value = action.get("value", "")
                    result = await self.a2a_client.mcp.call_tool(
                        self.mcp_server,
                        "selectOption",
                        {"selector": selector, "value": value}
                    )
                    interaction_results.append({
                        "type": "select",
                        "selector": selector,
                        "value": value,
                        "result": result
                    })

            # Take a screenshot after interactions
            screenshot_result = await self.a2a_client.mcp.call_tool(
                self.mcp_server,
                "takeScreenshot",
                {}
            )

            return A2ATaskResult(
                status="completed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text=f"Completed {len(interaction_results)} page interactions")]
                ),
                artifacts=[
                    A2AArtifact(
                        name=f"interaction_results_{subtask_id}",
                        description="Page interaction results",
                        parts=[
                            A2ATextPart(text=f"# Page Interaction Results\n\nCompleted {len(interaction_results)} interactions"),
                            A2ADataPart(data={
                                "interactions": interaction_results,
                                "screenshot": screenshot_result.get("screenshot")
                            })
                        ]
                    )
                ]
            )
        except Exception as e:
            logger.error(f"Error during page interaction: {e}")
            return A2ATaskResult(
                status="failed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text=f"Failed to interact with page: {e}")]
                )
            )

    async def _handle_take_screenshot(self, context: A2ATaskContext, subtask_id: str,
                                    subtask_description: str) -> A2ATaskResult:
        """Handle screenshot tasks."""
        # Check if MCP is available
        if not self.mcp_available:
            return A2ATaskResult(
                status="failed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text=self._fallback_responses["take_screenshot"])]
                )
            )

        # Extract selector
        selector = None

        if context.get_text_parts():
            selector = context.get_text_parts()[0]
        elif context.get_data_parts():
            data = context.get_data_parts()[0]
            if "selector" in data:
                selector = data["selector"]

        await context.update_status("working", message_text="Taking screenshot...")

        try:
            # Use Puppeteer MCP to take screenshot
            screenshot_params = {}
            if selector:
                screenshot_params["selector"] = selector

            screenshot_result = await self.a2a_client.mcp.call_tool(
                self.mcp_server,
                "takeScreenshot",
                screenshot_params
            )

            # Get page info
            page_info = await self.a2a_client.mcp.call_tool(
                self.mcp_server,
                "getPageInfo",
                {}
            )

            # Create a description of what was captured
            if selector:
                screenshot_description = f"Screenshot of element matching '{selector}'"
            else:
                screenshot_description = f"Screenshot of page: {page_info.get('title', 'Unknown page')}"

            return A2ATaskResult(
                status="completed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text=f"Screenshot captured successfully")]
                ),
                artifacts=[
                    A2AArtifact(
                        name=f"screenshot_{subtask_id}",
                        description=screenshot_description,
                        parts=[
                            A2ATextPart(text=f"# {screenshot_description}\n\nURL: {page_info.get('url', 'Unknown URL')}"),
                            A2ADataPart(data={
                                "screenshot": screenshot_result.get("screenshot"),
                                "page_info": page_info
                            })
                        ]
                    )
                ]
            )
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return A2ATaskResult(
                status="failed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text=f"Failed to take screenshot: {e}")]
                )
            )
