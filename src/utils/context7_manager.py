import logging
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class Context7Manager:
    """
    Manager for Context7 operations.
    
    This class provides a unified interface for Context7 operations,
    using the Context7 MCP server.
    """
    
    def __init__(self, mcp_manager):
        """
        Initialize the Context7 manager.
        
        Args:
            mcp_manager: The MCP client manager
        """
        self.mcp_manager = mcp_manager
        self.server_name = "context7"
    
    async def list_contexts(self) -> List[Dict[str, Any]]:
        """
        List all contexts.
        
        Returns:
            List of contexts
        """
        logger.debug("Listing all contexts...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "listContexts",
            {}
        )
        
        return result
    
    async def create_context(self, name: str, content: str, 
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new context.
        
        Args:
            name: Name of the context
            content: Content of the context
            metadata: Metadata for the context (optional)
            
        Returns:
            Created context
        """
        logger.debug(f"Creating context '{name}'...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "createContext",
            {
                "name": name,
                "content": content,
                "metadata": metadata or {}
            }
        )
        
        return result
    
    async def get_context(self, context_id: str) -> Dict[str, Any]:
        """
        Get a context by ID.
        
        Args:
            context_id: ID of the context
            
        Returns:
            Context
        """
        logger.debug(f"Getting context {context_id}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "getContext",
            {
                "id": context_id
            }
        )
        
        return result
    
    async def update_context(self, context_id: str, name: Optional[str] = None, 
                           content: Optional[str] = None, 
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update a context.
        
        Args:
            context_id: ID of the context
            name: New name for the context (optional)
            content: New content for the context (optional)
            metadata: New metadata for the context (optional)
            
        Returns:
            Updated context
        """
        logger.debug(f"Updating context {context_id}...")
        
        update_data = {"id": context_id}
        if name is not None:
            update_data["name"] = name
        if content is not None:
            update_data["content"] = content
        if metadata is not None:
            update_data["metadata"] = metadata
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "updateContext",
            update_data
        )
        
        return result
    
    async def delete_context(self, context_id: str) -> Dict[str, Any]:
        """
        Delete a context.
        
        Args:
            context_id: ID of the context
            
        Returns:
            Result of the deletion
        """
        logger.debug(f"Deleting context {context_id}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "deleteContext",
            {
                "id": context_id
            }
        )
        
        return result
    
    async def search_contexts(self, query: str) -> List[Dict[str, Any]]:
        """
        Search contexts by name or metadata.
        
        Args:
            query: Search query
            
        Returns:
            List of matching contexts
        """
        logger.debug(f"Searching contexts with query '{query}'...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "searchContexts",
            {
                "query": query
            }
        )
        
        return result
    
    async def query_contexts(self, query: str) -> Dict[str, Any]:
        """
        Query contexts by content.
        
        Args:
            query: Query string
            
        Returns:
            Query results with relevant contexts
        """
        logger.debug(f"Querying contexts with query '{query}'...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "queryContexts",
            {
                "query": query
            }
        )
        
        return result
    
    async def create_or_update_context(self, name: str, content: str, 
                                     metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new context or update an existing one with the same name.
        
        Args:
            name: Name of the context
            content: Content of the context
            metadata: Metadata for the context (optional)
            
        Returns:
            Created or updated context
        """
        logger.debug(f"Creating or updating context '{name}'...")
        
        # Search for existing context with the same name
        existing_contexts = await self.search_contexts(name)
        exact_matches = [c for c in existing_contexts if c.get("name") == name]
        
        if exact_matches:
            # Update existing context
            context_id = exact_matches[0].get("id")
            return await self.update_context(context_id, name=name, content=content, metadata=metadata)
        else:
            # Create new context
            return await self.create_context(name, content, metadata)
    
    async def get_context_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a context by name.
        
        Args:
            name: Name of the context
            
        Returns:
            Context or None if not found
        """
        logger.debug(f"Getting context by name '{name}'...")
        
        # Search for context with the given name
        matching_contexts = await self.search_contexts(name)
        exact_matches = [c for c in matching_contexts if c.get("name") == name]
        
        return exact_matches[0] if exact_matches else None
    
    async def store_document(self, name: str, content: str, 
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Store a document as a context.
        
        Args:
            name: Name of the document
            content: Content of the document
            metadata: Metadata for the document (optional)
            
        Returns:
            Created or updated context
        """
        logger.debug(f"Storing document '{name}'...")
        
        # Add document type to metadata
        doc_metadata = metadata or {}
        doc_metadata["type"] = "document"
        
        return await self.create_or_update_context(name, content, doc_metadata)
    
    async def store_knowledge(self, name: str, content: str, 
                            category: Optional[str] = None,
                            tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Store knowledge as a context.
        
        Args:
            name: Name of the knowledge
            content: Content of the knowledge
            category: Category of the knowledge (optional)
            tags: Tags for the knowledge (optional)
            
        Returns:
            Created or updated context
        """
        logger.debug(f"Storing knowledge '{name}'...")
        
        # Prepare metadata
        metadata = {
            "type": "knowledge"
        }
        
        if category:
            metadata["category"] = category
        
        if tags:
            metadata["tags"] = tags
        
        return await self.create_or_update_context(name, content, metadata)
    
    async def query_knowledge(self, query: str, 
                            category: Optional[str] = None) -> Dict[str, Any]:
        """
        Query knowledge contexts.
        
        Args:
            query: Query string
            category: Category to filter by (optional)
            
        Returns:
            Query results with relevant knowledge
        """
        logger.debug(f"Querying knowledge with query '{query}'...")
        
        # Query all contexts
        results = await self.query_contexts(query)
        
        # Filter by type and category if needed
        if "contexts" in results:
            filtered_contexts = [
                c for c in results["contexts"] 
                if c.get("metadata", {}).get("type") == "knowledge" and
                (category is None or c.get("metadata", {}).get("category") == category)
            ]
            
            results["contexts"] = filtered_contexts
        
        return results
