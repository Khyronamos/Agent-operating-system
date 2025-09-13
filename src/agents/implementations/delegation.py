# agents/delegation.py
import asyncio
import logging
import random
import uuid
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set

from core.framework import APIA_BaseAgent
from utils.protocols import A2ATaskContext, A2ATaskResult, A2AClientManager
from utils.models import A2AArtifact, A2ATextPart, A2ADataPart, A2AMessage, A2ATaskSendParams
from utils.memory import AgentMemory

logger = logging.getLogger(__name__)

class APIA_DelegationAgent(APIA_BaseAgent):
    """
    Delegation Agent for breaking down complex tasks into manageable subtasks.
    
    This agent specializes in analyzing complex tasks, identifying component parts,
    determining dependencies, and matching subtasks to agent capabilities.
    """
    """
    6/7/2025[Future me, make this a real function, this would be a game changer for self organizaing and orchestration]:
    one for delegation working with architect
    one where the delegation is the architect and makes a team given the task( harder)
    one where the delegation is the architect and makes a team given the task and the team is the architect(super meta, and hard, but could be a good idea)
    one where the delegation returns a report to the ceo( medium/ not that hard)
    maybe another micro agency with the aiops, architect, delegation, and a to be decided highly specialized agent implemenation.
    """
async def handle_architect_collaboration_skill(self, context: A2ATaskContext) -> A2ATaskResult:
        """
        Handles the skill that enables direct collaboration with the architect agent, allowing for new agent types to be broken down into smaller parts, therefore more digestible and receptive to nuance.
        Delegation agent makes a call to the A2A Router, allowing the Architect agent to assist if it's available.
        Args:
            context: Task context containing direction to call the architect agent for agent implementation assistance
        Returns:
            Task result with call outcome status and agent implementations need
        """
        logger.info(f"DelegationAgent({self.id}) handling architect collaboration skill")
        await context.update_status("working", message_text="Attempting collaboration with architect...")

        # Example of how to call another agent (Architect) via A2A
        # This assumes the Architect agent is running and its A2A endpoint is known.
        # For a real implementation, you'd discover the Architect's URL or have it configured.
        # For MVP, we'll simulate a call or assume a direct A2A call to a known Architect.

        # In a real scenario, you'd get the Architect's URL from the Knowledge Base or Agent Registry
        # For now, let's assume a placeholder URL or direct call if Architect is local.
        # This part needs to be refined based on how Architect agent is exposed.
        architect_agent_url = "http://127.0.0.1:8000" # Placeholder: Replace with actual Architect URL

        try:
            # Prepare the task for the Architect agent
            architect_task_params = A2ATaskSendParams(
                message=A2AMessage(
                    role="user",
                    parts=[A2ATextPart(text="Please provide guidance on breaking down a new agent type for implementation.")],
                    metadata={"skill_id": "architecture_design", "original_task_id": context.task_id}
                )
            )
            logger.info(f"DelegationAgent sending task to Architect: {architect_task_params.id}")
            architect_response = await self.a2a_client.send_task(architect_agent_url, architect_task_params)
            logger.info(f"DelegationAgent received response from Architect: {architect_response.status}")

            # Process the Architect's response
            if architect_response.status == "completed":
                return A2ATaskResult(
                    status="completed",
                    message=A2AMessage(
                        role="agent",
                        parts=[A2ATextPart(text=f"Collaboration with Architect successful. Architect response: {architect_response.message.parts[0].text if architect_response.message else 'No message'}")]
                    ),
                    artifacts=architect_response.artifacts
                )
            else:
                return A2ATaskResult(
                    status="failed",
                    message=A2AMessage(
                        role="agent",
                        parts=[A2ATextPart(text=f"Collaboration with Architect failed. Status: {architect_response.status}. Message: {architect_response.message.parts[0].text if architect_response.message else 'No message'}")]
                    )
                )
        except Exception as e:
            logger.error(f"Error during Architect collaboration: {e}", exc_info=True)
            return A2ATaskResult(
                status="failed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text=f"Failed to collaborate with Architect: {str(e)}")]
                )
            )

    async def initialize(self, memory_dir: Optional[str] = None):
        """Initialize the Delegation Agent."""
        logger.info(f"DelegationAgent ({self.id}) initializing...")
        
        # Initialize agent-specific memory
        self._memory = AgentMemory(self.id, memory_dir)
        
        # Initialize agent capability registry
        self._capability_registry = {}
        
        # Any delegation-specific initialization here
        await super().initialize()
        
        # Load agent capabilities from knowledge base
        await self._load_agent_capabilities()
        
        logger.info(f"DelegationAgent ({self.id}) initialized with agent-specific memory")
    
    async def _load_agent_capabilities(self):
        """Load agent capabilities from the knowledge base."""
        try:
            # Get agent registry from knowledge base
            agent_registry = await self.knowledge_base.get_value("agent_registry", {})
            
            # Extract capabilities from agent registry
            for agent_id, agent_info in agent_registry.items():
                if "skills" in agent_info:
                    self._capability_registry[agent_id] = {
                        "agent_type": agent_info.get("type", "unknown"),
                        "skills": agent_info["skills"]
                    }
            
            logger.info(f"Loaded capabilities for {len(self._capability_registry)} agents")
            
            # If no capabilities found, use default capabilities for testing
            if not self._capability_registry:
                self._initialize_default_capabilities()
        except Exception as e:
            logger.error(f"Error loading agent capabilities: {e}")
            # Initialize default capabilities for testing
            self._initialize_default_capabilities()
    
    def _initialize_default_capabilities(self):
        """Initialize default agent capabilities for testing."""
        self._capability_registry = {
            "ceo-agent": {
                "agent_type": "CEO",
                "skills": ["business_strategy", "executive_decision", "resource_allocation"]
            },
            "cto-agent": {
                "agent_type": "CTO",
                "skills": ["technology_assessment", "mvp_conceptualization", "mvp_team_assembly"]
            },
            "aiops-agent": {
                "agent_type": "AIOps",
                "skills": ["system_health", "incident_management", "performance_optimization"]
            },
            "monitor-agent": {
                "agent_type": "Monitor",
                "skills": ["system_monitoring", "anomaly_detection", "alert_management"]
            },
            "database-integration-agent": {
                "agent_type": "DBIntegration",
                "skills": ["design_schema", "create_migration", "migration path optimization"]
            },
            "backend-development-agent": {
                "agent_type": "Backend ",
                "skills": ["business logic flow", "api_endpoint_creation", "authentication_implementation"]
            },

            "research-agent": {
                "agent_type": "Research",
                "skills": ["market_research", "competitor_analysis", "trend_analysis"]
            },
            "content-agent": {
                "agent_type": "Content",
                "skills": ["content_creation", "content_optimization", "content_distribution"]
            }
        }
        logger.info("Initialized default agent capabilities for testing")
    
    async def handle_task_decomposition_skill(self, context: A2ATaskContext) -> A2ATaskResult:
        """
        Break down a complex task into manageable subtasks.
        
        This skill takes a complex task description and breaks it down into
        subtasks that can be assigned to different agents based on their
        capabilities.
        
        Args:
            context: Task context containing the complex task description
            
        Returns:
            Task result with execution plan
        """
        logger.info(f"DelegationAgent ({self.id}) decomposing task")
        await context.update_status("working", message_text="Breaking down complex task...")
        
        # Extract the complex task
        complex_task = None
        task_metadata = {}
        
        if context.get_text_parts():
            complex_task = context.get_text_parts()[0]
        elif context.get_data_parts():
            data = context.get_data_parts()[0]
            if "task" in data:
                complex_task = data["task"]
            if "metadata" in data:
                task_metadata = data["metadata"]
        
        if not complex_task:
            return A2ATaskResult(
                status="failed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text="Missing complex task description")]
                )
            )
        
        # Generate a unique plan ID
        plan_id = str(uuid.uuid4())
        
        # Analyze the task and break it down into subtasks
        subtasks = self._analyze_and_decompose(complex_task)
        
        # Identify dependencies between subtasks
        dependencies = self._identify_dependencies(subtasks)
        
        # Match subtasks to agent capabilities
        agent_assignments = await self._match_subtasks_to_agents(subtasks)
        
        # Create execution plan with dependencies
        execution_plan = self._create_execution_plan(
            plan_id=plan_id,
            complex_task=complex_task,
            subtasks=subtasks,
            dependencies=dependencies,
            agent_assignments=agent_assignments,
            metadata=task_metadata
        )
        
        # Store the plan in both KB and agent memory
        await self.knowledge_base.set_value(f"execution_plans/{plan_id}", execution_plan)
        await self._memory.store(f"execution_plans/{plan_id}", execution_plan)
        
        # Store decision rationale in agent memory
        await self._memory.store_decision("task_decomposition", {
            "plan_id": plan_id,
            "complex_task": complex_task,
            "rationale": {
                "subtask_identification": "Identified subtasks based on task components and actions",
                "dependency_analysis": "Determined dependencies based on logical flow and prerequisites",
                "agent_assignment": "Matched subtasks to agents based on skill requirements"
            }
        })
        
        # Create a summary of the execution plan
        summary = self._format_plan_summary(execution_plan)
        
        # Return the execution plan
        return A2ATaskResult(
            status="completed",
            message=A2AMessage(
                role="agent",
                parts=[A2ATextPart(text=f"Task decomposition completed. Plan ID: {plan_id}")]
            ),
            artifacts=[
                A2AArtifact(
                    name=f"execution_plan_{plan_id}",
                    description="Task Execution Plan",
                    parts=[
                        A2ATextPart(text=summary),
                        A2ADataPart(data=execution_plan)
                    ]
                )
            ]
        )
    
    def _analyze_and_decompose(self, complex_task: str) -> List[Dict[str, Any]]:
        """
        Analyze a complex task and break it down into subtasks.
        
        Args:
            complex_task: Complex task description
            
        Returns:
            List of subtasks
        """
        # In a real implementation, this would use more sophisticated NLP
        # For now, we'll use a simple rule-based approach
        
        # Clean and normalize the task description
        task_clean = complex_task.strip()
        
        # Extract potential subtasks based on common patterns
        subtasks = []
        
        # Look for numbered lists (1. Task, 2. Task, etc.)
        numbered_tasks = re.findall(r'(?:^|\n)\s*(\d+\.?\s*[^\n]+)', task_clean)
        if numbered_tasks:
            for i, task in enumerate(numbered_tasks):
                # Remove the number and leading/trailing whitespace
                task_text = re.sub(r'^\s*\d+\.?\s*', '', task).strip()
                subtasks.append({
                    "id": f"subtask_{i+1}",
                    "description": task_text,
                    "estimated_effort": self._estimate_effort(task_text),
                    "required_skills": self._identify_required_skills(task_text)
                })
        
        # Look for bulleted lists (• Task, - Task, * Task, etc.)
        if not subtasks:
            bulleted_tasks = re.findall(r'(?:^|\n)\s*[•\-\*]\s*([^\n]+)', task_clean)
            if bulleted_tasks:
                for i, task in enumerate(bulleted_tasks):
                    subtasks.append({
                        "id": f"subtask_{i+1}",
                        "description": task.strip(),
                        "estimated_effort": self._estimate_effort(task),
                        "required_skills": self._identify_required_skills(task)
                    })
        
        # If no structured lists found, break down by sentences or phrases
        if not subtasks:
            # Split by periods, question marks, or exclamation points followed by a space
            sentences = re.split(r'[.!?]\s+', task_clean)
            
            # Filter out very short sentences (likely not tasks)
            sentences = [s for s in sentences if len(s) > 15]
            
            for i, sentence in enumerate(sentences):
                if self._is_actionable(sentence):
                    subtasks.append({
                        "id": f"subtask_{i+1}",
                        "description": sentence.strip(),
                        "estimated_effort": self._estimate_effort(sentence),
                        "required_skills": self._identify_required_skills(sentence)
                    })
        
        # If still no subtasks, create artificial breakdown
        if not subtasks:
            # Split the task into roughly equal parts
            words = task_clean.split()
            chunk_size = max(5, len(words) // 3)  # Aim for 3 subtasks minimum
            
            for i in range(0, len(words), chunk_size):
                chunk = ' '.join(words[i:i+chunk_size])
                if chunk:
                    subtasks.append({
                        "id": f"subtask_{i//chunk_size+1}",
                        "description": chunk,
                        "estimated_effort": self._estimate_effort(chunk),
                        "required_skills": self._identify_required_skills(chunk)
                    })
        
        # Ensure we have at least one subtask
        if not subtasks:
            subtasks.append({
                "id": "subtask_1",
                "description": task_clean,
                "estimated_effort": self._estimate_effort(task_clean),
                "required_skills": self._identify_required_skills(task_clean)
            })
        
        return subtasks
    
    def _is_actionable(self, text: str) -> bool:
        """
        Determine if a piece of text describes an actionable task.
        
        Args:
            text: Text to analyze
            
        Returns:
            True if the text is actionable, False otherwise
        """
        # Check if the text starts with a verb or contains action-oriented words
        action_words = [
            "create", "develop", "build", "implement", "design", "analyze",
            "research", "write", "prepare", "review", "test", "deploy",
            "monitor", "evaluate", "assess", "identify", "find", "gather",
            "collect", "organize", "plan", "schedule", "coordinate", "manage"
        ]
        
        text_lower = text.lower()
        
        # Check if the text starts with an action word
        for word in action_words:
            if text_lower.startswith(word) or f" {word} " in text_lower:
                return True
        
        return False
    
    def _estimate_effort(self, task: str) -> str:
        """
        Estimate the effort required for a task.
        
        Args:
            task: Task description
            
        Returns:
            Effort estimate (low, medium, high)
        """
        # Simple heuristic based on task length and complexity indicators
        task_lower = task.lower()
        
        # Check for complexity indicators
        complexity_indicators = [
            "complex", "difficult", "challenging", "comprehensive", "detailed",
            "thorough", "extensive", "in-depth", "complete", "full"
        ]
        
        # Check for simplicity indicators
        simplicity_indicators = [
            "simple", "easy", "straightforward", "basic", "quick", "brief",
            "short", "small", "minor", "trivial"
        ]
        
        # Count indicators
        complexity_count = sum(1 for word in complexity_indicators if word in task_lower)
        simplicity_count = sum(1 for word in simplicity_indicators if word in task_lower)
        
        # Base effort on task length
        if len(task) < 50:
            base_effort = "low"
        elif len(task) < 100:
            base_effort = "medium"
        else:
            base_effort = "high"
        
        # Adjust based on indicators
        if complexity_count > simplicity_count:
            # Increase effort
            if base_effort == "low":
                return "medium"
            elif base_effort == "medium":
                return "high"
            else:
                return "high"
        elif simplicity_count > complexity_count:
            # Decrease effort
            if base_effort == "high":
                return "medium"
            elif base_effort == "medium":
                return "low"
            else:
                return "low"
        
        return base_effort
    
    def _identify_required_skills(self, task: str) -> List[str]:
        """
        Identify the skills required for a task.
        
        Args:
            task: Task description
            
        Returns:
            List of required skills
        """
        # Map keywords to skills
        skill_keywords = {
            "business_strategy": ["strategy", "business", "market", "opportunity", "growth", "plan"],
            "executive_decision": ["decision", "approve", "authorize", "prioritize", "allocate"],
            "resource_allocation": ["resource", "budget", "allocate", "assign", "distribute"],
            "technology_assessment": ["technology", "tech", "assess", "evaluate", "compare"],
            "mvp_conceptualization": ["mvp", "product", "concept", "design", "prototype"],
            "mvp_team_assembly": ["team", "assemble", "assign", "staff", "resource"],
            "system_health": ["health", "monitor", "status", "check", "verify"],
            "incident_management": ["incident", "issue", "problem", "resolve", "fix"],
            "performance_optimization": ["performance", "optimize", "improve", "enhance", "speed"],
            "system_monitoring": ["monitor", "track", "observe", "watch", "log"],
            "anomaly_detection": ["anomaly", "unusual", "detect", "identify", "find"],
            "alert_management": ["alert", "notification", "warn", "inform", "notify"],
            "market_research": ["research", "market", "industry", "competitor", "trend"],
            "competitor_analysis": ["competitor", "competition", "analyze", "compare", "benchmark"],
            "trend_analysis": ["trend", "pattern", "analyze", "forecast", "predict"],
            "content_creation": ["content", "create", "write", "develop", "produce"],
            "content_optimization": ["optimize", "improve", "enhance", "refine", "seo"],
            "content_distribution": ["distribute", "publish", "share", "promote", "spread"]
        }
        
        task_lower = task.lower()
        required_skills = []
        
        # Check for skill keywords in the task
        for skill, keywords in skill_keywords.items():
            if any(keyword in task_lower for keyword in keywords):
                required_skills.append(skill)
        
        # Ensure we have at least one skill
        if not required_skills:
            # Default to a general skill based on task characteristics
            if "research" in task_lower or "analyze" in task_lower:
                required_skills.append("market_research")
            elif "develop" in task_lower or "build" in task_lower:
                required_skills.append("mvp_conceptualization")
            elif "monitor" in task_lower or "track" in task_lower:
                required_skills.append("system_monitoring")
            else:
                required_skills.append("business_strategy")  # Default
        
        return required_skills
    
    def _identify_dependencies(self, subtasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Identify dependencies between subtasks.
        
        Args:
            subtasks: List of subtasks
            
        Returns:
            Dictionary mapping subtask IDs to lists of dependency subtask IDs
        """
        dependencies = {}
        
        # Initialize dependencies for each subtask
        for subtask in subtasks:
            dependencies[subtask["id"]] = []
        
        # In a real implementation, this would use more sophisticated analysis
        # For now, we'll use a simple sequential approach
        for i in range(1, len(subtasks)):
            current_subtask = subtasks[i]
            previous_subtask = subtasks[i-1]
            
            # Check if the current subtask likely depends on the previous one
            current_desc = current_subtask["description"].lower()
            previous_desc = previous_subtask["description"].lower()
            
            # Look for dependency indicators
            dependency_indicators = [
                "after", "following", "once", "then", "next", "subsequently",
                "based on", "using", "with", "from"
            ]
            
            # Check if any dependency indicators are present
            if any(indicator in current_desc for indicator in dependency_indicators):
                dependencies[current_subtask["id"]].append(previous_subtask["id"])
            
            # Check for shared keywords that might indicate a dependency
            current_words = set(current_desc.split())
            previous_words = set(previous_desc.split())
            shared_words = current_words.intersection(previous_words)
            
            # If there are significant shared keywords, there might be a dependency
            if len(shared_words) >= 3 and len(shared_words) / len(current_words) > 0.3:
                if previous_subtask["id"] not in dependencies[current_subtask["id"]]:
                    dependencies[current_subtask["id"]].append(previous_subtask["id"])
        
        return dependencies
    
    async def _match_subtasks_to_agents(self, subtasks: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Match subtasks to agents based on required skills.
        
        Args:
            subtasks: List of subtasks
            
        Returns:
            Dictionary mapping subtask IDs to agent IDs
        """
        agent_assignments = {}
        
        # Get agent capabilities
        agent_capabilities = self._capability_registry
        
        # Match subtasks to agents
        for subtask in subtasks:
            subtask_id = subtask["id"]
            required_skills = subtask["required_skills"]
            
            # Find the best agent for this subtask
            best_agent_id = None
            best_match_score = -1
            
            for agent_id, capabilities in agent_capabilities.items():
                agent_skills = capabilities.get("skills", [])
                
                # Calculate match score (number of required skills the agent has)
                match_score = sum(1 for skill in required_skills if skill in agent_skills)
                
                # If this agent is a better match, update the best agent
                if match_score > best_match_score:
                    best_match_score = match_score
                    best_agent_id = agent_id
            
            # If no agent has any of the required skills, assign to a default agent
            if best_agent_id is None:
                # Use the first agent as default
                if agent_capabilities:
                    best_agent_id = next(iter(agent_capabilities.keys()))
                else:
                    best_agent_id = "default-agent"  # Fallback
            
            # Assign the subtask to the best agent
            agent_assignments[subtask_id] = best_agent_id
        
        return agent_assignments
    
    def _create_execution_plan(
        self,
        plan_id: str,
        complex_task: str,
        subtasks: List[Dict[str, Any]],
        dependencies: Dict[str, List[str]],
        agent_assignments: Dict[str, str],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create an execution plan for the subtasks.
        
        Args:
            plan_id: Unique ID for the plan
            complex_task: Original complex task description
            subtasks: List of subtasks
            dependencies: Dictionary mapping subtask IDs to dependency subtask IDs
            agent_assignments: Dictionary mapping subtask IDs to agent IDs
            metadata: Additional metadata for the plan
            
        Returns:
            Execution plan
        """
        # Calculate the execution order based on dependencies
        execution_order = self._calculate_execution_order(subtasks, dependencies)
        
        # Create the execution plan
        execution_plan = {
            "id": plan_id,
            "created_at": datetime.now().isoformat(),
            "status": "created",
            "original_task": complex_task,
            "subtasks": subtasks,
            "dependencies": dependencies,
            "agent_assignments": agent_assignments,
            "execution_order": execution_order,
            "metadata": metadata
        }
        
        return execution_plan
    
    def _calculate_execution_order(
        self,
        subtasks: List[Dict[str, Any]],
        dependencies: Dict[str, List[str]]
    ) -> List[List[str]]:
        """
        Calculate the execution order for subtasks based on dependencies.
        
        Args:
            subtasks: List of subtasks
            dependencies: Dictionary mapping subtask IDs to dependency subtask IDs
            
        Returns:
            List of lists of subtask IDs, where each inner list represents
            subtasks that can be executed in parallel
        """
        # Create a set of all subtask IDs
        all_subtask_ids = {subtask["id"] for subtask in subtasks}
        
        # Create a dictionary mapping subtask IDs to their remaining dependencies
        remaining_dependencies = {
            subtask_id: set(dependencies.get(subtask_id, []))
            for subtask_id in all_subtask_ids
        }
        
        # Create the execution order
        execution_order = []
        
        # Continue until all subtasks have been assigned to the execution order
        while remaining_dependencies:
            # Find subtasks with no remaining dependencies
            ready_subtasks = [
                subtask_id for subtask_id, deps in remaining_dependencies.items()
                if not deps
            ]
            
            # If no subtasks are ready, there might be a circular dependency
            if not ready_subtasks:
                # Break the circular dependency by selecting a subtask with the fewest dependencies
                subtask_id = min(
                    remaining_dependencies.items(),
                    key=lambda x: len(x[1])
                )[0]
                ready_subtasks = [subtask_id]
                logger.warning(f"Possible circular dependency detected. Breaking by selecting {subtask_id}")
            
            # Add the ready subtasks to the execution order
            execution_order.append(ready_subtasks)
            
            # Remove the ready subtasks from the remaining dependencies
            for subtask_id in ready_subtasks:
                del remaining_dependencies[subtask_id]
            
            # Remove the ready subtasks from the dependencies of other subtasks
            for deps in remaining_dependencies.values():
                deps.difference_update(ready_subtasks)
        
        return execution_order
    
    def _format_plan_summary(self, execution_plan: Dict[str, Any]) -> str:
        """
        Format a summary of the execution plan.
        
        Args:
            execution_plan: Execution plan
            
        Returns:
            Formatted summary
        """
        summary = f"Execution Plan: {execution_plan['id']}\n\n"
        
        # Add original task
        summary += f"Original Task: {execution_plan['original_task']}\n\n"
        
        # Add subtasks
        summary += "Subtasks:\n"
        for subtask in execution_plan["subtasks"]:
            agent_id = execution_plan["agent_assignments"].get(subtask["id"], "unassigned")
            summary += f"- {subtask['id']}: {subtask['description']} (Assigned to: {agent_id}, Effort: {subtask['estimated_effort']})\n"
        
        # Add execution order
        summary += "\nExecution Order:\n"
        for i, phase in enumerate(execution_plan["execution_order"]):
            summary += f"Phase {i+1}: {', '.join(phase)}\n"
        
        return summary
    
    async def handle_plan_execution_skill(self, context: A2ATaskContext) -> A2ATaskResult:
        """
        Execute a task execution plan.
        
        This skill takes an execution plan and coordinates the execution of
        subtasks by different agents.
        
        Args:
            context: Task context containing the execution plan or plan ID
            
        Returns:
            Task result with execution results
        """
        logger.info(f"DelegationAgent ({self.id}) executing plan")
        await context.update_status("working", message_text="Executing task plan...")
        
        # Extract the execution plan or plan ID
        plan_id = None
        execution_plan = None
        
        if context.get_text_parts():
            plan_id = context.get_text_parts()[0]
        elif context.get_data_parts():
            data = context.get_data_parts()[0]
            if "plan_id" in data:
                plan_id = data["plan_id"]
            elif "id" in data:
                plan_id = data["id"]
            elif "execution_plan" in data:
                execution_plan = data["execution_plan"]
            else:
                execution_plan = data
        
        # If we have a plan ID but no plan, get the plan from the knowledge base
        if plan_id and not execution_plan:
            execution_plan = await self.knowledge_base.get_value(f"execution_plans/{plan_id}")
            
            if not execution_plan:
                return A2ATaskResult(
                    status="failed",
                    message=A2AMessage(
                        role="agent",
                        parts=[A2ATextPart(text=f"Execution plan not found for ID: {plan_id}")]
                    )
                )
        
        if not execution_plan:
            return A2ATaskResult(
                status="failed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text="Missing execution plan")]
                )
            )
        
        # Update plan status
        execution_plan["status"] = "executing"
        await self.knowledge_base.set_value(f"execution_plans/{execution_plan['id']}", execution_plan)
        
        # Execute the plan
        # In a real implementation, this would send tasks to agents and track progress
        # For now, we'll simulate execution
        
        # Simulate execution time
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        # Update plan status
        execution_plan["status"] = "completed"
        execution_plan["completed_at"] = datetime.now().isoformat()
        await self.knowledge_base.set_value(f"execution_plans/{execution_plan['id']}", execution_plan)
        
        # Return the execution results
        return A2ATaskResult(
            status="completed",
            message=A2AMessage(
                role="agent",
                parts=[A2ATextPart(text=f"Plan execution completed for plan {execution_plan['id']}")]
            ),
            artifacts=[
                A2AArtifact(
                    name=f"execution_results_{execution_plan['id']}",
                    description="Task Execution Results",
                    parts=[
                        A2ATextPart(text=f"Execution of plan {execution_plan['id']} completed successfully."),
                        A2ADataPart(data=execution_plan)
                    ]
                )
            ]
        )
