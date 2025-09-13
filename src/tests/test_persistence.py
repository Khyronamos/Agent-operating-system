#!/usr/bin/env python3
"""
Test script for the persistence layer.

This script demonstrates how to use the persistence layer to store and retrieve
data in the Knowledge Base and agent memory.
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.config import load_settings
from utils.persistence import initialize_database_manager
from core.framework import APIA_KnowledgeBase
from utils.memory import AgentMemory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_knowledge_base_persistence():
    """Test the Knowledge Base persistence."""
    logger.info("Testing Knowledge Base persistence...")

    # Load settings
    settings = load_settings()

    # Initialize database manager
    db_manager = initialize_database_manager(settings)

    # Create Knowledge Base with persistence
    kb = APIA_KnowledgeBase(db_manager=db_manager)

    # Store some values
    await kb.set_value("test/string", "Hello, world!")
    await kb.set_value("test/number", 42)
    await kb.set_value("test/dict", {"name": "APIA", "version": "0.1.0"})
    await kb.set_value("test/list", ["item1", "item2", "item3"])

    # Retrieve values
    string_value = await kb.get_value("test/string")
    number_value = await kb.get_value("test/number")
    dict_value = await kb.get_value("test/dict")
    list_value = await kb.get_value("test/list")

    # Print values
    logger.info(f"String value: {string_value}")
    logger.info(f"Number value: {number_value}")
    logger.info(f"Dict value: {dict_value}")
    logger.info(f"List value: {list_value}")

    # List keys
    keys = await kb.list_keys("test/")
    logger.info(f"Keys: {keys}")

    # Update a value
    await kb.set_value("test/dict", {"name": "APIA", "version": "0.2.0"})
    updated_dict = await kb.get_value("test/dict")
    logger.info(f"Updated dict value: {updated_dict}")

    # Delete a value
    await kb.delete_value("test/list")
    deleted_list = await kb.get_value("test/list")
    logger.info(f"Deleted list value: {deleted_list}")

    # Update a metric
    await kb.update_metric("test", "counter", 1)
    # Get the metric from system_metrics
    metrics = await kb.get_value("system_metrics")
    metric_value = metrics.get("test", {}).get("counter")
    logger.info(f"Metric value: {metric_value}")

    logger.info("Knowledge Base persistence test completed.")

async def test_agent_memory_persistence():
    """Test the agent memory persistence."""
    logger.info("Testing agent memory persistence...")

    # Load settings
    settings = load_settings()

    # Initialize database manager
    db_manager = initialize_database_manager(settings)

    # Create agent memory with persistence
    memory = AgentMemory(
        agent_id="test-agent",
        db_manager=db_manager,
        memory_dir="data/memory"
    )

    # Store some values
    await memory.store("test/string", "Hello, agent!")
    await memory.store("test/number", 42)
    await memory.store("test/dict", {"name": "Agent", "version": "0.1.0"})
    await memory.store("test/list", ["item1", "item2", "item3"])

    # Retrieve values
    string_value = await memory.retrieve("test/string")
    number_value = await memory.retrieve("test/number")
    dict_value = await memory.retrieve("test/dict")
    list_value = await memory.retrieve("test/list")

    # Print values
    logger.info(f"String value: {string_value}")
    logger.info(f"Number value: {number_value}")
    logger.info(f"Dict value: {dict_value}")
    logger.info(f"List value: {list_value}")

    # List keys
    keys = await memory.list_keys("test/")
    logger.info(f"Keys: {keys}")

    # Update a value
    await memory.store("test/dict", {"name": "Agent", "version": "0.2.0"})
    updated_dict = await memory.retrieve("test/dict")
    logger.info(f"Updated dict value: {updated_dict}")

    # Delete a value
    await memory.delete("test/list")
    deleted_list = await memory.retrieve("test/list")
    logger.info(f"Deleted list value: {deleted_list}")

    # Store a decision
    await memory.store_decision(
        "test_decision",
        {
            "decision": "test",
            "rationale": "This is a test decision"
        }
    )

    # Get decisions
    decisions = await memory.get_decisions("test_decision")
    logger.info(f"Decisions: {decisions}")

    # Store project history
    await memory.store_project_history(
        "test-project",
        {
            "event": "test",
            "description": "This is a test event"
        }
    )

    # Get project history
    project_history = await memory.get_project_history("test-project")
    logger.info(f"Project history: {project_history}")

    logger.info("Agent memory persistence test completed.")

async def main():
    """Main function to run the tests."""
    try:
        # Create data directories
        os.makedirs("data", exist_ok=True)
        os.makedirs("data/memory", exist_ok=True)

        # Run tests
        await test_knowledge_base_persistence()
        logger.info("\n" + "=" * 80 + "\n")
        await test_agent_memory_persistence()
    except Exception as e:
        logger.exception(f"Error during test: {e}")

if __name__ == "__main__":
    asyncio.run(main())
