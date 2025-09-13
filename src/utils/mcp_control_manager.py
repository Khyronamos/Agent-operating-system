import logging
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class MCPControlManager:
    """
    Manager for MCP Control operations.
    
    This class provides a unified interface for MCP Control operations,
    using the MCP Control server for managing and orchestrating MCP servers.
    """
    
    def __init__(self, mcp_manager):
        """
        Initialize the MCP Control manager.
        
        Args:
            mcp_manager: The MCP client manager
        """
        self.mcp_manager = mcp_manager
        self.server_name = "mcp-control"
    
    async def list_servers(self) -> List[Dict[str, Any]]:
        """
        List available MCP servers.
        
        Returns:
            List of available MCP servers
        """
        logger.debug("Listing available MCP servers...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "listServers",
            {}
        )
        
        return result
    
    async def start_server(self, server_name: str) -> Dict[str, Any]:
        """
        Start an MCP server.
        
        Args:
            server_name: Name of the server to start
            
        Returns:
            Start result
        """
        logger.debug(f"Starting server {server_name}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "startServer",
            {
                "serverName": server_name
            }
        )
        
        return result
    
    async def stop_server(self, server_name: str) -> Dict[str, Any]:
        """
        Stop an MCP server.
        
        Args:
            server_name: Name of the server to stop
            
        Returns:
            Stop result
        """
        logger.debug(f"Stopping server {server_name}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "stopServer",
            {
                "serverName": server_name
            }
        )
        
        return result
    
    async def get_server_status(self, server_name: str) -> Dict[str, Any]:
        """
        Get status of an MCP server.
        
        Args:
            server_name: Name of the server
            
        Returns:
            Server status
        """
        logger.debug(f"Getting status for server {server_name}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "getServerStatus",
            {
                "serverName": server_name
            }
        )
        
        return result
    
    async def orchestrate_workflow(self, workflow: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Orchestrate a workflow across multiple MCP servers.
        
        Args:
            workflow: Name of the workflow to orchestrate
            params: Workflow parameters (optional)
            
        Returns:
            Orchestration result
        """
        logger.debug(f"Orchestrating workflow {workflow}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "orchestrateWorkflow",
            {
                "workflow": workflow,
                "params": params or {}
            }
        )
        
        return result
    
    async def register_workflow(self, workflow_name: str, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new workflow.
        
        Args:
            workflow_name: Name of the workflow
            workflow_definition: Workflow definition
            
        Returns:
            Registration result
        """
        logger.debug(f"Registering workflow {workflow_name}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "registerWorkflow",
            {
                "workflowName": workflow_name,
                "workflowDefinition": workflow_definition
            }
        )
        
        return result
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """
        List available workflows.
        
        Returns:
            List of available workflows
        """
        logger.debug("Listing available workflows...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "listWorkflows",
            {}
        )
        
        return result
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get status of a workflow execution.
        
        Args:
            workflow_id: ID of the workflow execution
            
        Returns:
            Workflow status
        """
        logger.debug(f"Getting status for workflow {workflow_id}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "getWorkflowStatus",
            {
                "workflowId": workflow_id
            }
        )
        
        return result
    
    async def start_all_servers(self) -> Dict[str, Any]:
        """
        Start all MCP servers.
        
        Returns:
            Start results for all servers
        """
        logger.debug("Starting all MCP servers...")
        
        # Get list of servers
        servers = await self.list_servers()
        
        # Start each server
        results = {}
        for server in servers:
            server_name = server.get("name")
            try:
                result = await self.start_server(server_name)
                results[server_name] = result
            except Exception as e:
                logger.error(f"Error starting server {server_name}: {e}")
                results[server_name] = {"error": str(e)}
        
        return results
    
    async def stop_all_servers(self) -> Dict[str, Any]:
        """
        Stop all MCP servers.
        
        Returns:
            Stop results for all servers
        """
        logger.debug("Stopping all MCP servers...")
        
        # Get list of servers
        servers = await self.list_servers()
        
        # Stop each server
        results = {}
        for server in servers:
            server_name = server.get("name")
            try:
                result = await self.stop_server(server_name)
                results[server_name] = result
            except Exception as e:
                logger.error(f"Error stopping server {server_name}: {e}")
                results[server_name] = {"error": str(e)}
        
        return results
    
    async def get_all_server_statuses(self) -> Dict[str, Any]:
        """
        Get status of all MCP servers.
        
        Returns:
            Status for all servers
        """
        logger.debug("Getting status for all MCP servers...")
        
        # Get list of servers
        servers = await self.list_servers()
        
        # Get status for each server
        results = {}
        for server in servers:
            server_name = server.get("name")
            try:
                result = await self.get_server_status(server_name)
                results[server_name] = result
            except Exception as e:
                logger.error(f"Error getting status for server {server_name}: {e}")
                results[server_name] = {"error": str(e)}
        
        return results
    
    async def create_landing_page_workflow(self) -> Dict[str, Any]:
        """
        Create a workflow for the Landing Page Method.
        
        Returns:
            Workflow registration result
        """
        logger.debug("Creating Landing Page Method workflow...")
        
        # Define the workflow
        workflow_definition = {
            "name": "landing_page_method",
            "description": "Workflow for the Landing Page Method",
            "steps": [
                {
                    "name": "find_businesses",
                    "server": "hyperbrowser",
                    "tool": "navigateToUrl",
                    "params": {
                        "url": "https://www.yelp.com/search?find_desc=&find_loc={{location}}"
                    },
                    "next": "extract_business_info"
                },
                {
                    "name": "extract_business_info",
                    "server": "hyperbrowser",
                    "tool": "extractData",
                    "params": {
                        "selectors": {
                            "businesses": ".businessName"
                        }
                    },
                    "next": "generate_landing_page"
                },
                {
                    "name": "generate_landing_page",
                    "server": "starwind-ui",
                    "tool": "generateComponent",
                    "params": {
                        "componentType": "landing-page",
                        "params": {
                            "businessName": "{{business.name}}",
                            "businessType": "{{business.type}}",
                            "description": "{{business.description}}"
                        }
                    },
                    "next": "test_landing_page"
                },
                {
                    "name": "test_landing_page",
                    "server": "e2b",
                    "tool": "runNode",
                    "params": {
                        "code": "const puppeteer = require('puppeteer'); async function testPage(html) { const browser = await puppeteer.launch(); const page = await browser.newPage(); await page.setContent(html); const title = await page.title(); await browser.close(); return { title }; } testPage('{{landing_page.html}}');"
                    },
                    "next": "store_business_info"
                },
                {
                    "name": "store_business_info",
                    "server": "codex-keeper",
                    "tool": "createCodex",
                    "params": {
                        "name": "{{business.name}}",
                        "content": JSON.stringify({
                            "business": "{{business}}",
                            "landing_page": "{{landing_page}}"
                        }),
                        "tags": ["landing_page_method", "business"]
                    },
                    "next": null
                }
            ]
        }
        
        # Register the workflow
        return await self.register_workflow("landing_page_method", workflow_definition)
    
    async def create_ziprecruiter_workflow(self) -> Dict[str, Any]:
        """
        Create a workflow for the ZipRecruiter Method.
        
        Returns:
            Workflow registration result
        """
        logger.debug("Creating ZipRecruiter Method workflow...")
        
        # Define the workflow
        workflow_definition = {
            "name": "ziprecruiter_method",
            "description": "Workflow for the ZipRecruiter Method",
            "steps": [
                {
                    "name": "find_jobs",
                    "server": "hyperbrowser",
                    "tool": "navigateToUrl",
                    "params": {
                        "url": "https://www.ziprecruiter.com/jobs-search?search={{job_title}}&location={{location}}"
                    },
                    "next": "extract_job_info"
                },
                {
                    "name": "extract_job_info",
                    "server": "hyperbrowser",
                    "tool": "extractData",
                    "params": {
                        "selectors": {
                            "jobs": ".job_content"
                        }
                    },
                    "next": "analyze_job_requirements"
                },
                {
                    "name": "analyze_job_requirements",
                    "server": "sequential-thinking",
                    "tool": "sequentialThinking",
                    "params": {
                        "prompt": "Analyze the following job requirements and determine if they can be automated: {{job.description}}",
                        "steps": 5
                    },
                    "next": "create_solution"
                },
                {
                    "name": "create_solution",
                    "server": "e2b",
                    "tool": "runPython",
                    "params": {
                        "code": "# Create a solution for the job requirements\nprint('Creating solution for {{job.title}}')"
                    },
                    "next": "store_job_info"
                },
                {
                    "name": "store_job_info",
                    "server": "codex-keeper",
                    "tool": "createCodex",
                    "params": {
                        "name": "{{job.title}}",
                        "content": JSON.stringify({
                            "job": "{{job}}",
                            "analysis": "{{analysis}}",
                            "solution": "{{solution}}"
                        }),
                        "tags": ["ziprecruiter_method", "job"]
                    },
                    "next": null
                }
            ]
        }
        
        # Register the workflow
        return await self.register_workflow("ziprecruiter_method", workflow_definition)
