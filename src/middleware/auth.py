"""
Authentication middleware for APIA framework.

This module provides middleware for authenticating requests to the A2A protocol
endpoints.
"""

import logging
from typing import Callable, Dict, List, Optional, Union

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from utils.auth import AuthManager
from core.exceptions import AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for authenticating requests to the A2A protocol endpoints.
    
    This middleware checks for a valid JWT token in the Authorization header
    and verifies that the token has the required roles for the requested
    endpoint.
    """
    
    def __init__(
        self,
        app,
        auth_manager: AuthManager,
        exclude_paths: List[str] = None,
        required_roles: Dict[str, List[str]] = None
    ):
        """
        Initialize the authentication middleware.
        
        Args:
            app: FastAPI application
            auth_manager: Authentication manager
            exclude_paths: List of paths to exclude from authentication
            required_roles: Dictionary mapping paths to required roles
        """
        super().__init__(app)
        self.auth_manager = auth_manager
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/auth/token",
            "/auth/agent-token"
        ]
        self.required_roles = required_roles or {}
        
        logger.info(f"AuthMiddleware initialized with {len(self.exclude_paths)} excluded paths")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and apply authentication.
        
        Args:
            request: FastAPI request
            call_next: Next middleware or endpoint handler
            
        Returns:
            Response from the next middleware or endpoint handler
        """
        # Skip authentication for excluded paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)
        
        # Skip authentication if disabled
        if not self.auth_manager.config.enabled:
            return await call_next(request)
        
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return Response(
                content='{"detail":"Authentication required"}',
                status_code=HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": "Bearer"},
                media_type="application/json"
            )
        
        # Extract token
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                return Response(
                    content='{"detail":"Invalid authentication scheme"}',
                    status_code=HTTP_401_UNAUTHORIZED,
                    headers={"WWW-Authenticate": "Bearer"},
                    media_type="application/json"
                )
        except ValueError:
            return Response(
                content='{"detail":"Invalid authorization header"}',
                status_code=HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": "Bearer"},
                media_type="application/json"
            )
        
        # Verify token
        try:
            token_data = self.auth_manager.verify_token(token)
        except AuthenticationError as e:
            return Response(
                content=f'{{"detail":"{str(e)}"}}',
                status_code=HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": "Bearer"},
                media_type="application/json"
            )
        
        # Check roles if required for this path
        required_roles = None
        for path_prefix, roles in self.required_roles.items():
            if path.startswith(path_prefix):
                required_roles = roles
                break
        
        if required_roles and not self.auth_manager.check_permission(token_data, required_roles):
            return Response(
                content=f'{{"detail":"Not enough permissions. Required roles: {required_roles}"}}',
                status_code=HTTP_403_FORBIDDEN,
                media_type="application/json"
            )
        
        # Add token data to request state
        request.state.token_data = token_data
        
        # Continue with the request
        return await call_next(request)
