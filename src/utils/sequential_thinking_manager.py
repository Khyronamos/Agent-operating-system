import logging
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class SequentialThinkingManager:
    """
    Manager for Sequential Thinking operations.
    
    This class provides a unified interface for Sequential Thinking operations,
    using the Sequential Thinking MCP server for structured reasoning.
    """
    
    def __init__(self, mcp_manager):
        """
        Initialize the Sequential Thinking manager.
        
        Args:
            mcp_manager: The MCP client manager
        """
        self.mcp_manager = mcp_manager
        self.server_name = "sequential-thinking"
    
    async def sequential_thinking(self, prompt: str, steps: int = 5) -> Dict[str, Any]:
        """
        Perform sequential thinking on a prompt.
        
        Args:
            prompt: The prompt to think about
            steps: Number of steps for sequential thinking
            
        Returns:
            Sequential thinking result
        """
        logger.debug(f"Performing sequential thinking on prompt: {prompt}")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "sequentialThinking",
            {
                "prompt": prompt,
                "steps": steps
            }
        )
        
        return result
    
    async def solve_problem(self, problem: str, steps: int = 5) -> Dict[str, Any]:
        """
        Solve a problem using sequential thinking.
        
        Args:
            problem: The problem to solve
            steps: Number of steps for sequential thinking
            
        Returns:
            Problem solution
        """
        logger.debug(f"Solving problem: {problem}")
        
        prompt = f"Solve the following problem step by step: {problem}"
        
        return await self.sequential_thinking(prompt, steps)
    
    async def analyze_code(self, code: str, steps: int = 5) -> Dict[str, Any]:
        """
        Analyze code using sequential thinking.
        
        Args:
            code: The code to analyze
            steps: Number of steps for sequential thinking
            
        Returns:
            Code analysis
        """
        logger.debug(f"Analyzing code")
        
        prompt = f"Analyze the following code step by step, identifying potential issues and improvements:\n\n```\n{code}\n```"
        
        return await self.sequential_thinking(prompt, steps)
    
    async def design_system(self, system: str, steps: int = 5) -> Dict[str, Any]:
        """
        Design a system using sequential thinking.
        
        Args:
            system: The system to design
            steps: Number of steps for sequential thinking
            
        Returns:
            System design
        """
        logger.debug(f"Designing system: {system}")
        
        prompt = f"Design the following system step by step: {system}"
        
        return await self.sequential_thinking(prompt, steps)
    
    async def create_plan(self, task: str, steps: int = 5) -> Dict[str, Any]:
        """
        Create a plan using sequential thinking.
        
        Args:
            task: The task to plan
            steps: Number of steps for sequential thinking
            
        Returns:
            Task plan
        """
        logger.debug(f"Creating plan for task: {task}")
        
        prompt = f"Create a detailed plan for the following task step by step: {task}"
        
        return await self.sequential_thinking(prompt, steps)
    
    async def debug_issue(self, issue: str, steps: int = 5) -> Dict[str, Any]:
        """
        Debug an issue using sequential thinking.
        
        Args:
            issue: The issue to debug
            steps: Number of steps for sequential thinking
            
        Returns:
            Debug result
        """
        logger.debug(f"Debugging issue: {issue}")
        
        prompt = f"Debug the following issue step by step: {issue}"
        
        return await self.sequential_thinking(prompt, steps)
    
    async def evaluate_solution(self, solution: str, criteria: str, steps: int = 5) -> Dict[str, Any]:
        """
        Evaluate a solution using sequential thinking.
        
        Args:
            solution: The solution to evaluate
            criteria: The evaluation criteria
            steps: Number of steps for sequential thinking
            
        Returns:
            Evaluation result
        """
        logger.debug(f"Evaluating solution against criteria: {criteria}")
        
        prompt = f"Evaluate the following solution step by step against these criteria: {criteria}\n\nSolution: {solution}"
        
        return await self.sequential_thinking(prompt, steps)
    
    async def analyze_requirements(self, requirements: str, steps: int = 5) -> Dict[str, Any]:
        """
        Analyze requirements using sequential thinking.
        
        Args:
            requirements: The requirements to analyze
            steps: Number of steps for sequential thinking
            
        Returns:
            Requirements analysis
        """
        logger.debug(f"Analyzing requirements")
        
        prompt = f"Analyze the following requirements step by step, identifying potential issues, ambiguities, and improvements:\n\n{requirements}"
        
        return await self.sequential_thinking(prompt, steps)
    
    async def generate_test_cases(self, feature: str, steps: int = 5) -> Dict[str, Any]:
        """
        Generate test cases using sequential thinking.
        
        Args:
            feature: The feature to test
            steps: Number of steps for sequential thinking
            
        Returns:
            Test cases
        """
        logger.debug(f"Generating test cases for feature: {feature}")
        
        prompt = f"Generate comprehensive test cases for the following feature step by step: {feature}"
        
        return await self.sequential_thinking(prompt, steps)
