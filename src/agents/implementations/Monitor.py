# agents/resource_monitor.py
import logging
from datetime import datetime

from core.framework import APIA_BaseAgent
from utils.protocols import A2ATaskContext, A2ATaskResult
from utils.models import A2AArtifact, A2ATextPart, A2ADataPart

logger = logging.getLogger(__name__)

class APIA_ResourceMonitorAgent(APIA_BaseAgent):
    """
    Monitors external resource usage via MCP or direct checks.
    Example Skills: check_api_quota, check_db_connections
    """

    # Example specific handler using MCP
    async def handle_check_api_quota_skill(self, context: A2ATaskContext) -> A2ATaskResult:
        logger.info(f"Resource Monitor ({self.id}) executing: check_api_quota")
        target_api = context.metadata.get("target_api") if context.metadata else "unknown_api"
        mcp_server_name = context.metadata.get("mcp_server") if context.metadata else "metrics" # Default to 'metrics' server

        await context.update_status("working", message_text=f"Checking quota for API: {target_api}...")

        quota_info = {"api": target_api, "limit": None, "usage": None, "status": "unknown"}
        try:
            # Use MCP to get API quota information
            logger.info(f"Calling MCP server '{mcp_server_name}' to check quota for {target_api}")
            mcp_result = await self.mcp.call_tool(mcp_server_name, "search_nodes", {"query": f"api_quota {target_api}"})

            # Process the result from MCP
            if isinstance(mcp_result, list) and len(mcp_result) > 0:
                # Extract quota information from search results
                for node in mcp_result:
                    if node.get("name", "").startswith(target_api):
                        # Found relevant quota information
                        quota_info.update({
                            "limit": node.get("quota_limit"),
                            "usage": node.get("quota_usage"),
                            "reset_time": node.get("quota_reset_time"),
                            "status": "active"
                        })
                        break
                if quota_info["status"] == "unknown":
                    quota_info["status"] = "no_quota_found"
            elif isinstance(mcp_result, dict):
                # Direct result format
                quota_info.update(mcp_result)
                quota_info["status"] = "active"
            else:
                quota_info["status"] = "no_data_returned"

            logger.info(f"MCP quota check for {target_api} completed with status: {quota_info['status']}")

        except Exception as e:
            logger.error(f"Resource Monitor failed to check quota for {target_api} via MCP {mcp_server_name}: {e}")
            quota_info["status"] = f"error"
            quota_info["error_message"] = str(e)

        # Create artifact with quota information
        artifact = A2AArtifact(parts=[
            A2ATextPart(text=f"API Quota for {target_api}: {quota_info['status']}"),
            A2ADataPart(data=quota_info)
        ])
        return A2ATaskResult(status="completed", artifacts=[artifact])

    # Add a new handler for checking system metrics
    async def handle_check_system_metrics_skill(self, context: A2ATaskContext) -> A2ATaskResult:
        logger.info(f"Resource Monitor ({self.id}) executing: check_system_metrics")
        metric_type = context.metadata.get("metric_type") if context.metadata else "cpu"
        mcp_server_name = context.metadata.get("mcp_server") if context.metadata else "metrics"

        await context.update_status("working", message_text=f"Checking system metrics for: {metric_type}...")

        try:
            # Use MCP to get system metrics
            logger.info(f"Calling MCP server '{mcp_server_name}' to check {metric_type} metrics")
            mcp_result = await self.mcp.call_tool(mcp_server_name, "search_nodes", {"query": metric_type})

            # Process the metrics data
            metrics_data = {
                "type": metric_type,
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "data": mcp_result
            }

            # Create a human-readable summary
            summary = f"System {metric_type} metrics retrieved successfully."
            if isinstance(mcp_result, list):
                summary += f" Found {len(mcp_result)} data points."

            logger.info(f"MCP system metrics check completed: {summary}")

        except Exception as e:
            logger.error(f"Resource Monitor failed to check {metric_type} metrics via MCP {mcp_server_name}: {e}")
            metrics_data = {
                "type": metric_type,
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error_message": str(e)
            }
            summary = f"Failed to retrieve {metric_type} metrics: {e}"

        # Create artifact with metrics information
        artifact = A2AArtifact(parts=[
            A2ATextPart(text=summary),
            A2ADataPart(data=metrics_data)
        ])
        return A2ATaskResult(status="completed", artifacts=[artifact])

    # Add other resource checking handlers (e.g., db connections)