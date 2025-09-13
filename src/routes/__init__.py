"""
Routes for APIA framework.

This package contains route handlers for the APIA framework, including:
- Authentication routes
"""

from routes.auth import router as auth_router

__all__ = ["auth_router"]
