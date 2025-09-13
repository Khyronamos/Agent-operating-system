# agents/specialized.py
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional

from core.framework import APIA_BaseAgent
from utils.protocols import A2ATaskContext, A2ATaskResult
from utils.models import A2AMessage, A2ATextPart

logger = logging.getLogger(__name__)

class APIA_SpecializedAgent(APIA_BaseAgent, ABC):
    """
    Abstract base class for specialized agents that handle domain-specific tasks.

    Specialized agents typically:
    1. Initialize domain-specific resources (e.g., API clients, templates).
    2. Register their specific skills/capabilities.
    3. Provide a common way to handle domain tasks, often routing to
       more specific internal handlers based on the task details.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._skill_registry: Dict[str, Dict] = {} # For internal skill definitions

    async def initialize(self, memory_dir: Optional[str] = None):
        """
        Initializes the specialized agent.
        Calls superclass initialize, then domain-specific resource initialization
        and skill registration.
        """
        logger.info(f"SpecializedAgent ({self.role} - {self.id}) initializing...")
        await super().initialize() # Call base agent's initialize
        await self._initialize_domain_resources()
        await self._register_skills()
        logger.info(f"SpecializedAgent ({self.role} - {self.id}) initialized.")

    @abstractmethod
    async def _initialize_domain_resources(self):
        """
        Abstract method for subclasses to initialize their domain-specific resources.
        This could include loading configurations, setting up connections, etc.
        """
        pass

    @abstractmethod
    async def _register_skills(self):
        """
        Abstract method for subclasses to register or define their specific skills.
        This typically populates `self._skill_registry` with skill details.
        These details can be used by `_handle_domain_task` for routing.
        """
        pass

    async def handle_a2a_task(self, context: A2ATaskContext) -> A2ATaskResult:
        """
        Overrides the default A2A task handler from APIA_BaseAgent.
        This common handler for specialized agents extracts relevant information
        from the context and calls the abstract `_handle_domain_task` method.
        """
        skill_id = context.task.metadata.get("skill_id", "unknown_specialized_skill") if context.task.metadata else "unknown_specialized_skill"
        description = " ".join(context.get_text_parts()) if context.get_text_parts() else f"Execute specialized skill: {skill_id}"
        logger.info(f"{self.role} ({self.id}) routing to _handle_domain_task for skill '{skill_id}'.")
        return await self._handle_domain_task(context, skill_id, description)

    @abstractmethod
    async def _handle_domain_task(self, context: A2ATaskContext, subtask_id: str, subtask_description: str) -> A2ATaskResult:
        """
        Abstract method for subclasses to implement the core logic for handling
        domain-specific tasks. This method will be called by the overridden
        `handle_a2a_task` or by specific `handle_<skill_id>_skill` methods
        if the specialized agent defines those for finer-grained routing.

        Args:
            context: The A2A task context.
            subtask_id: An identifier for the specific subtask or skill being handled.
                        Often, this will be the `skill_id` from the A2A task metadata.
            subtask_description: A textual description of the task to be performed.
        """
        pass