# agents/cto.py
import asyncio
import logging
import random
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from core.framework import APIA_BaseAgent
from utils.protocols import A2ATaskContext, A2ATaskResult
from utils.models import A2AArtifact, A2ATextPart, A2ADataPart, A2AMessage, A2ATaskSendParams
from utils.memory import AgentMemory

logger = logging.getLogger(__name__)

class APIA_CTOAgent(APIA_BaseAgent):

    async def initialize(self, memory_dir: Optional[str] = None):
        logger.info(f"CTO Agent ({self.id}) initializing...")

        # Initialize agent-specific memory
        self._memory = AgentMemory(self.id, memory_dir)

        # Any CTO-specific initialization here
        await super().initialize()

        logger.info(f"CTO Agent ({self.id}) initialized with agent-specific memory")

    async def handle_technology_assessment_skill(self, context: A2ATaskContext) -> A2ATaskResult:
        logger.info(f"CTO ({self.id}) executing specific handler for: technology_assessment")
        await context.update_status("working", message_text="CTO assessing technology...")

        tech_to_assess = None
        if context.get_text_parts():
            tech_to_assess = context.get_text_parts()[0]
        elif context.metadata and context.metadata.get("technology"):
            tech_to_assess = context.metadata["technology"]

        if not tech_to_assess:
            return A2ATaskResult(status="failed", message=A2AMessage(role="agent", parts=[A2ATextPart(text="Missing technology name for assessment.")]))

        try:
            tech_stack = await self.knowledge_base.get_value("tech_stack", default={})
            approved = tech_stack.get("approved", [])
            experimental = tech_stack.get("experimental", [])
        except Exception as e:
            logger.error(f"CTO failed to access knowledge base: {e}")
            return A2ATaskResult(status="failed", message=A2AMessage(role="agent", parts=[A2ATextPart(text=f"Error accessing knowledge base: {e}")]))

        await asyncio.sleep(random.uniform(0.5, 1.5)) # Simulate assessment time

        assessment = {"technology": tech_to_assess, "scores": {}, "recommendation": "Undecided"}
        # Simplified assessment logic
        criteria = {
            "maturity": round(random.uniform(0.5, 1.0), 2),
            "support": round(random.uniform(0.6, 1.0), 2),
            "performance": round(random.uniform(0.7, 1.0), 2),
            "cost_efficiency": round(random.uniform(0.4, 0.9), 2),
            "alignment": round(random.uniform(0.5, 1.0), 2), # Strategic alignment
        }
        assessment["scores"] = criteria
        overall_score = sum(criteria.values()) / len(criteria)
        assessment["recommendation"] = "Recommended" if overall_score >= 0.7 else "Not Recommended"

        notes = []
        if tech_to_assess in approved: notes.append("Currently approved.")
        elif tech_to_assess in experimental: notes.append("Currently experimental.")
        else: notes.append("Not currently listed in tech stack.")
        assessment["notes"] = notes

        artifact = A2AArtifact(
            name=f"{tech_to_assess}_assessment",
            parts=[A2ADataPart(data=assessment)]
        )
        return A2ATaskResult(status="completed", artifacts=[artifact])

    async def handle_mvp_conceptualization_skill(self, context: A2ATaskContext) -> A2ATaskResult:
        """
        Transform business requirements into technical MVP specifications.

        This skill takes business requirements as input and produces a detailed
        technical specification for an MVP (Minimum Viable Product).

        Args:
            context: Task context containing business requirements

        Returns:
            Task result with MVP specification
        """
        logger.info(f"CTO ({self.id}) executing MVP conceptualization")
        await context.update_status("working", message_text="CTO conceptualizing MVP...")

        # Extract business requirements from context
        business_requirements = None
        if context.get_text_parts():
            business_requirements = context.get_text_parts()[0]
        elif context.get_data_parts():
            data = context.get_data_parts()[0]
            business_requirements = data.get("requirements")

        if not business_requirements:
            return A2ATaskResult(
                status="failed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text="Missing business requirements for MVP conceptualization.")]
                )
            )

        # Generate a unique project ID
        project_id = str(uuid.uuid4())

        # Simulate analysis time
        await asyncio.sleep(random.uniform(1.0, 2.0))

        # Create MVP specification
        mvp_spec = {
            "id": project_id,
            "created_at": datetime.now().isoformat(),
            "status": "conceptualized",
            "business_requirements": business_requirements,
            "components": self._determine_components(business_requirements),
            "architecture": self._design_architecture(business_requirements),
            "timeline": self._estimate_timeline(business_requirements),
            "risks": self._identify_risks(business_requirements),
            "tech_stack": self._select_tech_stack(business_requirements),
            "resources": self._estimate_resources(business_requirements)
        }

        # Store the MVP specification in the knowledge base (shared state)
        await self.knowledge_base.set_value(f"mvp_projects/{project_id}", mvp_spec)

        # Store decision rationale in agent-specific memory
        await self._memory.store_decision("mvp_conceptualization", {
            "project_id": project_id,
            "business_requirements": business_requirements,
            "rationale": {
                "component_selection": "Selected components based on key requirements mentions",
                "architecture_choice": f"Selected {mvp_spec['architecture']['type']} architecture for simplicity and speed",
                "timeline_factors": f"Estimated {mvp_spec['timeline']['estimated_weeks']} weeks based on complexity assessment",
                "tech_stack_reasoning": "Selected modern, well-supported technologies with good ecosystem"
            }
        })

        # Create a summary of the MVP specification
        summary = f"MVP Concept: {project_id}\n\n"
        summary += f"Components: {', '.join(mvp_spec['components'])}\n"
        summary += f"Architecture: {mvp_spec['architecture']['type']}\n"
        summary += f"Timeline: {mvp_spec['timeline']['estimated_weeks']} weeks\n"
        summary += f"Tech Stack: {', '.join(mvp_spec['tech_stack'])}\n"

        # Return the MVP specification
        return A2ATaskResult(
            status="completed",
            message=A2AMessage(
                role="agent",
                parts=[A2ATextPart(text=f"MVP conceptualization completed. Project ID: {project_id}")]
            ),
            artifacts=[
                A2AArtifact(
                    name=f"mvp_spec_{project_id}",
                    description="MVP Technical Specification",
                    parts=[
                        A2ATextPart(text=summary),
                        A2ADataPart(data=mvp_spec)
                    ]
                )
            ]
        )

    def _determine_components(self, requirements: str) -> List[str]:
        """Determine the components needed for the MVP based on requirements."""
        components = []

        # Simple keyword-based component determination, will be upgraded in next version
        if "user interface" in requirements.lower() or "ui" in requirements.lower():
            components.append("frontend")

        if "api" in requirements.lower() or "backend" in requirements.lower() or "server" in requirements.lower():
            components.append("backend")

        if "data" in requirements.lower() or "database" in requirements.lower() or "storage" in requirements.lower():
            components.append("database")

        if "authentication" in requirements.lower() or "auth" in requirements.lower() or "login" in requirements.lower():
            components.append("authentication")

        if "analytics" in requirements.lower() or "reporting" in requirements.lower() or "dashboard" in requirements.lower():
            components.append("analytics")

        # Ensure we have at least frontend and backend
        if not components or ("frontend" not in components and "backend" not in components):
            components = ["frontend", "backend"]

        return components

    def _design_architecture(self, requirements: str) -> Dict[str, Any]:
        """Design the architecture for the MVP based on requirements."""
        # Determine architecture type
        if "microservices" in requirements.lower():
            arch_type = "microservices"
        elif "serverless" in requirements.lower():
            arch_type = "serverless"
        else:
            arch_type = "monolithic"

        # Create architecture specification
        architecture = {
            "type": arch_type,
            "description": f"{arch_type.capitalize()} architecture for MVP",
            "components": {},
            "data_flow": [],
            "deployment": {}
        }

        return architecture

    def _estimate_timeline(self, requirements: str) -> Dict[str, Any]:
        """Estimate the timeline for the MVP based on requirements."""
        # Simple complexity-based estimation
        complexity = 1.0

        # Adjust complexity based on keywords
        if "complex" in requirements.lower() or "complicated" in requirements.lower():
            complexity *= 1.5

        if "simple" in requirements.lower() or "basic" in requirements.lower():
            complexity *= 0.7

        if "urgent" in requirements.lower() or "fast" in requirements.lower():
            complexity *= 0.8

        # Calculate timeline
        base_weeks = 4
        estimated_weeks = int(base_weeks * complexity)

        # Create timeline specification
        timeline = {
            "estimated_weeks": estimated_weeks,
            "phases": [
                {"name": "Planning", "duration": max(1, int(estimated_weeks * 0.2))},
                {"name": "Development", "duration": max(2, int(estimated_weeks * 0.6))},
                {"name": "Testing", "duration": max(1, int(estimated_weeks * 0.2))}
            ],
            "milestones": [
                {"name": "Requirements Finalized", "week": 1},
                {"name": "MVP Alpha", "week": max(2, int(estimated_weeks * 0.5))},
                {"name": "MVP Beta", "week": max(3, int(estimated_weeks * 0.8))},
                {"name": "MVP Release", "week": estimated_weeks}
            ]
        }

        return timeline

    def _identify_risks(self, requirements: str) -> List[Dict[str, Any]]:
        """Identify risks for the MVP based on requirements."""
        risks = [
            {
                "category": "Technical",
                "description": "Integration complexity may be higher than anticipated",
                "probability": "medium",
                "impact": "high",
                "mitigation": "Early integration testing and clear API contracts"
            },
            {
                "category": "Schedule",
                "description": "Timeline may slip due to scope creep",
                "probability": "high",
                "impact": "medium",
                "mitigation": "Strict scope management and regular reviews"
            }
        ]

        # Add specific risks based on requirements
        if "security" in requirements.lower() or "sensitive" in requirements.lower():
            risks.append({
                "category": "Security",
                "description": "Sensitive data handling requires additional security measures",
                "probability": "medium",
                "impact": "high",
                "mitigation": "Security review and penetration testing before release"
            })

        if "performance" in requirements.lower() or "speed" in requirements.lower():
            risks.append({
                "category": "Performance",
                "description": "System may not meet performance expectations under load",
                "probability": "medium",
                "impact": "high",
                "mitigation": "Early performance testing and optimization"
            })

        return risks

    def _select_tech_stack(self, requirements: str) -> List[str]:
        """Select the technology stack for the MVP based on requirements."""
        # Get approved technologies from knowledge base
        tech_stack = []

        # Add technologies based on components and requirements
        if "frontend" in self._determine_components(requirements):
            tech_stack.append("react")

        if "backend" in self._determine_components(requirements):
            tech_stack.append("python")
            tech_stack.append("fastapi")

        if "database" in self._determine_components(requirements):
            if "nosql" in requirements.lower() or "document" in requirements.lower():
                tech_stack.append("mongodb")
            else:
                tech_stack.append("postgres")

        return tech_stack

    def _estimate_resources(self, requirements: str) -> Dict[str, Any]:
        """Estimate the resources needed for the MVP based on requirements."""
        # Determine components
        components = self._determine_components(requirements)

        # Calculate developer resources needed
        frontend_devs = 1 if "frontend" in components else 0
        backend_devs = 1 if "backend" in components else 0
        database_devs = 1 if "database" in components else 0

        # Adjust based on complexity
        complexity = 1.0
        if "complex" in requirements.lower() or "complicated" in requirements.lower():
            complexity = 1.5

        # Create resources specification
        resources = {
            "developers": {
                "frontend": frontend_devs,
                "backend": backend_devs,
                "database": database_devs,
                "total": max(1, int((frontend_devs + backend_devs + database_devs) * complexity))
            },
            "infrastructure": {
                "servers": max(1, len(components) - 1),
                "databases": 1 if "database" in components else 0,
                "storage_gb": 10 * (1 if "database" in components else 0.5)
            },
            "tools": [
                "git",
                "ci/cd",
                "issue tracker"
            ]
        }

        return resources

    async def handle_mvp_team_assembly_skill(self, context: A2ATaskContext) -> A2ATaskResult:
        """
        Assemble a team of specialized agents to build an MVP.

        This skill takes an MVP specification and creates a team of specialized
        agents to build the MVP.

        Args:
            context: Task context containing MVP specification or project ID

        Returns:
            Task result with team information
        """
        logger.info(f"CTO ({self.id}) executing MVP team assembly")
        await context.update_status("working", message_text="CTO assembling MVP team...")

        # Extract project ID or MVP specification from context
        project_id = None
        mvp_spec = None

        if context.get_text_parts():
            project_id = context.get_text_parts()[0]
        elif context.get_data_parts():
            data = context.get_data_parts()[0]
            if "id" in data:
                project_id = data["id"]
                mvp_spec = data
            elif "project_id" in data:
                project_id = data["project_id"]

        if not project_id:
            return A2ATaskResult(
                status="failed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text="Missing project ID for MVP team assembly.")]
                )
            )

        # If we don't have the MVP spec yet, get it from the knowledge base
        if not mvp_spec:
            mvp_spec = await self.knowledge_base.get_value(f"mvp_projects/{project_id}")

            if not mvp_spec:
                return A2ATaskResult(
                    status="failed",
                    message=A2AMessage(
                        role="agent",
                        parts=[A2ATextPart(text=f"MVP specification not found for project ID: {project_id}")]
                    )
                )

        # Determine required agent types based on MVP components
        required_agents = []
        if "frontend" in mvp_spec["components"]:
            required_agents.append("FrontendDeveloperAgent")
        if "backend" in mvp_spec["components"]:
            required_agents.append("BackendDeveloperAgent")
        if "database" in mvp_spec["components"]:
            required_agents.append("DatabaseintegrationAgent")

        # Ensure we have at least one agent
        if not required_agents:
            required_agents.append("GenericDeveloperAgent")

        # Simulate team assembly time
        await asyncio.sleep(random.uniform(1.0, 2.0))

        # Create actual agent instances using the AgentFactory
        team_members = []
        creation_errors = []

        # Map agent types to blueprint roles
        agent_type_to_blueprint = {
            "BackendDeveloperAgent": "backend_developer",
            "FrontendDeveloperAgent": "frontend_developer",
            "DatabaseintegrationAgent": "database_integration",
            "GenericDeveloperAgent": "generic_developer"
        }

        # Get the agent factory from the registry
        # The AgentRegistry does not directly expose a get_agent_factory method.
        # The factory is initialized in main.py and stored in app.state.
        # For agents to access it, it needs to be passed during agent creation
        # or retrieved via a shared mechanism like the KnowledgeBase if stored there.
        # For now, we'll assume the factory is accessible via the registry for simplicity
        # or that the agent itself has a reference (which it does via self.agent_factory).
        # This part of the code needs to be aligned with how AgentFactory is truly managed.
        # For this MVP, we'll assume self.agent_factory is correctly populated.
        agent_factory = self.agent_factory # Access the factory directly from the agent's instance
        if not agent_factory:
            return A2ATaskResult(
                status="failed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text="Agent factory not available to CTO agent.")]
                )
            )

        # Create each required agent
        for agent_type in required_agents:
            blueprint_role = agent_type_to_blueprint.get(agent_type)
            if not blueprint_role:
                logger.warning(f"No blueprint mapping found for agent type: {agent_type}")
                blueprint_role = "generic_developer"  # Fallback to generic developer

            # Generate a unique agent ID for this project
            agent_id = f"{agent_type.lower()}_{project_id[:8]}"

            try:
                # Create the agent using the factory
                new_agent = await agent_factory.create_agent(blueprint_role, agent_id)

                if new_agent:
                    # Add the successfully created agent to the team
                    team_members.append({
                        "agent_id": new_agent.id,
                        "agent_type": agent_type,
                        "role": agent_type.replace("Agent", ""),
                        "status": "ready",
                        "blueprint_role": blueprint_role,
                        "skills": [skill.id for skill in new_agent.a2a_skills] if hasattr(new_agent, "a2a_skills") else []
                    })
                    logger.info(f"Created agent {new_agent.id} of type {agent_type} for project {project_id}")
                else:
                    # Record the error
                    creation_errors.append(f"Failed to create agent of type {agent_type} with blueprint {blueprint_role}")
                    logger.error(f"Failed to create agent of type {agent_type} with blueprint {blueprint_role}")
            except Exception as e:
                creation_errors.append(f"Error creating agent of type {agent_type}: {str(e)}")
                logger.error(f"Error creating agent of type {agent_type}: {e}", exc_info=True)

        # Create team record with status based on success/partial success
        status = "assembled" if team_members and not creation_errors else "partially_assembled" if team_members else "failed"

        team_record = {
            "project_id": project_id,
            "created_at": datetime.now().isoformat(),
            "status": status,
            "members": team_members,
            "lead": self.id,
            "errors": creation_errors
        }

        # Store the team record in the knowledge base (shared state)
        await self.knowledge_base.set_value(f"mvp_teams/{project_id}", team_record)

        # Store project history in agent-specific memory
        await self._memory.store_project_history(project_id, {
            "event": "team_assembly",
            "team_composition": team_members,
            "reasoning": {
                "frontend_developer": "Frontend developer needed for UI components",
                "backend_developer": "Backend developer needed for API and business logic",
                "database_integration": "Database integration needed for data modeling and storage"
            },
            "challenges": creation_errors if creation_errors else [],
            "decisions": [
                {
                    "decision": "team_composition",
                    "rationale": "Selected team composition based on MVP components"
                }
            ]
        })

        # Create a summary of the team
        summary = f"MVP Team for Project: {project_id}\n\n"
        summary += f"Status: {team_record['status']}\n"
        summary += f"Team Lead: {team_record['lead']}\n\n"
        summary += "Team Members:\n"
        for member in team_members:
            summary += f"- {member['role']} ({member['agent_id']})\n"

        # Return the team information
        return A2ATaskResult(
            status="completed",
            message=A2AMessage(
                role="agent",
                parts=[A2ATextPart(text=f"MVP team assembled for project {project_id}. {len(team_members)} agents ready.")]
            ),
            artifacts=[
                A2AArtifact(
                    name=f"mvp_team_{project_id}",
                    description="MVP Team Information",
                    parts=[
                        A2ATextPart(text=summary),
                        A2ADataPart(data=team_record)
                    ]
                )
            ]
        )

    async def handle_mvp_orchestration_skill(self, context: A2ATaskContext) -> A2ATaskResult:
        """
        Orchestrate the MVP development process across a team of specialized agents.

        This skill takes an MVP specification and team information, then coordinates
        the development process by breaking down tasks, assigning them to team members,
        tracking progress, and integrating components.

        Args:
            context: Task context containing MVP specification or project ID

        Returns:
            Task result with orchestration status and artifacts
        """
        logger.info(f"CTO ({self.id}) executing MVP orchestration")
        await context.update_status("working", message_text="CTO orchestrating MVP development...")

        # Extract project ID or MVP specification from context
        project_id = None
        mvp_spec = None

        if context.get_text_parts():
            project_id = context.get_text_parts()[0]
        elif context.get_data_parts():
            data = context.get_data_parts()[0]
            if "id" in data:
                project_id = data["id"]
                mvp_spec = data
            elif "project_id" in data:
                project_id = data["project_id"]

        if not project_id:
            return A2ATaskResult(
                status="failed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text="Missing project ID for MVP orchestration.")]
                )
            )

        # If we don't have the MVP spec yet, get it from the knowledge base
        if not mvp_spec:
            mvp_spec = await self.knowledge_base.get_value(f"mvp_projects/{project_id}")

            if not mvp_spec:
                return A2ATaskResult(
                    status="failed",
                    message=A2AMessage(
                        role="agent",
                        parts=[A2ATextPart(text=f"MVP specification not found for project ID: {project_id}")]
                    )
                )

        # Get the team information from the knowledge base
        team_info = await self.knowledge_base.get_value(f"mvp_teams/{project_id}")

        if not team_info:
            return A2ATaskResult(
                status="failed",
                message=A2AMessage(
                    role="agent",
                    parts=[A2ATextPart(text=f"Team information not found for project ID: {project_id}. Please assemble a team first.")]
                )
            )

        # Create an orchestration plan
        orchestration_plan = await self._create_orchestration_plan(project_id, mvp_spec, team_info)

        # Store the orchestration plan in the knowledge base
        await self.knowledge_base.set_value(f"mvp_orchestration/{project_id}", orchestration_plan)

        # Execute the orchestration plan
        orchestration_result = await self._execute_orchestration_plan(project_id, orchestration_plan, team_info)

        # Store the orchestration result in the knowledge base
        await self.knowledge_base.set_value(f"mvp_orchestration_results/{project_id}", orchestration_result)

        # Store orchestration history in agent-specific memory
        await self._memory.store_project_history(project_id, {
            "event": "mvp_orchestration",
            "orchestration_plan": orchestration_plan,
            "orchestration_result": orchestration_result,
            "timestamp": datetime.now().isoformat()
        })

        # Create a summary of the orchestration
        summary = f"MVP Orchestration for Project: {project_id}\n\n"
        summary += f"Status: {orchestration_result['status']}\n"
        summary += f"Phases Completed: {orchestration_result['phases_completed']}/{len(orchestration_plan['phases'])}\n"
        summary += f"Tasks Completed: {orchestration_result['tasks_completed']}/{orchestration_result['total_tasks']}\n\n"

        if orchestration_result['status'] == "completed":
            summary += "All phases completed successfully!\n\n"
        elif orchestration_result['status'] == "in_progress":
            summary += "Orchestration is still in progress.\n\n"
        else:
            summary += f"Orchestration encountered issues: {orchestration_result['issues']}\n\n"

        # Add research results if available
        if "research" in orchestration_result:
            summary += "Technology Research:\n"

            # Add best practices
            if orchestration_result["research"].get("best_practices"):
                summary += "Best Practices:\n"
                for practice in orchestration_result["research"]["best_practices"][:3]:  # Limit to top 3
                    summary += f"- {practice.get('technology')}: {practice.get('title')}\n"
                summary += "\n"

            # Add resources
            if orchestration_result["research"].get("resources"):
                summary += "Learning Resources:\n"
                for resource in orchestration_result["research"]["resources"][:3]:  # Limit to top 3
                    summary += f"- {resource.get('technology')}: {resource.get('title')}\n"
                summary += "\n"

        summary += "Key Deliverables:\n"
        for artifact in orchestration_result['artifacts']:
            summary += f"- {artifact['name']}: {artifact['description']}\n"

        # Return the orchestration result
        return A2ATaskResult(
            status="completed",
            message=A2AMessage(
                role="agent",
                parts=[A2ATextPart(text=f"MVP orchestration {orchestration_result['status']} for project {project_id}.")]
            ),
            artifacts=[
                A2AArtifact(
                    name=f"mvp_orchestration_{project_id}",
                    description="MVP Orchestration Summary",
                    parts=[
                        A2ATextPart(text=summary),
                        A2ADataPart(data=orchestration_result)
                    ]
                )
            ]
        )

    async def _create_orchestration_plan(self, project_id: str, mvp_spec: Dict[str, Any], team_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an orchestration plan for the MVP development process.

        Args:
            project_id: Project ID
            mvp_spec: MVP specification
            team_info: Team information

        Returns:
            Orchestration plan
        """
        logger.info(f"Creating orchestration plan for project {project_id}")

        # Define the phases of the MVP development process
        phases = [
            {
                "id": "planning",
                "name": "Planning",
                "description": "Define the detailed requirements and architecture",
                "tasks": [
                    {
                        "id": f"{project_id}_task_requirements",
                        "name": "Detailed Requirements",
                        "description": "Create detailed requirements based on the MVP specification",
                        "assigned_to": None,  # Will be assigned based on skills
                        "required_skills": ["requirements_analysis"],
                        "dependencies": [],
                        "status": "pending",
                        "artifacts": []
                    },
                    {
                        "id": f"{project_id}_task_architecture",
                        "name": "Technical Architecture",
                        "description": "Design the technical architecture for the MVP",
                        "assigned_to": None,  # Will be assigned based on skills
                        "required_skills": ["architecture_design"],
                        "dependencies": [f"{project_id}_task_requirements"],
                        "status": "pending",
                        "artifacts": []
                    }
                ]
            },
            {
                "id": "development",
                "name": "Development",
                "description": "Implement the MVP components",
                "tasks": []  # Will be populated based on components
            },
            {
                "id": "integration",
                "name": "Integration",
                "description": "Integrate the MVP components",
                "tasks": [
                    {
                        "id": f"{project_id}_task_integration",
                        "name": "Component Integration",
                        "description": "Integrate all MVP components",
                        "assigned_to": None,  # Will be assigned based on skills
                        "required_skills": ["system_integration"],
                        "dependencies": [],  # Will be populated based on development tasks
                        "status": "pending",
                        "artifacts": []
                    }
                ]
            },
            {
                "id": "testing",
                "name": "Testing",
                "description": "Test the MVP",
                "tasks": [
                    {
                        "id": f"{project_id}_task_testing",
                        "name": "System Testing",
                        "description": "Test the integrated MVP",
                        "assigned_to": None,  # Will be assigned based on skills
                        "required_skills": ["system_testing"],
                        "dependencies": [f"{project_id}_task_integration"],
                        "status": "pending",
                        "artifacts": []
                    }
                ]
            },
            {
                "id": "deployment",
                "name": "Deployment",
                "description": "Prepare the MVP for deployment",
                "tasks": [
                    {
                        "id": f"{project_id}_task_deployment",
                        "name": "Deployment Preparation",
                        "description": "Prepare the MVP for deployment",
                        "assigned_to": None,  # Will be assigned based on skills
                        "required_skills": ["deployment"],
                        "dependencies": [f"{project_id}_task_testing"],
                        "status": "pending",
                        "artifacts": []
                    }
                ]
            }
        ]

        # Add component-specific development tasks based on the MVP components
        development_tasks = []
        for component in mvp_spec["components"]:
            component_id = component.lower().replace(" ", "_")
            task_id = f"{project_id}_task_dev_{component_id}"

            # Determine required skills based on component
            required_skills = []
            if component == "frontend":
                required_skills = ["frontend_development"]
            elif component == "backend":
                required_skills = ["backend_development"]
            elif component == "database":
                required_skills = ["database_development"]
            elif component == "authentication":
                required_skills = ["security_development"]
            else:
                required_skills = ["generic_development"]

            # Create the task
            task = {
                "id": task_id,
                "name": f"{component.capitalize()} Development",
                "description": f"Implement the {component} component",
                "assigned_to": None,  # Will be assigned based on skills
                "required_skills": required_skills,
                "dependencies": [f"{project_id}_task_architecture"],
                "status": "pending",
                "artifacts": []
            }

            development_tasks.append(task)

            # Add this task as a dependency for the integration task
            integration_task = next((task for phase in phases for task in phase["tasks"] if task["id"] == f"{project_id}_task_integration"), None)
            if integration_task:
                integration_task["dependencies"].append(task_id)

        # Add the development tasks to the development phase
        for phase in phases:
            if phase["id"] == "development":
                phase["tasks"] = development_tasks

        # Create the orchestration plan
        orchestration_plan = {
            "id": f"{project_id}_orchestration",
            "project_id": project_id,
            "created_at": datetime.now().isoformat(),
            "status": "created",
            "phases": phases,
            "team_info": team_info,
            "mvp_spec": mvp_spec
        }

        return orchestration_plan

    async def _execute_orchestration_plan(self, project_id: str, orchestration_plan: Dict[str, Any], team_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the orchestration plan for the MVP development process.

        Args:
            project_id: Project ID
            orchestration_plan: Orchestration plan
            team_info: Team information

        Returns:
            Orchestration result
        """
        logger.info(f"Executing orchestration plan for project {project_id}")

        # Initialize orchestration result
        orchestration_result = {
            "project_id": project_id,
            "started_at": datetime.now().isoformat(),
            "status": "in_progress",
            "phases_completed": 0,
            "tasks_completed": 0,
            "total_tasks": sum(len(phase["tasks"]) for phase in orchestration_plan["phases"]),
            "current_phase": orchestration_plan["phases"][0]["id"],
            "artifacts": [],
            "issues": []
        }

        # Get the delegation agent to help with task assignment and execution
        delegation_agent = await self._get_delegation_agent()

        if not delegation_agent:
            orchestration_result["status"] = "failed"
            orchestration_result["issues"].append("Failed to get delegation agent")
            return orchestration_result

        # Get the browser use agent to help with research
        browser_agent = await self._get_browser_use_agent()

        # If browser agent is available, conduct initial research for the project
        if browser_agent:
            logger.info(f"Using browser agent to research technologies for project {project_id}")
            research_results = await self._conduct_technology_research(browser_agent, orchestration_plan["mvp_spec"])

            if research_results:
                # Add research results to the orchestration result
                orchestration_result["research"] = research_results

                # Store research results in the knowledge base
                await self.knowledge_base.set_value(f"mvp_research/{project_id}", research_results)

        # Assign tasks to team members based on their skills
        await self._assign_tasks_to_team_members(orchestration_plan, team_info)

        # For each phase in the orchestration plan
        for phase_index, phase in enumerate(orchestration_plan["phases"]):
            logger.info(f"Executing phase {phase['id']} for project {project_id}")
            orchestration_result["current_phase"] = phase["id"]

            # Update the orchestration result in the knowledge base
            await self.knowledge_base.set_value(f"mvp_orchestration_results/{project_id}", orchestration_result)

            # Execute the tasks in this phase
            phase_result = await self._execute_phase(project_id, phase, delegation_agent)

            # Update the orchestration result with the phase result
            if phase_result["status"] == "completed":
                orchestration_result["tasks_completed"] += len(phase["tasks"])
                orchestration_result["phases_completed"] += 1
                orchestration_result["artifacts"].extend(phase_result["artifacts"])
            else:
                orchestration_result["status"] = "failed"
                orchestration_result["issues"].append(f"Phase {phase['id']} failed: {phase_result['issues']}")
                break

            # Update the orchestration result in the knowledge base
            await self.knowledge_base.set_value(f"mvp_orchestration_results/{project_id}", orchestration_result)

        # If all phases completed successfully, update the status
        if orchestration_result["status"] == "in_progress":
            orchestration_result["status"] = "completed"
            orchestration_result["completed_at"] = datetime.now().isoformat()

        # Final update to the orchestration result in the knowledge base
        await self.knowledge_base.set_value(f"mvp_orchestration_results/{project_id}", orchestration_result)

        return orchestration_result

    async def _get_delegation_agent(self) -> Optional[str]:
        """
        Get the delegation agent ID from the agent registry.

        Returns:
            Delegation agent ID or None if not found
        """
        logger.info("Looking for delegation agent")

        # Get all agents from the registry
        agents = await self.agent_registry.get_all_agents()

        # Find the delegation agent
        for agent_id, agent_info in agents.items():
            if agent_info.get("role") == "delegation" or agent_info.get("type") == "DelegationAgent":
                logger.info(f"Found delegation agent: {agent_id}")
                return agent_id

        logger.warning("Delegation agent not found")
        return None

    async def _get_browser_use_agent(self) -> Optional[str]:
        """
        Get the browser use agent ID from the agent registry.

        Returns:
            Browser use agent ID or None if not found
        """
        logger.info("Looking for browser use agent")

        # Get all agents from the registry
        agents = await self.agent_registry.get_all_agents()

        # Find the browser use agent
        for agent_id, agent_info in agents.items():
            if agent_info.get("role") == "browser_use" or agent_info.get("type") == "BrowserUseAgent":
                logger.info(f"Found browser use agent: {agent_id}")
                return agent_id

        logger.warning("Browser use agent not found")
        return None

    async def _conduct_technology_research(self, browser_agent_id: str, mvp_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Conduct research on technologies for the MVP using the browser use agent.

        Args:
            browser_agent_id: Browser use agent ID
            mvp_spec: MVP specification

        Returns:
            Research results
        """
        logger.info("Conducting technology research")

        # Initialize research results
        research_results = {
            "technologies": {},
            "best_practices": [],
            "resources": [],
            "timestamp": datetime.now().isoformat()
        }

        try:
            # Research each technology in the tech stack
            for tech in mvp_spec.get("tech_stack", []):
                # Create a search query for the technology
                search_query = f"{tech} best practices for {mvp_spec.get('architecture', {}).get('type', 'web')} development"

                # Send the search query to the browser use agent
                search_message = A2AMessage(
                    role="user",
                    parts=[A2ATextPart(text=search_query)],
                    metadata={"skill_id": "search_web"}
                )

                search_params = A2ATaskSendParams(message=search_message)

                # Use the A2A client to send the task to the browser use agent
                search_result = await self.a2a_client.send_task(browser_agent_id, search_params)

                # Process the search result
                if search_result.status == "completed" and search_result.artifacts:
                    # Extract search results from the artifacts
                    for artifact in search_result.artifacts:
                        if "search_results" in artifact.name:
                            # Add the search results to the research results
                            research_results["technologies"][tech] = {
                                "search_query": search_query,
                                "results": artifact.parts[0].data if hasattr(artifact.parts[0], "data") else str(artifact.parts[0])
                            }

                            # Extract best practices and resources from the search results
                            if hasattr(artifact.parts[0], "data") and isinstance(artifact.parts[0].data, list):
                                for result in artifact.parts[0].data:
                                    if "best practice" in result.get("title", "").lower() or "best practice" in result.get("snippet", "").lower():
                                        research_results["best_practices"].append({
                                            "technology": tech,
                                            "title": result.get("title"),
                                            "url": result.get("url"),
                                            "snippet": result.get("snippet")
                                        })

                                    if "tutorial" in result.get("title", "").lower() or "guide" in result.get("title", "").lower():
                                        research_results["resources"].append({
                                            "technology": tech,
                                            "title": result.get("title"),
                                            "url": result.get("url"),
                                            "type": "tutorial"
                                        })

            # Research architecture best practices
            arch_type = mvp_spec.get("architecture", {}).get("type", "monolithic")
            arch_query = f"{arch_type} architecture best practices"

            arch_message = A2AMessage(
                role="user",
                parts=[A2ATextPart(text=arch_query)],
                metadata={"skill_id": "search_web"}
            )

            arch_params = A2ATaskSendParams(message=arch_message)

            # Use the A2A client to send the task to the browser use agent
            arch_result = await self.a2a_client.send_task(browser_agent_id, arch_params)

            # Process the architecture search result
            if arch_result.status == "completed" and arch_result.artifacts:
                # Extract architecture search results from the artifacts
                for artifact in arch_result.artifacts:
                    if "search_results" in artifact.name:
                        # Add the architecture search results to the research results
                        research_results["architecture"] = {
                            "search_query": arch_query,
                            "results": artifact.parts[0].data if hasattr(artifact.parts[0], "data") else str(artifact.parts[0])
                        }

            return research_results

        except Exception as e:
            logger.error(f"Error conducting technology research: {e}", exc_info=True)
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _assign_tasks_to_team_members(self, orchestration_plan: Dict[str, Any], team_info: Dict[str, Any]) -> None:
        """
        Assign tasks to team members based on their skills.

        Args:
            orchestration_plan: Orchestration plan
            team_info: Team information
        """
        logger.info("Assigning tasks to team members")

        # Create a mapping of skills to team members
        skill_to_members = {}
        for member in team_info["members"]:
            for skill in member.get("skills", []):
                if skill not in skill_to_members:
                    skill_to_members[skill] = []
                skill_to_members[skill].append(member["agent_id"])

        # For each phase in the orchestration plan
        for phase in orchestration_plan["phases"]:
            # For each task in the phase
            for task in phase["tasks"]:
                # Find a team member with the required skills
                assigned = False
                for required_skill in task["required_skills"]:
                    if required_skill in skill_to_members and skill_to_members[required_skill]:
                        # Assign the task to the first team member with the required skill
                        task["assigned_to"] = skill_to_members[required_skill][0]
                        assigned = True
                        break

                # If no team member has the required skills, assign to a generic worker
                if not assigned:
                    # Find a generic worker
                    generic_workers = [member["agent_id"] for member in team_info["members"]
                                      if "generic" in member["agent_type"].lower()]

                    if generic_workers:
                        task["assigned_to"] = generic_workers[0]
                    else:
                        # If no generic worker, assign to the team lead (self)
                        task["assigned_to"] = self.id

    async def _execute_phase(self, project_id: str, phase: Dict[str, Any], delegation_agent_id: str) -> Dict[str, Any]:
        """
        Execute a phase of the orchestration plan.

        Args:
            project_id: Project ID
            phase: Phase to execute
            delegation_agent_id: Delegation agent ID

        Returns:
            Phase execution result
        """
        logger.info(f"Executing phase {phase['id']} for project {project_id}")

        # Initialize phase result
        phase_result = {
            "phase_id": phase["id"],
            "status": "in_progress",
            "tasks_completed": 0,
            "total_tasks": len(phase["tasks"]),
            "artifacts": [],
            "issues": []
        }

        # Create a task for the delegation agent to execute this phase
        delegation_task = {
            "project_id": project_id,
            "phase_id": phase["id"],
            "tasks": phase["tasks"],
            "description": phase["description"]
        }

        try:
            # Send the task to the delegation agent
            delegation_message = A2AMessage(
                role="user",
                parts=[A2ADataPart(data=delegation_task)],
                metadata={"skill_id": "plan_execution"}
            )

            delegation_params = A2ATaskSendParams(message=delegation_message)

            # Use the A2A client to send the task to the delegation agent
            delegation_result = await self.a2a_client.send_task(delegation_agent_id, delegation_params)

            # Process the delegation result
            if delegation_result.status == "completed":
                # Extract artifacts from the delegation result
                for artifact in delegation_result.artifacts:
                    phase_result["artifacts"].append({
                        "name": artifact.name,
                        "description": artifact.description,
                        "content": artifact.parts[0].data if hasattr(artifact.parts[0], "data") else str(artifact.parts[0])
                    })

                phase_result["status"] = "completed"
                phase_result["tasks_completed"] = len(phase["tasks"])
            else:
                phase_result["status"] = "failed"
                phase_result["issues"].append(f"Delegation agent failed to execute phase: {delegation_result.message}")

        except Exception as e:
            logger.error(f"Error executing phase {phase['id']} for project {project_id}: {e}", exc_info=True)
            phase_result["status"] = "failed"
            phase_result["issues"].append(f"Error executing phase: {str(e)}")

        return phase_result

    # Future skills to implement:
    # - handle_mvp_evaluation_skill: Evaluate a completed MVP