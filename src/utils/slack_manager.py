import logging
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class SlackManager:
    """
    Manager for Slack operations.
    
    This class provides a unified interface for Slack operations,
    using the Slack MCP server.
    """
    
    def __init__(self, mcp_manager):
        """
        Initialize the Slack manager.
        
        Args:
            mcp_manager: The MCP client manager
        """
        self.mcp_manager = mcp_manager
        self.server_name = "slack"
    
    async def send_message(self, channel: str, text: str, 
                         blocks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Send a message to a Slack channel.
        
        Args:
            channel: Channel ID or name
            text: Message text
            blocks: Message blocks (optional)
            
        Returns:
            Message details
        """
        logger.debug(f"Sending message to channel {channel}...")
        
        params = {
            "channel": channel,
            "text": text
        }
        
        if blocks:
            params["blocks"] = blocks
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "sendMessage",
            params
        )
        
        return result
    
    async def list_channels(self) -> List[Dict[str, Any]]:
        """
        List Slack channels.
        
        Returns:
            List of channels
        """
        logger.debug("Listing channels...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "listChannels",
            {}
        )
        
        return result
    
    async def list_users(self) -> List[Dict[str, Any]]:
        """
        List Slack users.
        
        Returns:
            List of users
        """
        logger.debug("Listing users...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "listUsers",
            {}
        )
        
        return result
    
    async def get_channel_history(self, channel: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get channel history.
        
        Args:
            channel: Channel ID or name
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of messages
        """
        logger.debug(f"Getting history for channel {channel}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "getChannelHistory",
            {
                "channel": channel,
                "limit": limit
            }
        )
        
        return result
    
    async def get_user_info(self, user: str) -> Dict[str, Any]:
        """
        Get user information.
        
        Args:
            user: User ID or name
            
        Returns:
            User details
        """
        logger.debug(f"Getting information for user {user}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "getUserInfo",
            {
                "user": user
            }
        )
        
        return result
    
    async def get_channel_info(self, channel: str) -> Dict[str, Any]:
        """
        Get channel information.
        
        Args:
            channel: Channel ID or name
            
        Returns:
            Channel details
        """
        logger.debug(f"Getting information for channel {channel}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "getChannelInfo",
            {
                "channel": channel
            }
        )
        
        return result
    
    async def join_channel(self, channel: str) -> Dict[str, Any]:
        """
        Join a channel.
        
        Args:
            channel: Channel ID or name
            
        Returns:
            Join result
        """
        logger.debug(f"Joining channel {channel}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "joinChannel",
            {
                "channel": channel
            }
        )
        
        return result
    
    async def create_channel(self, name: str, is_private: bool = False) -> Dict[str, Any]:
        """
        Create a channel.
        
        Args:
            name: Channel name
            is_private: Whether the channel is private
            
        Returns:
            Created channel details
        """
        logger.debug(f"Creating channel {name}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "createChannel",
            {
                "name": name,
                "is_private": is_private
            }
        )
        
        return result
    
    async def invite_to_channel(self, channel: str, user: str) -> Dict[str, Any]:
        """
        Invite a user to a channel.
        
        Args:
            channel: Channel ID or name
            user: User ID or name
            
        Returns:
            Invite result
        """
        logger.debug(f"Inviting user {user} to channel {channel}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "inviteToChannel",
            {
                "channel": channel,
                "user": user
            }
        )
        
        return result
    
    async def upload_file(self, channels: List[str], file: str, 
                        title: Optional[str] = None, 
                        initial_comment: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a file to Slack.
        
        Args:
            channels: List of channel IDs or names
            file: File content or path
            title: File title (optional)
            initial_comment: Initial comment (optional)
            
        Returns:
            Upload result
        """
        logger.debug(f"Uploading file to channels {channels}...")
        
        params = {
            "channels": channels,
            "file": file
        }
        
        if title:
            params["title"] = title
        
        if initial_comment:
            params["initial_comment"] = initial_comment
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "uploadFile",
            params
        )
        
        return result
    
    async def search_messages(self, query: str, count: int = 20) -> Dict[str, Any]:
        """
        Search messages.
        
        Args:
            query: Search query
            count: Maximum number of results
            
        Returns:
            Search results
        """
        logger.debug(f"Searching messages with query '{query}'...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "searchMessages",
            {
                "query": query,
                "count": count
            }
        )
        
        return result
