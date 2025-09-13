# agents/compliance.py
import logging
import asyncio

from core.framework import APIA_BaseAgent
from utils.protocols import A2ATaskContext, A2ATaskResult
from utils.models import A2AMessage, A2ATextPart, A2ADataPart, A2AArtifact

logger = logging.getLogger(__name__)

class APIA_ComplianceAgent(APIA_BaseAgent):
    """
    Monitors specific tasks or KB changes for compliance violations.
    Example Skills: audit_task_completion, check_kb_change
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load compliance rules (e.g., from config or KB)
        self.rules = {
            "PII_IN_ARTIFACTS": {"enabled": True, "keywords": ["ssn", "credit card", "password"]},
            "UNAPPROVED_TECH_PROPOSED": {"enabled": True}
        }
        logger.info(f"Compliance Agent ({self.id}) initialized with rules: {list(self.rules.keys())}")


    # This agent might not handle direct A2A requests, but subscribe to events
    # or be triggered by other agents/orchestrator.
    # Let's make a skill to be called *after* another task completes.
    async def handle_audit_task_completion_skill(self, context: A2ATaskContext) -> A2ATaskResult:
        logger.info(f"Compliance Agent ({self.id}) executing: audit_task_completion")

        # Get details of the completed task (passed in metadata)
        original_task_id = context.metadata.get("original_task_id") if context.metadata else None
        original_task_artifacts = context.metadata.get("original_task_artifacts") if context.metadata else [] # Simplified - need real artifact data

        if not original_task_id:
             return A2ATaskResult(status="failed", message=A2AMessage(role="agent", parts=[A2ATextPart(text="Missing original_task_id for audit.")]))

        await context.update_status("working", message_text=f"Auditing artifacts for task {original_task_id}...")

        # Use MCP to perform compliance check
        mcp_server_name = context.metadata.get("mcp_server") if context.metadata else "compliance"
        violations = []

        try:
            # Call MCP to check for PII in the artifacts
            logger.info(f"Calling MCP server '{mcp_server_name}' to check compliance for task {original_task_id}")

            # Prepare artifact text for compliance check
            artifact_texts = []
            for artifact_dict in original_task_artifacts:
                try:
                    artifact = A2AArtifact(**artifact_dict)
                    for part in artifact.parts:
                        if isinstance(part, A2ATextPart):
                            artifact_texts.append(part.text)
                except Exception as e:
                    logger.warning(f"Compliance: Error parsing artifact for audit: {e}")

            # Join all texts for the compliance check
            combined_text = "\n".join(artifact_texts)

            # Call MCP to check for compliance issues
            mcp_result = await self.mcp.call_tool(mcp_server_name, "search_nodes", {
                "query": "compliance_check",
                "text": combined_text,
                "rules": list(self.rules.keys())
            })

            # Process the compliance check results
            if isinstance(mcp_result, list) and len(mcp_result) > 0:
                for finding in mcp_result:
                    rule_name = finding.get("rule_name")
                    match = finding.get("match")
                    context = finding.get("context")
                    violations.append(f"Compliance issue: {rule_name} - Found '{match}' in context '{context}'")
            elif isinstance(mcp_result, dict) and "violations" in mcp_result:
                # Alternative format where violations are directly returned
                violations = mcp_result["violations"]

            logger.info(f"MCP compliance check completed with {len(violations)} violations found")

        except Exception as e:
            logger.error(f"Compliance Agent failed to check compliance via MCP {mcp_server_name}: {e}")
            # Fallback to local compliance check if MCP fails
            logger.warning("Falling back to local compliance check")

            # Rule: Check for PII keywords in text artifacts
            if self.rules["PII_IN_ARTIFACTS"]["enabled"]:
                keywords = self.rules["PII_IN_ARTIFACTS"]["keywords"]
                for artifact_dict in original_task_artifacts:
                    try:
                        artifact = A2AArtifact(**artifact_dict)
                        for part in artifact.parts:
                            if isinstance(part, A2ATextPart):
                                for keyword in keywords:
                                    if keyword in part.text.lower():
                                        violations.append(f"Potential PII ('{keyword}') detected in artifact '{artifact.name or artifact.index}' of task {original_task_id}")
                                        break
                    except Exception as e:
                        logger.warning(f"Compliance: Error parsing artifact for local audit: {e}")

        # Prepare the result
        if violations:
            logger.warning(f"Compliance violations found for task {original_task_id}: {violations}")
            # If violations found, we might want to trigger additional MCP actions
            try:
                # Notify about compliance violations via MCP
                await self.mcp.call_tool(mcp_server_name, "notify_compliance_violation", {
                    "task_id": original_task_id,
                    "violations": violations,
                    "severity": "high" if len(violations) > 3 else "medium"
                })
                logger.info(f"Sent compliance violation notification to MCP server {mcp_server_name}")
            except Exception as e:
                logger.error(f"Failed to notify about compliance violations via MCP: {e}")

            result_text = f"Compliance Violations Found for task {original_task_id}:\n" + "\n".join(f"- {v}" for v in violations)
            status = "completed_with_violations"
        else:
            logger.info(f"Compliance check passed for task {original_task_id}.")
            result_text = f"Compliance check passed for task {original_task_id}."
            status = "completed"

        artifact = A2AArtifact(parts=[A2ATextPart(text=result_text), A2ADataPart(data={"violations": violations})])
        # Use custom status in result message, final task status is 'completed'
        message = A2AMessage(role="agent", parts=[A2ATextPart(text=result_text)], metadata={"compliance_status": status})
        return A2ATaskResult(status="completed", message=message, artifacts=[artifact])

    # Add a new handler for checking tech stack compliance
    async def handle_check_tech_stack_compliance_skill(self, context: A2ATaskContext) -> A2ATaskResult:
        logger.info(f"Compliance Agent ({self.id}) executing: check_tech_stack_compliance")

        # Get the tech stack to check from the context
        tech_stack = context.metadata.get("tech_stack") if context.metadata else []
        if not tech_stack and context.get_text_parts():
            # Try to parse tech stack from text input
            text_input = " ".join(context.get_text_parts())
            tech_stack = [tech.strip() for tech in text_input.split(",")]

        if not tech_stack:
            return A2ATaskResult(status="failed", message=A2AMessage(role="agent", parts=[A2ATextPart(text="No tech stack specified for compliance check.")]))

        await context.update_status("working", message_text=f"Checking compliance for tech stack: {', '.join(tech_stack)}...")

        # Use MCP to check tech stack compliance
        mcp_server_name = context.metadata.get("mcp_server") if context.metadata else "compliance"

        try:
            # Call MCP to check tech stack compliance
            logger.info(f"Calling MCP server '{mcp_server_name}' to check tech stack compliance")
            mcp_result = await self.mcp.call_tool(mcp_server_name, "search_nodes", {
                "query": "approved_technologies",
                "tech_stack": tech_stack
            })

            # Process the compliance check results
            approved_tech = []
            unapproved_tech = []
            experimental_tech = []

            if isinstance(mcp_result, dict):
                approved_tech = mcp_result.get("approved", [])
                unapproved_tech = mcp_result.get("unapproved", [])
                experimental_tech = mcp_result.get("experimental", [])
            elif isinstance(mcp_result, list):
                # Alternative format where each tech has a status
                for tech_info in mcp_result:
                    tech_name = tech_info.get("name")
                    tech_status = tech_info.get("status")
                    if tech_status == "approved":
                        approved_tech.append(tech_name)
                    elif tech_status == "experimental":
                        experimental_tech.append(tech_name)
                    else:
                        unapproved_tech.append(tech_name)

            # Fallback to checking against KB if MCP doesn't return expected format
            if not (approved_tech or unapproved_tech or experimental_tech):
                logger.warning("MCP didn't return tech stack categorization, falling back to KB check")
                kb_tech_stack = await self.knowledge_base.get_value("tech_stack", {})
                kb_approved = kb_tech_stack.get("approved", [])
                kb_experimental = kb_tech_stack.get("experimental", [])

                for tech in tech_stack:
                    if tech.lower() in [t.lower() for t in kb_approved]:
                        approved_tech.append(tech)
                    elif tech.lower() in [t.lower() for t in kb_experimental]:
                        experimental_tech.append(tech)
                    else:
                        unapproved_tech.append(tech)

            logger.info(f"Tech stack compliance check completed: {len(approved_tech)} approved, {len(experimental_tech)} experimental, {len(unapproved_tech)} unapproved")

            # Prepare the result
            compliance_status = "compliant" if not unapproved_tech else "non_compliant"
            result_data = {
                "status": compliance_status,
                "approved": approved_tech,
                "experimental": experimental_tech,
                "unapproved": unapproved_tech
            }

            # Create human-readable summary
            summary_parts = []
            if approved_tech:
                summary_parts.append(f"Approved technologies: {', '.join(approved_tech)}")
            if experimental_tech:
                summary_parts.append(f"Experimental technologies (use with caution): {', '.join(experimental_tech)}")
            if unapproved_tech:
                summary_parts.append(f"Unapproved technologies (compliance violation): {', '.join(unapproved_tech)}")

            summary = "\n".join(summary_parts)
            if compliance_status == "compliant":
                summary = "Tech stack is compliant with organizational policies.\n" + summary
            else:
                summary = "Tech stack contains unapproved technologies!\n" + summary

        except Exception as e:
            logger.error(f"Compliance Agent failed to check tech stack compliance via MCP {mcp_server_name}: {e}")
            compliance_status = "error"
            result_data = {
                "status": "error",
                "error_message": str(e),
                "tech_stack": tech_stack
            }
            summary = f"Failed to check tech stack compliance: {e}"

        # Create artifact with compliance information
        artifact = A2AArtifact(parts=[
            A2ATextPart(text=summary),
            A2ADataPart(data=result_data)
        ])
        return A2ATaskResult(status="completed", artifacts=[artifact])