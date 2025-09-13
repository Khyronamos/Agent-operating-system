import logging
import os
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class E2BManager:
    """
    Manager for E2B operations.
    
    This class provides a unified interface for E2B operations,
    using the E2B MCP server for code execution and sandbox environments.
    """
    
    def __init__(self, mcp_manager):
        """
        Initialize the E2B manager.
        
        Args:
            mcp_manager: The MCP client manager
        """
        self.mcp_manager = mcp_manager
        self.server_name = "e2b"
    
    async def run_python(self, code: str) -> Dict[str, Any]:
        """
        Run Python code in a sandbox environment.
        
        Args:
            code: Python code to execute
            
        Returns:
            Execution result
        """
        logger.debug("Running Python code...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "runPython",
            {
                "code": code
            }
        )
        
        return result
    
    async def run_node(self, code: str) -> Dict[str, Any]:
        """
        Run Node.js code in a sandbox environment.
        
        Args:
            code: Node.js code to execute
            
        Returns:
            Execution result
        """
        logger.debug("Running Node.js code...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "runNode",
            {
                "code": code
            }
        )
        
        return result
    
    async def run_bash(self, code: str) -> Dict[str, Any]:
        """
        Run Bash code in a sandbox environment.
        
        Args:
            code: Bash code to execute
            
        Returns:
            Execution result
        """
        logger.debug("Running Bash code...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "runBash",
            {
                "code": code
            }
        )
        
        return result
    
    async def read_file(self, path: str) -> Dict[str, Any]:
        """
        Read a file from the sandbox environment.
        
        Args:
            path: Path to the file
            
        Returns:
            File content
        """
        logger.debug(f"Reading file {path}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "readFile",
            {
                "path": path
            }
        )
        
        return result
    
    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """
        Write a file to the sandbox environment.
        
        Args:
            path: Path to the file
            content: Content to write
            
        Returns:
            Write result
        """
        logger.debug(f"Writing to file {path}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "writeFile",
            {
                "path": path,
                "content": content
            }
        )
        
        return result
    
    async def list_files(self, path: str = ".") -> Dict[str, Any]:
        """
        List files in a directory in the sandbox environment.
        
        Args:
            path: Path to the directory
            
        Returns:
            List of files
        """
        logger.debug(f"Listing files in {path}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "listFiles",
            {
                "path": path
            }
        )
        
        return result
    
    async def delete_file(self, path: str) -> Dict[str, Any]:
        """
        Delete a file from the sandbox environment.
        
        Args:
            path: Path to the file
            
        Returns:
            Delete result
        """
        logger.debug(f"Deleting file {path}...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "deleteFile",
            {
                "path": path
            }
        )
        
        return result
    
    async def install_package(self, package: str, manager: str = "pip") -> Dict[str, Any]:
        """
        Install a package in the sandbox environment.
        
        Args:
            package: Package to install
            manager: Package manager to use (pip, npm, apt)
            
        Returns:
            Installation result
        """
        logger.debug(f"Installing package {package} with {manager}...")
        
        if manager == "pip":
            command = f"pip install {package}"
        elif manager == "npm":
            command = f"npm install {package}"
        elif manager == "apt":
            command = f"apt-get update && apt-get install -y {package}"
        else:
            raise ValueError(f"Unsupported package manager: {manager}")
        
        result = await self.run_bash(command)
        
        return result
    
    async def run_python_script(self, script_path: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run a Python script in the sandbox environment.
        
        Args:
            script_path: Path to the script
            args: Command-line arguments
            
        Returns:
            Execution result
        """
        logger.debug(f"Running Python script {script_path}...")
        
        command = f"python {script_path}"
        if args:
            command += " " + " ".join(args)
        
        result = await self.run_bash(command)
        
        return result
    
    async def run_node_script(self, script_path: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run a Node.js script in the sandbox environment.
        
        Args:
            script_path: Path to the script
            args: Command-line arguments
            
        Returns:
            Execution result
        """
        logger.debug(f"Running Node.js script {script_path}...")
        
        command = f"node {script_path}"
        if args:
            command += " " + " ".join(args)
        
        result = await self.run_bash(command)
        
        return result
    
    async def create_python_project(self, project_name: str, 
                                  files: Dict[str, str],
                                  requirements: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a Python project in the sandbox environment.
        
        Args:
            project_name: Name of the project
            files: Dictionary mapping file paths to content
            requirements: List of requirements to install
            
        Returns:
            Project creation result
        """
        logger.debug(f"Creating Python project {project_name}...")
        
        # Create project directory
        await self.run_bash(f"mkdir -p {project_name}")
        
        # Create files
        results = {}
        for file_path, content in files.items():
            full_path = os.path.join(project_name, file_path)
            # Create directory if needed
            dir_path = os.path.dirname(full_path)
            if dir_path:
                await self.run_bash(f"mkdir -p {dir_path}")
            # Write file
            result = await self.write_file(full_path, content)
            results[file_path] = result
        
        # Create requirements.txt if needed
        if requirements:
            requirements_content = "\n".join(requirements)
            await self.write_file(f"{project_name}/requirements.txt", requirements_content)
            
            # Install requirements
            await self.run_bash(f"cd {project_name} && pip install -r requirements.txt")
        
        return {
            "project_name": project_name,
            "files": results
        }
    
    async def create_node_project(self, project_name: str, 
                                files: Dict[str, str],
                                dependencies: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Create a Node.js project in the sandbox environment.
        
        Args:
            project_name: Name of the project
            files: Dictionary mapping file paths to content
            dependencies: Dictionary mapping package names to versions
            
        Returns:
            Project creation result
        """
        logger.debug(f"Creating Node.js project {project_name}...")
        
        # Create project directory
        await self.run_bash(f"mkdir -p {project_name}")
        
        # Create files
        results = {}
        for file_path, content in files.items():
            full_path = os.path.join(project_name, file_path)
            # Create directory if needed
            dir_path = os.path.dirname(full_path)
            if dir_path:
                await self.run_bash(f"mkdir -p {dir_path}")
            # Write file
            result = await self.write_file(full_path, content)
            results[file_path] = result
        
        # Create package.json if needed
        if dependencies:
            package_json = {
                "name": project_name,
                "version": "1.0.0",
                "description": f"{project_name} project",
                "main": "index.js",
                "dependencies": dependencies
            }
            await self.write_file(
                f"{project_name}/package.json", 
                json.dumps(package_json, indent=2)
            )
            
            # Install dependencies
            await self.run_bash(f"cd {project_name} && npm install")
        
        return {
            "project_name": project_name,
            "files": results
        }
