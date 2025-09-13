#!/usr/bin/env python3
"""
Test script for the Browser Use agent.

This script demonstrates how to use the Browser Use agent to interact with web content.
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.models import A2AMessage, A2ATextPart, A2ADataPart, A2ATaskSendParams
from utils.protocols import A2AClientManager
from core.framework import APIA_KnowledgeBase, APIA_AgentRegistry
from agents.implemtations.browser_use import APIA_BrowserUseAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_search_web():
    """Test the Browser Use agent's web search capability."""
    logger.info("Testing web search...")

    # Create dependencies
    knowledge_base = APIA_KnowledgeBase()
    agent_registry = APIA_AgentRegistry()

    # Create A2A client with explicit MCP configuration
    a2a_client = A2AClientManager()

    # Check if Puppeteer MCP server is available
    try:
        # Try to get MCP server info
        mcp_servers = a2a_client.mcp.get_servers()
        logger.info(f"Available MCP servers: {mcp_servers}")

        if "puppeteer" not in mcp_servers:
            logger.warning("Puppeteer MCP server not found in configuration")
            logger.info("Adding Puppeteer MCP server configuration")

            # Add Puppeteer MCP server configuration
            a2a_client.mcp.add_server(
                "puppeteer",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-puppeteer"]
            )
    except Exception as e:
        logger.error(f"Error checking MCP servers: {e}")
        logger.warning("Tests may fail if Puppeteer MCP server is not available")

    # Create Browser Use agent
    browser_agent = APIA_BrowserUseAgent(
        role="browser_use",
        agent_id="browser-use-test-agent",
        knowledge_base=knowledge_base,
        agent_registry=agent_registry,
        a2a_client=a2a_client,
        internal_skills=[],
        a2a_skills=[]
    )

    # Create memory directory
    memory_dir = os.path.join(os.path.dirname(__file__), "memory")
    os.makedirs(memory_dir, exist_ok=True)

    # Initialize the agent with memory
    await browser_agent.initialize(memory_dir=memory_dir)

    # Create a task context for web search
    search_query = "APIA agent framework"

    # Create a message with the search query
    message = A2AMessage(
        role="user",
        parts=[A2ATextPart(text=search_query)],
        metadata={
            "subtask_id": "search_task_1",
            "plan_id": "test_plan",
            "skill_id": "search_web"
        }
    )

    # Create task parameters
    task_params = A2ATaskSendParams(
        id="task_1",
        message=message
    )

    # Call the Browser Use agent's search skill
    task_context = await browser_agent.create_task_context(task_params)
    result = await browser_agent.handle_subtask_skill(task_context)

    # Print the result
    logger.info(f"Web search result: {result.status}")

    # Extract search results
    search_results = None
    for artifact in result.artifacts:
        if artifact.name.startswith("search_results_"):
            for part in artifact.parts:
                if hasattr(part, 'text'):
                    logger.info(f"Search results text: {part.text[:500]}...")
                elif hasattr(part, 'data'):
                    search_results = part.data
                    logger.info(f"Found {len(search_results)} search results")

    if not search_results:
        logger.error("No search results found")

    return browser_agent

async def test_navigate_and_screenshot(browser_agent):
    """Test the Browser Use agent's navigation and screenshot capabilities."""
    logger.info("Testing navigation and screenshot...")

    # Create a task context for navigation
    url = "https://github.com"

    # Create a message with the URL
    message = A2AMessage(
        role="user",
        parts=[A2ATextPart(text=url)],
        metadata={
            "subtask_id": "navigate_task_1",
            "plan_id": "test_plan",
            "skill_id": "navigate_to_url"
        }
    )

    # Create task parameters
    task_params = A2ATaskSendParams(
        id="task_2",
        message=message
    )

    # Call the Browser Use agent's navigation skill
    task_context = await browser_agent.create_task_context(task_params)
    result = await browser_agent.handle_subtask_skill(task_context)

    # Print the result
    logger.info(f"Navigation result: {result.status}")

    # Extract navigation results
    navigation_result = None
    for artifact in result.artifacts:
        if artifact.name.startswith("navigation_result_"):
            for part in artifact.parts:
                if hasattr(part, 'data'):
                    navigation_result = part.data
                    logger.info(f"Navigated to: {navigation_result.get('url')}")
                    logger.info(f"Page title: {navigation_result.get('title')}")

    if not navigation_result:
        logger.error("No navigation result found")

    # Now take a screenshot
    message = A2AMessage(
        role="user",
        parts=[A2ATextPart(text="Take a screenshot of the page")],
        metadata={
            "subtask_id": "screenshot_task_1",
            "plan_id": "test_plan",
            "skill_id": "take_screenshot"
        }
    )

    # Create task parameters
    task_params = A2ATaskSendParams(
        id="task_3",
        message=message
    )

    # Call the Browser Use agent's screenshot skill
    task_context = await browser_agent.create_task_context(task_params)
    result = await browser_agent.handle_subtask_skill(task_context)

    # Print the result
    logger.info(f"Screenshot result: {result.status}")

    # Extract screenshot
    screenshot_data = None
    for artifact in result.artifacts:
        if artifact.name.startswith("screenshot_"):
            for part in artifact.parts:
                if hasattr(part, 'data'):
                    screenshot_data = part.data
                    logger.info("Screenshot captured successfully")

    if not screenshot_data:
        logger.error("No screenshot data found")

async def test_extract_content(browser_agent):
    """Test the Browser Use agent's content extraction capability."""
    logger.info("Testing content extraction...")

    # Create a task context for content extraction
    message = A2AMessage(
        role="user",
        parts=[A2ATextPart(text="Extract content from the current page")],
        metadata={
            "subtask_id": "extract_task_1",
            "plan_id": "test_plan",
            "skill_id": "extract_content"
        }
    )

    # Create task parameters
    task_params = A2ATaskSendParams(
        id="task_4",
        message=message
    )

    # Call the Browser Use agent's content extraction skill
    task_context = await browser_agent.create_task_context(task_params)
    result = await browser_agent.handle_subtask_skill(task_context)

    # Print the result
    logger.info(f"Content extraction result: {result.status}")

    # Extract content
    extraction_results = None
    for artifact in result.artifacts:
        if artifact.name.startswith("extracted_content_"):
            for part in artifact.parts:
                if hasattr(part, 'text'):
                    logger.info(f"Extracted content text: {part.text[:500]}...")
                elif hasattr(part, 'data'):
                    extraction_results = part.data
                    logger.info(f"Extracted content from {len(extraction_results)} selectors")

    if not extraction_results:
        logger.error("No extraction results found")

async def main():
    """Main function to run the tests."""
    try:
        browser_agent = await test_search_web()
        logger.info("\n" + "=" * 80 + "\n")
        await test_navigate_and_screenshot(browser_agent)
        logger.info("\n" + "=" * 80 + "\n")
        await test_extract_content(browser_agent)
    except Exception as e:
        logger.exception(f"Error during test: {e}")

if __name__ == "__main__":
    asyncio.run(main())
