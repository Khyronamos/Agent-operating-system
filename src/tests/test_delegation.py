#!/usr/bin/env python3
"""
Test script for the Delegation agent's task decomposition capabilities.

This script demonstrates how to use the Delegation agent to break down
complex tasks into manageable subtasks and create execution plans.
"""

import asyncio
import logging
import sys
import uuid
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.models import A2AMessage, A2ATextPart, A2ATaskSendParams
from utils.protocols import A2AClientManager
from core.framework import APIA_KnowledgeBase, APIA_AgentRegistry
from agents.implemtations.delegation import APIA_DelegationAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_task_decomposition():
    """Test the Delegation agent's task decomposition capability."""
    logger.info("Testing task decomposition...")
    
    # Create dependencies
    knowledge_base = APIA_KnowledgeBase()
    agent_registry = APIA_AgentRegistry()
    a2a_client = A2AClientManager()
    
    # Create Delegation agent
    delegation_agent = APIA_DelegationAgent(
        role="delegation",
        agent_id="delegation-test-agent",
        knowledge_base=knowledge_base,
        agent_registry=agent_registry,
        a2a_client=a2a_client,
        internal_skills=["task_analysis", "dependency_mapping"],
        a2a_skills=[]
    )
    
    # Create memory directory
    memory_dir = os.path.join(os.path.dirname(__file__), "memory")
    os.makedirs(memory_dir, exist_ok=True)
    
    # Initialize the agent with memory
    await delegation_agent.initialize(memory_dir=memory_dir)
    
    # Create a task context
    complex_task = """
    Launch a new marketing campaign for our product that includes:
    1. Conduct market research to identify target audience
    2. Develop messaging and creative assets
    3. Set up social media advertising campaigns
    4. Create email marketing sequences
    5. Implement analytics tracking
    6. Monitor campaign performance and optimize
    
    The campaign should focus on our new product features and target both existing customers and new prospects. We need to launch within 4 weeks and stay within a $10,000 budget.
    """
    
    # Create a message with the complex task
    message = A2AMessage(
        role="user",
        parts=[A2ATextPart(text=complex_task)],
        metadata={"skill_id": "task_decomposition"}
    )
    
    # Create task parameters
    task_params = A2ATaskSendParams(
        id=str(uuid.uuid4()),
        message=message
    )
    
    # Call the Delegation agent's task decomposition skill
    task_context = await delegation_agent.create_task_context(task_params)
    result = await delegation_agent.handle_task_decomposition_skill(task_context)
    
    # Print the result
    logger.info(f"Task decomposition result: {result.status}")
    
    # Extract the execution plan from the result
    execution_plan = None
    for artifact in result.artifacts:
        for part in artifact.parts:
            if hasattr(part, 'data'):
                execution_plan = part.data
                break
    
    if execution_plan:
        logger.info(f"Plan ID: {execution_plan['id']}")
        logger.info(f"Subtasks: {len(execution_plan['subtasks'])}")
        
        # Print subtasks
        logger.info("Subtasks:")
        for subtask in execution_plan['subtasks']:
            agent_id = execution_plan['agent_assignments'].get(subtask['id'], 'unassigned')
            logger.info(f"  - {subtask['id']}: {subtask['description']} (Assigned to: {agent_id})")
        
        # Print execution order
        logger.info("Execution Order:")
        for i, phase in enumerate(execution_plan['execution_order']):
            logger.info(f"  Phase {i+1}: {', '.join(phase)}")
        
        # Check agent memory for decision rationale
        decisions = await delegation_agent._memory.get_decisions("task_decomposition")
        if decisions:
            logger.info("Found decision rationale in agent memory:")
            for decision in decisions:
                logger.info(f"  - Plan: {decision['plan_id']}")
                logger.info(f"  - Rationale: {decision['rationale']}")
        else:
            logger.warning("No decision rationale found in agent memory")
        
        # Now test plan execution
        await test_plan_execution(delegation_agent, execution_plan['id'])
    else:
        logger.error("No execution plan found in the result")

async def test_plan_execution(delegation_agent, plan_id):
    """Test the Delegation agent's plan execution capability."""
    logger.info(f"Testing plan execution for plan {plan_id}...")
    
    # Create a message with the plan ID
    message = A2AMessage(
        role="user",
        parts=[A2ATextPart(text=plan_id)],
        metadata={"skill_id": "plan_execution"}
    )
    
    # Create task parameters
    task_params = A2ATaskSendParams(
        id=str(uuid.uuid4()),
        message=message
    )
    
    # Call the Delegation agent's plan execution skill
    task_context = await delegation_agent.create_task_context(task_params)
    result = await delegation_agent.handle_plan_execution_skill(task_context)
    
    # Print the result
    logger.info(f"Plan execution result: {result.status}")
    
    # Extract the execution results from the result
    execution_results = None
    for artifact in result.artifacts:
        for part in artifact.parts:
            if hasattr(part, 'data'):
                execution_results = part.data
                break
    
    if execution_results:
        logger.info(f"Plan status: {execution_results['status']}")
        if 'completed_at' in execution_results:
            logger.info(f"Completed at: {execution_results['completed_at']}")
    else:
        logger.error("No execution results found in the result")

async def main():
    """Main function to run the tests."""
    try:
        await test_task_decomposition()
    except Exception as e:
        logger.exception(f"Error during test: {e}")

if __name__ == "__main__":
    asyncio.run(main())
