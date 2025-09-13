"""
Authentication module for APIA framework.

This module provides JWT-based authentication for the A2A protocol,
including token generation, validation, and role-based access control.
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

import jwt
from pydantic import BaseModel, Field, validator
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from utils.config import Settings
from core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)

# Security scheme for Swagger UI
security = HTTPBearer()

# Define models for authentication
class TokenData(BaseModel):
    """Data contained in a JWT token."""
    sub: str  # Subject (agent ID or username)
    exp: int  # Expiration time
    iat: int  # Issued at time
    roles: List[str] = []  # Roles for RBAC
    agent_id: Optional[str] = None  # Agent ID if token is for an agent
    agent_type: Optional[str] = None  # Agent type if token is for an agent
    is_agent: bool = False  # Whether the token is for an agent or a user
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Additional metadata

class UserInDB(BaseModel):
    """User model stored in the database."""
    username: str
    hashed_password: str
    roles: List[str] = []
    disabled: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentCredentials(BaseModel):
    """Credentials for an agent."""
    agent_id: str
    agent_type: str
    roles: List[str] = []
    api_key: str
    disabled: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until expiration

class AuthConfig(BaseModel):
    """Authentication configuration."""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 1440  # 24 hours
    token_url: str = "/auth/token"
    
    @validator("secret_key")
    def secret_key_must_be_strong(cls, v):
        if len(v) < 32:
            logger.warning("Secret key is less than 32 characters. This is not secure for production.")
        return v

class AuthManager:
    """
    Authentication manager for APIA framework.
    
    Handles JWT token generation, validation, and role-based access control.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the authentication manager.
        
        Args:
            settings: Application settings containing auth configuration
        """
        # Get auth config from settings or use defaults
        auth_config = settings.auth if hasattr(settings, "auth") else {}
        
        # Use provided secret key or generate one
        secret_key = auth_config.get("secret_key", os.environ.get("JWT_SECRET_KEY", None))
        if not secret_key:
            # Generate a random secret key for development
            import secrets
            secret_key = secrets.token_hex(32)
            logger.warning(
                "No JWT_SECRET_KEY found in environment or settings. "
                "Generated a random secret key. This is not secure for production."
            )
        
        # Create auth config
        self.config = AuthConfig(
            secret_key=secret_key,
            algorithm=auth_config.get("algorithm", "HS256"),
            access_token_expire_minutes=auth_config.get("access_token_expire_minutes", 30),
            refresh_token_expire_minutes=auth_config.get("refresh_token_expire_minutes", 1440),
            token_url=auth_config.get("token_url", "/auth/token")
        )
        
        # Initialize user and agent stores
        # In a real implementation, these would be stored in a database
        self._users: Dict[str, UserInDB] = {}
        self._agents: Dict[str, AgentCredentials] = {}
        
        # Load initial users and agents if provided
        initial_users = auth_config.get("users", [])
        for user in initial_users:
            self.add_user(
                username=user["username"],
                password=user["password"],
                roles=user.get("roles", []),
                disabled=user.get("disabled", False),
                metadata=user.get("metadata", {})
            )
        
        initial_agents = auth_config.get("agents", [])
        for agent in initial_agents:
            self.add_agent(
                agent_id=agent["agent_id"],
                agent_type=agent["agent_type"],
                roles=agent.get("roles", []),
                api_key=agent.get("api_key"),
                disabled=agent.get("disabled", False),
                metadata=agent.get("metadata", {})
            )
        
        logger.info(f"AuthManager initialized with {len(self._users)} users and {len(self._agents)} agents")
    
    def add_user(self, username: str, password: str, roles: List[str] = None, 
                 disabled: bool = False, metadata: Dict[str, Any] = None) -> None:
        """
        Add a user to the authentication system.
        
        Args:
            username: Username for the user
            password: Plain text password (will be hashed)
            roles: List of roles for the user
            disabled: Whether the user is disabled
            metadata: Additional metadata for the user
        """
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        hashed_password = pwd_context.hash(password)
        self._users[username] = UserInDB(
            username=username,
            hashed_password=hashed_password,
            roles=roles or [],
            disabled=disabled,
            metadata=metadata or {}
        )
        logger.info(f"Added user: {username} with roles: {roles}")
    
    def add_agent(self, agent_id: str, agent_type: str, roles: List[str] = None,
                  api_key: Optional[str] = None, disabled: bool = False, 
                  metadata: Dict[str, Any] = None) -> str:
        """
        Add an agent to the authentication system.
        
        Args:
            agent_id: ID of the agent
            agent_type: Type of the agent
            roles: List of roles for the agent
            api_key: API key for the agent (generated if not provided)
            disabled: Whether the agent is disabled
            metadata: Additional metadata for the agent
            
        Returns:
            The API key for the agent
        """
        if api_key is None:
            import secrets
            api_key = secrets.token_hex(16)
        
        self._agents[agent_id] = AgentCredentials(
            agent_id=agent_id,
            agent_type=agent_type,
            roles=roles or [],
            api_key=api_key,
            disabled=disabled,
            metadata=metadata or {}
        )
        logger.info(f"Added agent: {agent_id} ({agent_type}) with roles: {roles}")
        return api_key
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username of the user
            password: Password of the user
            
        Returns:
            User object if authentication succeeds, None otherwise
        """
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        user = self._users.get(username)
        if not user:
            return None
        if user.disabled:
            return None
        if not pwd_context.verify(password, user.hashed_password):
            return None
        return user
    
    def authenticate_agent(self, agent_id: str, api_key: str) -> Optional[AgentCredentials]:
        """
        Authenticate an agent with agent_id and API key.
        
        Args:
            agent_id: ID of the agent
            api_key: API key of the agent
            
        Returns:
            Agent credentials if authentication succeeds, None otherwise
        """
        agent = self._agents.get(agent_id)
        if not agent:
            return None
        if agent.disabled:
            return None
        if agent.api_key != api_key:
            return None
        return agent
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Data to encode in the token
            expires_delta: Token expiration time
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire.timestamp(),
            "iat": datetime.utcnow().timestamp()
        })
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.config.secret_key, 
            algorithm=self.config.algorithm
        )
        return encoded_jwt
    
    def create_user_token(self, username: str) -> Token:
        """
        Create a token for a user.
        
        Args:
            username: Username of the user
            
        Returns:
            Token object with access token
            
        Raises:
            AuthenticationError: If user does not exist or is disabled
        """
        user = self._users.get(username)
        if not user:
            raise AuthenticationError(f"User {username} not found")
        if user.disabled:
            raise AuthenticationError(f"User {username} is disabled")
        
        expires_delta = timedelta(minutes=self.config.access_token_expire_minutes)
        expires_in = int(expires_delta.total_seconds())
        
        token_data = {
            "sub": username,
            "roles": user.roles,
            "is_agent": False,
            "metadata": user.metadata
        }
        
        access_token = self.create_access_token(
            data=token_data,
            expires_delta=expires_delta
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in
        )
    
    def create_agent_token(self, agent_id: str) -> Token:
        """
        Create a token for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Token object with access token
            
        Raises:
            AuthenticationError: If agent does not exist or is disabled
        """
        agent = self._agents.get(agent_id)
        if not agent:
            raise AuthenticationError(f"Agent {agent_id} not found")
        if agent.disabled:
            raise AuthenticationError(f"Agent {agent_id} is disabled")
        
        expires_delta = timedelta(minutes=self.config.access_token_expire_minutes)
        expires_in = int(expires_delta.total_seconds())
        
        token_data = {
            "sub": agent_id,
            "roles": agent.roles,
            "agent_id": agent_id,
            "agent_type": agent.agent_type,
            "is_agent": True,
            "metadata": agent.metadata
        }
        
        access_token = self.create_access_token(
            data=token_data,
            expires_delta=expires_delta
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in
        )
    
    def decode_token(self, token: str) -> TokenData:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            TokenData object with decoded token data
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token, 
                self.config.secret_key, 
                algorithms=[self.config.algorithm]
            )
            
            # Convert to TokenData model
            token_data = TokenData(
                sub=payload["sub"],
                exp=payload["exp"],
                iat=payload["iat"],
                roles=payload.get("roles", []),
                agent_id=payload.get("agent_id"),
                agent_type=payload.get("agent_type"),
                is_agent=payload.get("is_agent", False),
                metadata=payload.get("metadata", {})
            )
            
            return token_data
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
    
    def verify_token(self, token: str) -> TokenData:
        """
        Verify a JWT token and return the token data.
        
        Args:
            token: JWT token string
            
        Returns:
            TokenData object with decoded token data
            
        Raises:
            AuthenticationError: If token is invalid, expired, or user/agent is disabled
        """
        token_data = self.decode_token(token)
        
        # Check if token is for an agent or user
        if token_data.is_agent:
            agent = self._agents.get(token_data.agent_id)
            if not agent:
                raise AuthenticationError(f"Agent {token_data.agent_id} not found")
            if agent.disabled:
                raise AuthenticationError(f"Agent {token_data.agent_id} is disabled")
        else:
            user = self._users.get(token_data.sub)
            if not user:
                raise AuthenticationError(f"User {token_data.sub} not found")
            if user.disabled:
                raise AuthenticationError(f"User {token_data.sub} is disabled")
        
        return token_data
    
    def check_permission(self, token_data: TokenData, required_roles: List[str]) -> bool:
        """
        Check if the token has the required roles.
        
        Args:
            token_data: TokenData object with decoded token data
            required_roles: List of roles required for access
            
        Returns:
            True if token has required roles, False otherwise
        """
        # If no roles required, allow access
        if not required_roles:
            return True
        
        # Check if token has any of the required roles
        return any(role in token_data.roles for role in required_roles)

# FastAPI dependency for getting the current token data
async def get_current_token_data(
    credentials: HTTPAuthorizationCredentials = Security(security),
    auth_manager: AuthManager = Depends(lambda: get_auth_manager())
) -> TokenData:
    """
    Get the current token data from the request.
    
    Args:
        credentials: HTTP Authorization credentials
        auth_manager: Authentication manager
        
    Returns:
        TokenData object with decoded token data
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        token_data = auth_manager.verify_token(credentials.credentials)
        return token_data
    except AuthenticationError as e:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )

# FastAPI dependency for role-based access control
def has_roles(required_roles: List[str]):
    """
    Create a dependency that checks if the current token has the required roles.
    
    Args:
        required_roles: List of roles required for access
        
    Returns:
        Dependency function that checks roles
        
    Raises:
        HTTPException: If token does not have required roles
    """
    async def _has_roles(token_data: TokenData = Depends(get_current_token_data)):
        if not any(role in token_data.roles for role in required_roles):
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required roles: {required_roles}"
            )
        return token_data
    return _has_roles

# Global auth manager instance
_auth_manager = None

def get_auth_manager() -> AuthManager:
    """
    Get the global auth manager instance.
    
    Returns:
        AuthManager instance
    """
    global _auth_manager
    if _auth_manager is None:
        from utils.dependencies import get_settings
        settings = get_settings()
        _auth_manager = AuthManager(settings)
    return _auth_manager

def initialize_auth_manager(settings: Settings) -> AuthManager:
    """
    Initialize the global auth manager instance.
    
    Args:
        settings: Application settings
        
    Returns:
        AuthManager instance
    """
    global _auth_manager
    _auth_manager = AuthManager(settings)
    return _auth_manager
