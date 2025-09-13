"""
Authentication routes for APIA framework.

This module provides routes for authentication, including token generation
and validation.
"""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Form, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from utils.auth import AuthManager, Token, TokenData, get_current_token_data, has_roles
from utils.dependencies import get_auth_manager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={401: {"description": "Unauthorized"}},
)

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_manager: AuthManager = Depends(get_auth_manager)
):
    """
    Get an access token for a user.
    
    Args:
        form_data: OAuth2 password request form
        auth_manager: Authentication manager
        
    Returns:
        Token object with access token
        
    Raises:
        HTTPException: If authentication fails
    """
    user = auth_manager.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_manager.create_user_token(form_data.username)
    return token

@router.post("/agent-token", response_model=Token)
async def get_agent_token(
    agent_id: str = Form(...),
    api_key: str = Form(...),
    auth_manager: AuthManager = Depends(get_auth_manager)
):
    """
    Get an access token for an agent.
    
    Args:
        agent_id: ID of the agent
        api_key: API key of the agent
        auth_manager: Authentication manager
        
    Returns:
        Token object with access token
        
    Raises:
        HTTPException: If authentication fails
    """
    agent = auth_manager.authenticate_agent(agent_id, api_key)
    if not agent:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid agent credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_manager.create_agent_token(agent_id)
    return token

@router.get("/me", response_model=Dict[str, Any])
async def read_users_me(
    token_data: TokenData = Depends(get_current_token_data)
):
    """
    Get information about the current authenticated user or agent.
    
    Args:
        token_data: Current token data
        
    Returns:
        Dictionary with token data
    """
    return {
        "sub": token_data.sub,
        "roles": token_data.roles,
        "is_agent": token_data.is_agent,
        "agent_id": token_data.agent_id,
        "agent_type": token_data.agent_type,
        "metadata": token_data.metadata
    }

@router.get("/admin", response_model=Dict[str, str])
async def admin_only(
    token_data: TokenData = Depends(has_roles(["admin"]))
):
    """
    Admin-only endpoint for testing role-based access control.
    
    Args:
        token_data: Current token data with admin role
        
    Returns:
        Dictionary with message
    """
    return {"message": f"Welcome, admin {token_data.sub}!"}
