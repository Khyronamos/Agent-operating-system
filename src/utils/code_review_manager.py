import logging
import os
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class CodeReviewManager:
    """
    Manager for code review operations.
    
    This class provides a unified interface for code review operations,
    using the Code Review MCP server.
    """
    
    def __init__(self, mcp_manager):
        """
        Initialize the code review manager.
        
        Args:
            mcp_manager: The MCP client manager
        """
        self.mcp_manager = mcp_manager
        self.server_name = "code-review"
    
    async def review_code(self, code: str, language: str, review_type: str = "general") -> Dict[str, Any]:
        """
        Review code.
        
        Args:
            code: The code to review
            language: The programming language of the code
            review_type: The type of review to perform (general, security, performance, etc.)
            
        Returns:
            Review results
        """
        logger.debug(f"Reviewing {language} code with {review_type} review type...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "reviewCode",
            {
                "code": code,
                "language": language,
                "reviewType": review_type
            }
        )
        
        return result
    
    async def review_file(self, file_path: str, review_type: str = "general") -> Dict[str, Any]:
        """
        Review a code file.
        
        Args:
            file_path: Path to the file to review
            review_type: The type of review to perform
            
        Returns:
            Review results
        """
        # Determine language from file extension
        _, ext = os.path.splitext(file_path)
        language = self._get_language_from_extension(ext)
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Review code
        return await self.review_code(code, language, review_type)
    
    async def review_project(self, project_dir: str, review_type: str = "general", 
                           file_extensions: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Review a project directory.
        
        Args:
            project_dir: Path to the project directory
            review_type: The type of review to perform
            file_extensions: List of file extensions to include (e.g., ['.py', '.js'])
            
        Returns:
            Dictionary mapping file paths to review results
        """
        if file_extensions is None:
            file_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.java', '.c', '.cpp', '.go']
        
        results = {}
        
        # Walk through directory
        for root, _, files in os.walk(project_dir):
            for file in files:
                _, ext = os.path.splitext(file)
                if ext in file_extensions:
                    file_path = os.path.join(root, file)
                    try:
                        results[file_path] = await self.review_file(file_path, review_type)
                    except Exception as e:
                        logger.error(f"Error reviewing {file_path}: {e}")
                        results[file_path] = {"error": str(e)}
        
        return results
    
    async def suggest_improvements(self, code: str, language: str) -> Dict[str, Any]:
        """
        Suggest improvements for code.
        
        Args:
            code: The code to improve
            language: The programming language of the code
            
        Returns:
            Improvement suggestions
        """
        logger.debug(f"Suggesting improvements for {language} code...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "suggestImprovements",
            {
                "code": code,
                "language": language
            }
        )
        
        return result
    
    async def check_security(self, code: str, language: str) -> Dict[str, Any]:
        """
        Check code for security vulnerabilities.
        
        Args:
            code: The code to check
            language: The programming language of the code
            
        Returns:
            Security check results
        """
        logger.debug(f"Checking {language} code for security vulnerabilities...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "checkSecurity",
            {
                "code": code,
                "language": language
            }
        )
        
        return result
    
    async def analyze_complexity(self, code: str, language: str) -> Dict[str, Any]:
        """
        Analyze code complexity.
        
        Args:
            code: The code to analyze
            language: The programming language of the code
            
        Returns:
            Complexity analysis results
        """
        logger.debug(f"Analyzing complexity of {language} code...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "analyzeComplexity",
            {
                "code": code,
                "language": language
            }
        )
        
        return result
    
    async def check_style(self, code: str, language: str) -> Dict[str, Any]:
        """
        Check code style.
        
        Args:
            code: The code to check
            language: The programming language of the code
            
        Returns:
            Style check results
        """
        logger.debug(f"Checking style of {language} code...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "checkStyle",
            {
                "code": code,
                "language": language
            }
        )
        
        return result
    
    def _get_language_from_extension(self, extension: str) -> str:
        """
        Get programming language from file extension.
        
        Args:
            extension: File extension (e.g., '.py')
            
        Returns:
            Programming language name
        """
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.html': 'html',
            '.css': 'css',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.rs': 'rust',
            '.sh': 'bash',
            '.ps1': 'powershell'
        }
        
        return extension_map.get(extension.lower(), 'text')
