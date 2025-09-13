




class APIA_KnowledgeBase:
    # (Keep the async KB implementation from the previous step)
    def __init__(self):
        self._data: Dict[str, Any] = {
            "strategic_goals": {},
            "system_metrics": {"agent_health": {}, "a2a_tasks": {"received": 0, "completed": 0, "failed": 0}, "dlq_count": 0},
            "tech_stack": {"approved": ["python", "fastapi", "postgres", "react"], "experimental": ["rust", "chromadb"]},
            "architecture_blueprints": {},
            "agent_blueprints": {},
            "performance_history": {},
            "aiops_config": {"restart_threshold": 0.5, "monitoring_interval_sec": 60},
            "dependency_status": {}
        }
        self._lock = asyncio.Lock()
        logger.info("APIA Knowledge Base initialized (Async).")

    async def set_value(self, key: str, value: Any):
        async with self._lock:
            self._data[key] = value
            logger.debug(f"KnowledgeBase set: {key}")

    async def get_value(self, key: str, default: Any = None) -> Any:
        async with self._lock:
            return self._data.get(key, default)

    async def update_metric(self, metric_category: str, metric_name: str, value: Any):
        async with self._lock:
            metrics_data = self._data.setdefault("system_metrics", {})
            category_data = metrics_data.setdefault(metric_category, {})
            category_data[metric_name] = value

            if isinstance(value, (int, float)):
                history_key = f"{metric_category}.{metric_name}"
                history_data = self._data.setdefault("performance_history", {})
                history_list = history_data.setdefault(history_key, [])
                history_list.append((datetime.now(), value))
                self._data["performance_history"][history_key] = history_list[-100:]

            logger.debug(f"Metric updated: {metric_category}.{metric_name} = {value}")

    async def get_metric(self, metric_category: str, metric_name: str, default: Any = None) -> Any:
        async with self._lock:
            return self._data.get("system_metrics", {}).get(metric_category, {}).get(metric_name, default)

    async def get_agent_dependency_status(self, agent_id: str) -> bool:
        async with self._lock:
            return self._data.get("dependency_status", {}).get(agent_id, False)

    async def set_agent_dependency_status(self, agent_id: str, has_issues: bool):
        async with self._lock:
            self._data.setdefault("dependency_status", {})[agent_id] = has_issues
            logger.info(f"Dependency status for agent {agent_id} set to {has_issues}")