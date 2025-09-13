# dependencies.py
from fastapi import Request, Depends

# Assuming components are stored in app.state during lifespan
from utils.config import Settings
from core.framework import APIA_AgentRegistry, APIA_KnowledgeBase, APIA_AgentFactory
from utils.protocols import A2ATaskManager, MCPClientManager, A2AClientManager
from utils.auth import AuthManager

# These functions retrieve components initialized during startup

def get_settings(request: Request) -> Settings:
    if not hasattr(request.app.state, 'settings'):
         raise RuntimeError("Settings not initialized in app state")
    return request.app.state.settings

def get_agent_registry(request: Request) -> APIA_AgentRegistry:
    if not hasattr(request.app.state, 'agent_registry'):
         raise RuntimeError("AgentRegistry not initialized in app state")
    return request.app.state.agent_registry

def get_a2a_task_manager(request: Request) -> A2ATaskManager:
    if not hasattr(request.app.state, 'a2a_task_manager'):
         raise RuntimeError("A2ATaskManager not initialized in app state")
    return request.app.state.a2a_task_manager

def get_knowledge_base(request: Request) -> APIA_KnowledgeBase:
    if not hasattr(request.app.state, 'knowledge_base'):
        raise RuntimeError("KnowledgeBase not initialized in app state")
    return request.app.state.knowledge_base

def get_mcp_manager(request: Request) -> MCPClientManager:
    if not hasattr(request.app.state, 'mcp_manager'):
         raise RuntimeError("MCPClientManager not initialized in app state")
    return request.app.state.mcp_manager

def get_a2a_client(request: Request) -> A2AClientManager:
    if not hasattr(request.app.state, 'a2a_client'):
         raise RuntimeError("A2AClientManager not initialized in app state")
    return request.app.state.a2a_client

# Add get_agent_factory if needed by any routes
def get_agent_factory(request: Request) -> APIA_AgentFactory:
    if not hasattr(request.app.state, 'agent_factory'):
         raise RuntimeError("AgentFactory not initialized in app state")
    return request.app.state.agent_factory

def get_auth_manager(request: Request) -> AuthManager:
    if not hasattr(request.app.state, 'auth_manager'):
         raise RuntimeError("AuthManager not initialized in app state")
    return request.app.state.auth_manager
