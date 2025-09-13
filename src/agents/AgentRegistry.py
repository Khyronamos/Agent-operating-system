class APIA_AgentRegistry:
    # (Keep the async Registry implementation from the previous step)
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            if cls._instance is None:
                cls._instance = super(APIA_AgentRegistry, cls).__new__(cls)
                cls._instance.agents: Dict[str, 'APIA_BaseAgent'] = {}
                cls._instance._agent_lock = asyncio.Lock()
        return cls._instance

    async def register(self, agent: 'APIA_BaseAgent'):
        async with self._agent_lock:
            if agent.id in self.agents:
                logger.warning(f"Agent {agent.id} ({agent.role}) already registered. Overwriting.")
            self.agents[agent.id] = agent
            logger.info(f"Agent registered: {agent.role} ({agent.id})")

    async def unregister(self, agent_id: str) -> bool:
        async with self._agent_lock:
            if agent_id not in self.agents:
                logger.warning(f"Attempt to unregister non-existent agent: {agent_id}")
                return False
            # Make sure agent is stopped before removing? AIOps does this now.
            del self.agents[agent_id]
            logger.info(f"Agent unregistered: {agent_id}")
            return True

    async def get_agent(self, agent_id: str) -> Optional['APIA_BaseAgent']:
        async with self._agent_lock:
            return self.agents.get(agent_id)

    async def get_all_agents(self) -> List['APIA_BaseAgent']:
        async with self._agent_lock:
            return list(self.agents.values())

    async def get_agents_by_skill(self, skill: str) -> List['APIA_BaseAgent']:
        """Finds agents by *internal* skills (A2A skills are advertised)."""
        async with self._agent_lock:
            return [agent for agent in self.agents.values() if skill in agent.internal_skills]