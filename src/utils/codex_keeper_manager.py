import logging
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class CodexKeeperManager:
    """
    Manager for Codex Keeper operations.
    
    This class provides a unified interface for Codex Keeper operations,
    using the Codex Keeper MCP server.
    """
    
    def __init__(self, mcp_manager):
        """
        Initialize the Codex Keeper manager.
        
        Args:
            mcp_manager: The MCP client manager
        """
        self.mcp_manager = mcp_manager
        self.server_name = "codex-keeper"
    
    async def list_codices(self) -> List[Dict[str, Any]]:
        """
        List all codices.
        
        Returns:
            List of codices
        """
        logger.debug("Listing all codices...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "listCodex",
            {}
        )
        
        return result
    
    async def create_codex(self, name: str, content: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new codex.
        
        Args:
            name: Name of the codex
            content: Content of the codex
            tags: Tags for the codex (optional)
            
        Returns:
            Created codex
        """
        logger.debug(f"Creating codex '{name}'...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "createCodex",
            {
                "name": name,
                "content": content,
                "tags": tags or []
            }
        )
        
        return result
    
    async def get_codex(self, codex_id: str) -> Dict[str, Any]:
        """
        Get a codex by ID.
        
        Args:
            codex_id: ID of the codex
            
        Returns:
            Codex
        """
        logger.debug(f"Getting codex {codex_id}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "getCodex",
            {
                "id": codex_id
            }
        )
        
        return result
    
    async def update_codex(self, codex_id: str, name: Optional[str] = None, 
                         content: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Update a codex.
        
        Args:
            codex_id: ID of the codex
            name: New name for the codex (optional)
            content: New content for the codex (optional)
            tags: New tags for the codex (optional)
            
        Returns:
            Updated codex
        """
        logger.debug(f"Updating codex {codex_id}...")
        
        update_data = {"id": codex_id}
        if name is not None:
            update_data["name"] = name
        if content is not None:
            update_data["content"] = content
        if tags is not None:
            update_data["tags"] = tags
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "updateCodex",
            update_data
        )
        
        return result
    
    async def delete_codex(self, codex_id: str) -> Dict[str, Any]:
        """
        Delete a codex.
        
        Args:
            codex_id: ID of the codex
            
        Returns:
            Result of the deletion
        """
        logger.debug(f"Deleting codex {codex_id}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "deleteCodex",
            {
                "id": codex_id
            }
        )
        
        return result
    
    async def search_codices(self, query: str) -> List[Dict[str, Any]]:
        """
        Search codices.
        
        Args:
            query: Search query
            
        Returns:
            List of matching codices
        """
        logger.debug(f"Searching codices with query '{query}'...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "searchCodex",
            {
                "query": query
            }
        )
        
        return result
    
    async def create_or_update_codex(self, name: str, content: str, 
                                   tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new codex or update an existing one with the same name.
        
        Args:
            name: Name of the codex
            content: Content of the codex
            tags: Tags for the codex (optional)
            
        Returns:
            Created or updated codex
        """
        logger.debug(f"Creating or updating codex '{name}'...")
        
        # Search for existing codex with the same name
        existing_codices = await self.search_codices(name)
        exact_matches = [c for c in existing_codices if c.get("name") == name]
        
        if exact_matches:
            # Update existing codex
            codex_id = exact_matches[0].get("id")
            return await self.update_codex(codex_id, name=name, content=content, tags=tags)
        else:
            # Create new codex
            return await self.create_codex(name, content, tags)
    
    async def get_codex_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a codex by name.
        
        Args:
            name: Name of the codex
            
        Returns:
            Codex or None if not found
        """
        logger.debug(f"Getting codex by name '{name}'...")
        
        # Search for codex with the given name
        matching_codices = await self.search_codices(name)
        exact_matches = [c for c in matching_codices if c.get("name") == name]
        
        return exact_matches[0] if exact_matches else None
    
    async def get_codices_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        Get codices by tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of codices with the given tag
        """
        logger.debug(f"Getting codices with tag '{tag}'...")
        
        # Search for codices with the given tag
        all_codices = await self.list_codices()
        return [c for c in all_codices if tag in c.get("tags", [])]
