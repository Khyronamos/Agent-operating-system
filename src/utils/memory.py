"""Memory interface for APIA agents.

This module provides a memory interface for agents to store and retrieve
agent-specific information that doesn't belong in the shared Knowledge Base.
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

class AgentMemory:
    """
    Agent-specific memory interface.

    This class provides a simple interface for agents to store and retrieve
    agent-specific information that doesn't belong in the shared Knowledge Base.

    It supports both in-memory storage and persistent storage through a database.
    """

    def __init__(self, agent_id: str, db_manager=None, memory_dir: Optional[str] = None):
        """
        Initialize the agent memory.

        Args:
            agent_id: ID of the agent
            db_manager: Optional database manager for persistence
            memory_dir: Directory to store memory files (if file persistence is enabled)
        """
        self.agent_id = agent_id
        self.memory_dir = memory_dir
        self._db_manager = db_manager

        # In-memory storage
        self._memory: Dict[str, Any] = {}

        # Initialize memory
        self._initialize()

        logger.info(f"AgentMemory initialized for agent {agent_id} (Persistence: {db_manager is not None or memory_dir is not None})")

    def _initialize(self):
        """Initialize the memory store."""
        # Create memory directory if it doesn't exist and is specified
        if self.memory_dir:
            os.makedirs(self.memory_dir, exist_ok=True)

            # Load memory from file if it exists
            memory_file = os.path.join(self.memory_dir, f"{self.agent_id}_memory.json")
            if os.path.exists(memory_file):
                try:
                    with open(memory_file, 'r') as f:
                        self._memory = json.load(f)
                    logger.info(f"Loaded memory from {memory_file}")
                except Exception as e:
                    logger.error(f"Failed to load memory from {memory_file}: {e}")

    async def store(self, key: str, value: Any) -> None:
        """
        Store a value in memory.

        Args:
            key: Key to store the value under
            value: Value to store
        """
        self._memory[key] = value

        # Persist memory if enabled
        await self._persist(key, value)

        logger.debug(f"Stored value for key '{key}' in memory for agent {self.agent_id}")

    async def retrieve(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value from memory.

        Args:
            key: Key to retrieve
            default: Default value to return if key doesn't exist

        Returns:
            The stored value or the default value
        """
        # Try to get from database first if available
        if self._db_manager:
            try:
                db_value = await self._db_manager.get_agent_memory_value(self.agent_id, key)
                if db_value is not None:
                    # Update in-memory cache
                    self._memory[key] = db_value
                    return db_value
            except Exception as e:
                logger.error(f"Failed to retrieve agent memory value for {key} from database: {e}")

        # Fall back to in-memory storage
        value = self._memory.get(key, default)
        logger.debug(f"Retrieved value for key '{key}' from memory for agent {self.agent_id}")
        return value

    async def delete(self, key: str) -> None:
        """
        Delete a value from memory.

        Args:
            key: Key to delete
        """
        if key in self._memory:
            del self._memory[key]

            # Delete from database if available
            if self._db_manager:
                try:
                    await self._db_manager.delete_agent_memory_value(self.agent_id, key)
                except Exception as e:
                    logger.error(f"Failed to delete agent memory value for {key} from database: {e}")

            # Persist memory to file if enabled
            if self.memory_dir:
                await self._persist_to_file()

            logger.debug(f"Deleted key '{key}' from memory for agent {self.agent_id}")

    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """
        List all keys in memory.

        Args:
            prefix: Optional prefix to filter keys

        Returns:
            List of keys
        """
        # Get keys from database if available
        db_keys = []
        if self._db_manager:
            try:
                db_keys = await self._db_manager.list_agent_memory_keys(self.agent_id, prefix)
            except Exception as e:
                logger.error(f"Failed to list agent memory keys from database: {e}")

        # Get keys from in-memory storage
        memory_keys = [k for k in self._memory.keys() if not prefix or k.startswith(prefix)]

        # Combine and deduplicate keys
        return list(set(db_keys + memory_keys))

    async def _persist(self, key: str, value: Any) -> None:
        """Persist memory to storage."""
        # Persist to database if available
        if self._db_manager:
            try:
                await self._db_manager.set_agent_memory_value(self.agent_id, key, value)
            except Exception as e:
                logger.error(f"Failed to persist agent memory value for {key} to database: {e}")

        # Persist to file if enabled
        if self.memory_dir:
            await self._persist_to_file()

    async def _persist_to_file(self) -> None:
        """Persist memory to file."""
        if self.memory_dir:
            memory_file = os.path.join(self.memory_dir, f"{self.agent_id}_memory.json")
            try:
                with open(memory_file, 'w') as f:
                    json.dump(self._memory, f, indent=2)
                logger.debug(f"Persisted memory to {memory_file}")
            except Exception as e:
                logger.error(f"Failed to persist memory to {memory_file}: {e}")

    # Specialized methods for agent-specific needs

    async def store_decision(self, decision_type: str, decision_data: Dict[str, Any]) -> None:
        """
        Store a decision in memory.

        Args:
            decision_type: Type of decision
            decision_data: Decision data
        """
        # Get existing decisions or create new ones
        decisions = await self.retrieve("decisions", {})

        if decision_type not in decisions:
            decisions[decision_type] = []

        # Add timestamp to decision data
        decision_entry = {
            "timestamp": datetime.now().isoformat(),
            **decision_data
        }

        # Add decision entry
        decisions[decision_type].append(decision_entry)

        # Store updated decisions
        await self.store("decisions", decisions)

        logger.info(f"Stored {decision_type} decision for agent {self.agent_id}")

    async def get_decisions(self, decision_type: Optional[str] = None) -> Union[Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]]]:
        """
        Get decisions from memory.

        Args:
            decision_type: Optional type of decisions to retrieve

        Returns:
            All decisions or decisions of the specified type
        """
        decisions = await self.retrieve("decisions", {})

        if decision_type:
            return decisions.get(decision_type, [])
        else:
            return decisions

    async def store_project_history(self, project_id: str, history_data: Dict[str, Any]) -> None:
        """
        Store project history in memory.

        Args:
            project_id: ID of the project
            history_data: Project history data
        """
        # Get existing project history or create new one
        projects = await self.retrieve("projects", {})

        if project_id not in projects:
            projects[project_id] = {
                "created_at": datetime.now().isoformat(),
                "history": []
            }

        # Add timestamp to history data
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            **history_data
        }

        # Add history entry
        projects[project_id]["history"].append(history_entry)

        # Store updated projects
        await self.store("projects", projects)

        logger.info(f"Stored history for project {project_id} for agent {self.agent_id}")

    async def get_project_history(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get project history from memory.

        Args:
            project_id: ID of the project

        Returns:
            Project history or None if not found
        """
        projects = await self.retrieve("projects", {})
        return projects.get(project_id)