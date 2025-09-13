import logging
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class GitHubManager:
    """
    Manager for GitHub operations.
    
    This class provides a unified interface for GitHub operations,
    using the GitHub MCP server.
    """
    
    def __init__(self, mcp_manager):
        """
        Initialize the GitHub manager.
        
        Args:
            mcp_manager: The MCP client manager
        """
        self.mcp_manager = mcp_manager
        self.server_name = "github"
    
    async def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository details
        """
        logger.debug(f"Getting repository {owner}/{repo}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "getRepository",
            {
                "owner": owner,
                "repo": repo
            }
        )
        
        return result
    
    async def list_repositories(self, owner: str) -> List[Dict[str, Any]]:
        """
        List repositories for an owner.
        
        Args:
            owner: Repository owner
            
        Returns:
            List of repositories
        """
        logger.debug(f"Listing repositories for {owner}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "listRepositories",
            {
                "owner": owner
            }
        )
        
        return result
    
    async def create_repository(self, name: str, description: Optional[str] = None, 
                              private: bool = False) -> Dict[str, Any]:
        """
        Create a new repository.
        
        Args:
            name: Repository name
            description: Repository description (optional)
            private: Whether the repository is private (default: False)
            
        Returns:
            Created repository details
        """
        logger.debug(f"Creating repository {name}...")
        
        params = {
            "name": name,
            "private": private
        }
        
        if description:
            params["description"] = description
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "createRepository",
            params
        )
        
        return result
    
    async def create_issue(self, owner: str, repo: str, title: str, 
                         body: Optional[str] = None, 
                         labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create an issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue body (optional)
            labels: Issue labels (optional)
            
        Returns:
            Created issue details
        """
        logger.debug(f"Creating issue in {owner}/{repo}...")
        
        params = {
            "owner": owner,
            "repo": repo,
            "title": title
        }
        
        if body:
            params["body"] = body
        
        if labels:
            params["labels"] = labels
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "createIssue",
            params
        )
        
        return result
    
    async def list_issues(self, owner: str, repo: str, state: str = "open") -> List[Dict[str, Any]]:
        """
        List issues in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state (open, closed, all) (default: open)
            
        Returns:
            List of issues
        """
        logger.debug(f"Listing issues in {owner}/{repo}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "listIssues",
            {
                "owner": owner,
                "repo": repo,
                "state": state
            }
        )
        
        return result
    
    async def create_pull_request(self, owner: str, repo: str, title: str, 
                                head: str, base: str = "main", 
                                body: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: Pull request title
            head: Head branch
            base: Base branch (default: main)
            body: Pull request body (optional)
            
        Returns:
            Created pull request details
        """
        logger.debug(f"Creating pull request in {owner}/{repo}...")
        
        params = {
            "owner": owner,
            "repo": repo,
            "title": title,
            "head": head,
            "base": base
        }
        
        if body:
            params["body"] = body
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "createPullRequest",
            params
        )
        
        return result
    
    async def list_pull_requests(self, owner: str, repo: str, state: str = "open") -> List[Dict[str, Any]]:
        """
        List pull requests in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: Pull request state (open, closed, all) (default: open)
            
        Returns:
            List of pull requests
        """
        logger.debug(f"Listing pull requests in {owner}/{repo}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "listPullRequests",
            {
                "owner": owner,
                "repo": repo,
                "state": state
            }
        )
        
        return result
    
    async def get_file_content(self, owner: str, repo: str, path: str, 
                             ref: Optional[str] = None) -> Dict[str, Any]:
        """
        Get file content from a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            ref: Git reference (branch, tag, commit) (optional)
            
        Returns:
            File content details
        """
        logger.debug(f"Getting file content from {owner}/{repo}/{path}...")
        
        params = {
            "owner": owner,
            "repo": repo,
            "path": path
        }
        
        if ref:
            params["ref"] = ref
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "getFileContent",
            params
        )
        
        return result
    
    async def create_file(self, owner: str, repo: str, path: str, content: str, 
                        message: str, branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a file in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            content: File content
            message: Commit message
            branch: Branch name (optional)
            
        Returns:
            File creation details
        """
        logger.debug(f"Creating file in {owner}/{repo}/{path}...")
        
        params = {
            "owner": owner,
            "repo": repo,
            "path": path,
            "content": content,
            "message": message
        }
        
        if branch:
            params["branch"] = branch
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "createFile",
            params
        )
        
        return result
    
    async def update_file(self, owner: str, repo: str, path: str, content: str, 
                        message: str, sha: str, 
                        branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Update a file in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            content: New file content
            message: Commit message
            sha: File SHA
            branch: Branch name (optional)
            
        Returns:
            File update details
        """
        logger.debug(f"Updating file in {owner}/{repo}/{path}...")
        
        params = {
            "owner": owner,
            "repo": repo,
            "path": path,
            "content": content,
            "message": message,
            "sha": sha
        }
        
        if branch:
            params["branch"] = branch
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "updateFile",
            params
        )
        
        return result
    
    async def create_or_update_file(self, owner: str, repo: str, path: str, 
                                  content: str, message: str, 
                                  branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Create or update a file in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            content: File content
            message: Commit message
            branch: Branch name (optional)
            
        Returns:
            File creation or update details
        """
        logger.debug(f"Creating or updating file in {owner}/{repo}/{path}...")
        
        try:
            # Try to get the file first
            file_info = await self.get_file_content(owner, repo, path, branch)
            
            # If the file exists, update it
            return await self.update_file(
                owner=owner,
                repo=repo,
                path=path,
                content=content,
                message=message,
                sha=file_info.get("sha"),
                branch=branch
            )
        except Exception:
            # If the file doesn't exist, create it
            return await self.create_file(
                owner=owner,
                repo=repo,
                path=path,
                content=content,
                message=message,
                branch=branch
            )
    
    async def create_branch(self, owner: str, repo: str, branch: str, 
                          source_branch: str = "main") -> Dict[str, Any]:
        """
        Create a branch in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: New branch name
            source_branch: Source branch name (default: main)
            
        Returns:
            Branch creation details
        """
        logger.debug(f"Creating branch {branch} in {owner}/{repo}...")
        
        # Get the SHA of the source branch
        source_ref = await self.mcp_manager.call_tool(
            self.server_name,
            "getRef",
            {
                "owner": owner,
                "repo": repo,
                "ref": f"heads/{source_branch}"
            }
        )
        
        # Create the new branch
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "createRef",
            {
                "owner": owner,
                "repo": repo,
                "ref": f"refs/heads/{branch}",
                "sha": source_ref.get("object", {}).get("sha")
            }
        )
        
        return result
