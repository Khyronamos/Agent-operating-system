"""
Rate limiting middleware for APIA framework.

This module provides middleware for rate limiting requests to the A2A protocol
endpoints.
"""

import time
import logging
from typing import Callable, Dict, List, Optional, Union, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Simple in-memory rate limiter using the token bucket algorithm.
    
    This rate limiter uses a token bucket algorithm to limit the number of
    requests that can be made in a given time period.
    """
    
    def __init__(self, rate: float, per: float, burst: int = 1):
        """
        Initialize the rate limiter.
        
        Args:
            rate: Number of tokens to add per time period
            per: Time period in seconds
            burst: Maximum number of tokens that can be accumulated
        """
        self.rate = rate
        self.per = per
        self.burst = burst
        self.tokens = burst
        self.last_refill = time.time()
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Calculate tokens to add
        new_tokens = elapsed * (self.rate / self.per)
        
        # Update tokens and last refill time
        self.tokens = min(self.burst, self.tokens + new_tokens)
        self.last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False otherwise
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting requests to the A2A protocol endpoints.
    
    This middleware limits the number of requests that can be made to the
    A2A protocol endpoints in a given time period.
    """
    
    def __init__(
        self,
        app,
        rate: float = 10.0,
        per: float = 1.0,
        burst: int = 20,
        exclude_paths: List[str] = None,
        custom_limits: Dict[str, Tuple[float, float, int]] = None
    ):
        """
        Initialize the rate limiting middleware.
        
        Args:
            app: FastAPI application
            rate: Default number of requests allowed per time period
            per: Default time period in seconds
            burst: Default maximum number of requests that can be made in a burst
            exclude_paths: List of paths to exclude from rate limiting
            custom_limits: Dictionary mapping paths to custom rate limits (rate, per, burst)
        """
        super().__init__(app)
        self.default_limiter = RateLimiter(rate, per, burst)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health"
        ]
        self.custom_limits = custom_limits or {}
        self.limiters: Dict[str, Dict[str, RateLimiter]] = {}
        
        logger.info(f"RateLimitMiddleware initialized with default rate: {rate}/{per}s, burst: {burst}")
    
    def _get_limiter(self, path: str, client_id: str) -> RateLimiter:
        """
        Get the appropriate rate limiter for the path and client.
        
        Args:
            path: Request path
            client_id: Client identifier (IP address or token subject)
            
        Returns:
            Rate limiter for the path and client
        """
        # Check if there's a custom limit for this path
        for path_prefix, (rate, per, burst) in self.custom_limits.items():
            if path.startswith(path_prefix):
                # Create path-specific limiters dict if it doesn't exist
                if path_prefix not in self.limiters:
                    self.limiters[path_prefix] = {}
                
                # Create client-specific limiter if it doesn't exist
                if client_id not in self.limiters[path_prefix]:
                    self.limiters[path_prefix][client_id] = RateLimiter(rate, per, burst)
                
                return self.limiters[path_prefix][client_id]
        
        # Use default limiter for this client
        if "default" not in self.limiters:
            self.limiters["default"] = {}
        
        if client_id not in self.limiters["default"]:
            self.limiters["default"][client_id] = RateLimiter(
                self.default_limiter.rate,
                self.default_limiter.per,
                self.default_limiter.burst
            )
        
        return self.limiters["default"][client_id]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and apply rate limiting.
        
        Args:
            request: FastAPI request
            call_next: Next middleware or endpoint handler
            
        Returns:
            Response from the next middleware or endpoint handler
        """
        # Skip rate limiting for excluded paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)
        
        # Get client identifier (prefer token subject, fall back to IP)
        client_id = None
        if hasattr(request.state, "token_data"):
            client_id = request.state.token_data.sub
        
        if not client_id:
            client_id = request.client.host if request.client else "unknown"
        
        # Get appropriate limiter
        limiter = self._get_limiter(path, client_id)
        
        # Check if request is allowed
        if not limiter.consume():
            # Return 429 Too Many Requests
            return Response(
                content='{"detail":"Too many requests"}',
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": str(int(limiter.per))},
                media_type="application/json"
            )
        
        # Continue with the request
        return await call_next(request)
