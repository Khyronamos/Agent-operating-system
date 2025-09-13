import logging
import asyncio
import base64
from typing import Dict, Any, Optional, List, Tuple, Union

logger = logging.getLogger(__name__)

class BrowserManager:
    """
    Manager for browser automation with fallback logic.
    
    This class provides a unified interface for browser automation,
    using Hyperbrowser as the primary engine and Puppeteer as a fallback.
    """
    
    def __init__(self, mcp_manager):
        """
        Initialize the browser manager.
        
        Args:
            mcp_manager: The MCP client manager
        """
        self.mcp_manager = mcp_manager
        self.primary_server = "hyperbrowser"
        self.fallback_server = "puppeteer"
        self._sessions = {}
    
    async def _call_with_fallback(self, tool: str, params: Dict[str, Any]) -> Any:
        """
        Call an MCP tool with fallback logic.
        
        Args:
            tool: The tool name
            params: The tool parameters
            
        Returns:
            The tool result
        """
        try:
            # Try primary server
            logger.debug(f"Calling {tool} on {self.primary_server}...")
            result = await self.mcp_manager.call_tool(
                self.primary_server, 
                tool, 
                params
            )
            return result
        except Exception as e:
            # Log error and try fallback
            logger.warning(f"Error with {self.primary_server} ({tool}): {e}")
            logger.info(f"Falling back to {self.fallback_server}...")
            try:
                result = await self.mcp_manager.call_tool(
                    self.fallback_server, 
                    tool, 
                    params
                )
                return result
            except Exception as fallback_error:
                logger.error(f"Fallback also failed ({tool}): {fallback_error}")
                raise
    
    async def navigate_to_url(self, url: str) -> Dict[str, Any]:
        """
        Navigate to a URL.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            Result of the navigation
        """
        return await self._call_with_fallback("navigate", {"url": url})
    
    async def take_screenshot(self, selector: Optional[str] = None) -> bytes:
        """
        Take a screenshot of the current page or a specific element.
        
        Args:
            selector: Optional CSS selector for a specific element
            
        Returns:
            Screenshot as bytes
        """
        params = {}
        if selector:
            params["selector"] = selector
            
        result = await self._call_with_fallback("screenshot", params)
        
        # Handle different return formats
        if isinstance(result, bytes):
            return result
        elif isinstance(result, str) and result.startswith("data:image"):
            # Handle base64 data URL
            header, encoded = result.split(",", 1)
            return base64.b64decode(encoded)
        elif isinstance(result, dict) and "data" in result:
            # Handle dictionary with data field
            if isinstance(result["data"], bytes):
                return result["data"]
            elif isinstance(result["data"], str):
                return base64.b64decode(result["data"])
        
        raise ValueError(f"Unexpected screenshot format: {type(result)}")
    
    async def extract_text(self, selector: Optional[str] = None) -> str:
        """
        Extract text from the current page or a specific element.
        
        Args:
            selector: Optional CSS selector for a specific element
            
        Returns:
            Extracted text
        """
        params = {}
        if selector:
            params["selector"] = selector
            
        return await self._call_with_fallback("extractText", params)
    
    async def click_element(self, selector: str) -> Dict[str, Any]:
        """
        Click an element on the page.
        
        Args:
            selector: CSS selector for the element to click
            
        Returns:
            Result of the click operation
        """
        return await self._call_with_fallback("click", {"selector": selector})
    
    async def fill_form(self, selector: str, value: str) -> Dict[str, Any]:
        """
        Fill a form field.
        
        Args:
            selector: CSS selector for the form field
            value: Value to fill in
            
        Returns:
            Result of the fill operation
        """
        return await self._call_with_fallback("fill", {"selector": selector, "value": value})
    
    async def search_web(self, query: str) -> Dict[str, Any]:
        """
        Perform a web search.
        
        Args:
            query: Search query
            
        Returns:
            Search results
        """
        # Navigate to Google
        await self.navigate_to_url("https://www.google.com")
        
        # Fill search box
        await self.fill_form('input[name="q"]', query)
        
        # Submit search
        await self._call_with_fallback("press", {"key": "Enter"})
        
        # Wait for results to load
        await asyncio.sleep(2)
        
        # Extract search results
        results = await self.extract_text("#search")
        
        return {"query": query, "results": results}
    
    async def extract_links(self, selector: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Extract links from the current page.
        
        Args:
            selector: Optional CSS selector to limit the scope
            
        Returns:
            List of links with text and href
        """
        params = {}
        if selector:
            params["selector"] = selector
            
        return await self._call_with_fallback("extractLinks", params)
    
    async def scroll_page(self, direction: str = "down", amount: int = 500) -> Dict[str, Any]:
        """
        Scroll the page.
        
        Args:
            direction: Scroll direction ("up", "down", "left", "right")
            amount: Scroll amount in pixels
            
        Returns:
            Result of the scroll operation
        """
        return await self._call_with_fallback("scroll", {"direction": direction, "amount": amount})
    
    async def wait_for_selector(self, selector: str, timeout: int = 30000) -> Dict[str, Any]:
        """
        Wait for an element to appear on the page.
        
        Args:
            selector: CSS selector for the element
            timeout: Timeout in milliseconds
            
        Returns:
            Result of the wait operation
        """
        return await self._call_with_fallback("waitForSelector", {"selector": selector, "timeout": timeout})
    
    async def execute_javascript(self, code: str) -> Any:
        """
        Execute JavaScript code on the page.
        
        Args:
            code: JavaScript code to execute
            
        Returns:
            Result of the JavaScript execution
        """
        return await self._call_with_fallback("evaluate", {"code": code})
    
    async def close(self) -> None:
        """Close all browser sessions."""
        try:
            await self.mcp_manager.close_all()
        except Exception as e:
            logger.error(f"Error closing browser sessions: {e}")
