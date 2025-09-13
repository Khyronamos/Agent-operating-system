class APIA_AgentFactory:
    # (Keep the async Factory implementation, ensure it imports agent classes correctly)
    _agent_classes: Dict[str, Type['APIA_BaseAgent']] = {}

    def __init__(self, knowledge_base: APIA_KnowledgeBase, agent_registry: APIA_AgentRegistry, mcp_manager: 'MCPClientManager', a2a_client: 'A2AClientManager', a2a_router: 'A2ATaskRouter'):
        self.knowledge_base = knowledge_base
        self.agent_registry = agent_registry
        self.mcp_manager = mcp_manager
        self.a2a_client = a2a_client
        self.a2a_router = a2a_router
        # Discover classes only once
        if not APIA_AgentFactory._agent_classes:
             APIA_AgentFactory._agent_classes = self._discover_agent_classes()
             logger.info(f"Agent Factory discovered agent classes: {list(APIA_AgentFactory._agent_classes.keys())}")

    def _discover_agent_classes(self) -> Dict[str, type]:
        # Need to import agent modules explicitly now
     from agents.implementations import ceo, cto, architect, aiops, generic # Assuming these files exist in 'agents' package
     classes = {}
        # List known types manually is often more robust than reflection across modules
     known_types = [
            ceo.APIA_CEOAgent, cto.APIA_CTOAgent, architect.APIA_ArchitectAgent,
            aiops.APIA_AIOpsEngineAgent, generic.APIA_GenericWorkerAgent
        ]
     for cls in known_types:
             if issubclass(cls, APIA_BaseAgent) and cls != APIA_BaseAgent:
                 classes[cls.__name__] = cls
        return classes

    async def create_agent(self, blueprint_role: str, agent_id: Optional[str] = None) -> Optional['APIA_BaseAgent']:
        logger.info(f"Agent Factory creating agent for role: {blueprint_role}")
        blueprints = await self.knowledge_base.get_value("agent_blueprints", {})
        blueprint = blueprints.get(blueprint_role)

        if not blueprint:
            logger.error(f"Blueprint not found for role: {blueprint_role}")
            return None

        class_name = blueprint.get("class_name")
        agent_class = APIA_AgentFactory._agent_classes.get(class_name) if class_name else None
        if not agent_class:
            logger.error(f"Agent class '{class_name or 'N/A'}' not found or missing in blueprint for role: {blueprint_role}")
            return None

        # Get details from blueprint, providing defaults
        internal_skills = blueprint.get("internal_skills", [])
        # Ensure a2a_skills are parsed into models if stored as dicts in YAML
        a2a_skill_dicts = blueprint.get("a2a_skills", [])
        a2a_skills = [A2AAgentSkill(**s) for s in a2a_skill_dicts if isinstance(s, dict)]
        agent_config_override = blueprint.get("config", {})
        has_dependency_issues = blueprint.get("has_dependency_issues", False)
        initial_state = blueprint.get("initial_state", {})

        try:
            # Pass all required dependencies to the agent constructor
            constructor_kwargs = {
                "role": blueprint_role,
                "agent_id": agent_id or str(uuid.uuid4()),
                "knowledge_base": self.knowledge_base,
                "agent_registry": self.agent_registry,
                "mcp_manager": self.mcp_manager,
                "a2a_client": self.a2a_client,
                "a2a_router": self.a2a_router,
                "internal_skills": internal_skills,
                "a2a_skills": a2a_skills,
                "config_override": agent_config_override,
                "initial_state": initial_state
            }
            # Handle agents like AIOps that need the factory itself
            if agent_class == aiops.APIA_AIOpsEngineAgent: # Need to import aiops module
                 constructor_kwargs["agent_factory"] = self # Pass self

            new_agent = agent_class(**constructor_kwargs)

            await self.knowledge_base.set_agent_dependency_status(new_agent.id, has_dependency_issues)
            # Initialization called within agent.start() or separately? Let's keep it separate for now.
            await new_agent.initialize_state(initial_state)

            logger.info(f"Successfully created agent {new_agent.role} ({new_agent.id}).")
            return new_agent
        except Exception as e:
            logger.error(f"Failed to instantiate agent class {class_name} for role {blueprint_role}: {e}", exc_info=True)
            return None