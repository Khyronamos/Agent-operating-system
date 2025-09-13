class APIA_BaseAgent:
    # (Keep the async Base Agent from the previous step, ensuring skill routing registration is included)
    # Make sure imports for dependencies like A2ATaskContext, A2ATaskResult, Managers are correct
    from utils.protocols import MCPClientManager, A2AClientManager, A2ATaskRouter, A2ATaskContext, A2ATaskResult # noqa
    from utils.models import A2AAgentSkill, AgentCard, A2AArtifact, A2ATextPart, A2ADataPart, A2AFilePart, A2AFile # noqa
    import base64 # For file handling


    def __init__(
        self,
        role: str,
        agent_id: str,
        knowledge_base: APIA_KnowledgeBase,
        agent_registry: APIA_AgentRegistry,
        mcp_manager: MCPClientManager,
        a2a_client: A2AClientManager,
        a2a_router: A2ATaskRouter,
        internal_skills: List[str],
        a2a_skills: List[A2AAgentSkill],
        config_override: Dict = {},
        initial_state: Dict = {}
    ):
        self.id = agent_id
        self.role = role
        self.knowledge_base = knowledge_base
        self.agent_registry = agent_registry
        self.mcp = mcp_manager
        self.a2a_client = a2a_client
        self.a2a_router = a2a_router
        self.internal_skills = set(internal_skills)
        self.a2a_skills = a2a_skills
        self.config = {"max_internal_queue_size": 100, **config_override} # Simple default config

        self.internal_task_queue = asyncio.PriorityQueue(maxsize=self.config["max_internal_queue_size"])
        """
        DEPRECATION WARNING (Potentially): This internal queue is primarily
        a remnant of the pre-A2A architecture or for self-scheduling internal
        periodic tasks (like AIOps monitoring trigger).

        Consider replacing its usage with A2A calls, potentially even self-calls
        (Agent makes an A2A call to its own endpoint), to standardize task processing.
        Keeping it for now allows handling purely internal logic loops or maintaining
        compatibility during transition. Evaluate removal in future iterations.
        """

        self.status = "initializing"
        self.current_internal_task_id = None
        self.error_count = 0
        self.completed_task_count = 0
        self.created_at = datetime.now()
        self._stop_event = asyncio.Event()
        self._lock = asyncio.Lock()
        self._run_task: Optional[asyncio.Task] = None

        # Register specific A2A skill handlers
        for skill in self.a2a_skills:
            handler_method_name = f"handle_{skill.id.replace('-', '_')}_skill" # Convention
            handler = getattr(self, handler_method_name, self.handle_a2a_task) # Fallback to default
            # Ensure the handler is actually awaitable
            if not asyncio.iscoroutinefunction(handler):
                 logger.error(f"A2A handler '{handler_method_name}' for skill '{skill.id}' in agent '{self.role}' is not an async function!")
                 # Optionally skip registration or raise error
                 continue
            # Registration needs to happen *after* the event loop is running, use create_task
            # If called before loop starts, this might cause issues. Better place might be agent.start()
            # Let's keep it here for now assuming it's called after loop starts.
            try:
                asyncio.create_task(self.a2a_router.register_handler(skill.id, handler))
            except RuntimeError as e:
                 logger.warning(f"Could not register handler for {skill.id} during init (event loop might not be running?): {e}")


        # Register with registry (needs event loop running too)
        try:
             asyncio.create_task(self.agent_registry.register(self))
        except RuntimeError as e:
             logger.warning(f"Could not register agent {self.role} during init (event loop might not be running?): {e}")

        self.status = "idle"

    async def initialize(self):
        """
        Placeholder for agent-specific asynchronous initialization
        called after __init__ and typically invoked by a managing component
        or by the agent's own `start` sequence if appropriate.
        Subclasses should call `await super().initialize()` if they override this.
        """
        # Registration of A2A handlers and agent to registry is done in __init__
        # to ensure they are set up when the agent object is created.
        # This method is more for loading resources or initial state setup
        # that needs to be async and might depend on a running event loop.
        logger.debug(f"BaseAgent ({self.id}) initialize method called.")
        await asyncio.sleep(0.01) # Simulate some base init work if any

    async def initialize_state(self, state: Dict):
        logger.info(f"Agent {self.role} ({self.id}) initializing state.")
        # Add specific state loading logic here if needed
        await asyncio.sleep(0.01)

    async def receive_internal_task(self, task: Dict):
        async with self._lock:
            try:
                await self.internal_task_queue.put((-task.get("priority", 5), task))
                logger.info(f"Agent {self.role} ({self.id}) received internal task")
            except asyncio.QueueFull:
                 logger.warning(f"Agent {self.role} ({self.id}) internal queue full. Discarding task.")


    async def run(self):
        logger.info(f"Agent {self.role} ({self.id}) started run loop.")
        self.status = "idle"
        # Register handlers here maybe, if loop is guaranteed running?
        # for skill in self.a2a_skills: ... register ...
        # await self.agent_registry.register(self) # Ensure registration happens within running loop

        while not self._stop_event.is_set():
            try:
                neg_priority, task_data = await asyncio.wait_for(
                    self.internal_task_queue.get(), timeout=30.0
                )

                async with self._lock:
                    self.status = "busy"
                    self.current_internal_task_id = task_data.get("id", "N/A")

                try:
                    logger.info(f"Agent {self.role} ({self.id}) starting internal task: {task_data.get('type', 'N/A')}")
                    result = await self.execute_internal_task(task_data)
                    self.completed_task_count += 1
                    logger.debug(f"Internal task {self.current_internal_task_id} completed with result: {result}")
                except Exception as e:
                    logger.error(f"Agent {self.role} ({self.id}) failed executing internal task {self.current_internal_task_id}: {e}", exc_info=True)
                    self.error_count += 1
                finally:
                    async with self._lock:
                        self.status = "idle"
                        self.current_internal_task_id = None
                    self.internal_task_queue.task_done()

            except asyncio.TimeoutError:
                await self.run_periodic()
            except asyncio.CancelledError:
                 logger.info(f"Agent {self.role} ({self.id}) run loop cancelled.")
                 break
            except Exception as e:
                logger.error(f"Agent {self.role} ({self.id}) encountered error in run loop: {e}", exc_info=True)
                async with self._lock:
                    self.status = "error"
                await asyncio.sleep(5)

        logger.info(f"Agent {self.role} ({self.id}) stopped run loop.")
        self.status = "stopped"

    async def run_periodic(self):
        pass # Subclasses override

    async def execute_internal_task(self, task_data: Dict) -> Any:
        logger.warning(f"{self.role} agent received internal task but execute_internal_task is not implemented: {task_data.get('type')}")
        await asyncio.sleep(0.1)
        return {"status": "ignored"}

    # Default A2A Handler (integrates file part logic)
    async def handle_a2a_task(self, context: 'A2ATaskContext') -> 'A2ATaskResult':
        skill_id_attempt = context.task.metadata.get("skill_id", "unknown") if context.task.metadata else "unknown"
        logger.warning(f"{self.role} ({self.id}) received A2A task using default handler for skill '{skill_id_attempt}'.")

        incoming_text = context.get_text_parts()
        file_parts = context.get_file_parts()
        processed_files_info = []

        await context.update_status("working", message_text="Processing your request...")

        if file_parts:
             await context.update_status("working", message_text=f"Processing {len(file_parts)} files...")
             for file_part in file_parts:
                  try:
                      file_content = await context.process_file_part(file_part) # Use the context method
                      processed_files_info.append({"name": file_part.file.name, "size": len(file_content), "status": "processed (placeholder)"})
                  except Exception as e:
                      logger.error(f"Failed to process file '{file_part.file.name}' in default handler: {e}")
                      processed_files_info.append({"name": file_part.file.name, "status": "failed", "error": str(e)})

        await asyncio.sleep(0.5)

        response_text = f"Echo from {self.role} ({skill_id_attempt}): Received task {context.task_id}. "
        response_text += f"Text: '{' '.join(incoming_text)}'. " if incoming_text else "No text input. "
        response_text += f"Files: {len(processed_files_info)} processed."

        artifact = A2AArtifact(
             parts=[
                 A2ATextPart(text=response_text),
                 A2ADataPart(data={"files_processed": processed_files_info})
             ]
        )
        return A2ATaskResult(status="completed", artifacts=[artifact])


    async def get_agent_card_info(self, base_url: str) -> AgentCard:
        async with self._lock:
            # Ensure URL is valid
            try:
                validated_url = HttpUrl(url=f"{base_url.rstrip('/')}")
            except Exception:
                 logger.error(f"Invalid base_url provided for agent card: {base_url}")
                 validated_url = HttpUrl(url="http://invalid.url") # Fallback

            return AgentCard(
                name=self.role,
                description=f"APIA Agent performing role: {self.role}",
                url=validated_url,
                version="1.1-modular",
                capabilities=A2AAgentCapabilities(streaming=True), # Assume streaming
                skills=self.a2a_skills,
            )

    async def get_status_summary(self) -> Dict:
        async with self._lock:
            q_size = self.internal_task_queue.qsize() if self.internal_task_queue else 0
            return {
                "id": self.id, "role": self.role, "status": self.status,
                "internal_queue_size": q_size,
                "current_internal_task_id": self.current_internal_task_id,
                "error_count": self.error_count,
                "completed_task_count": self.completed_task_count,
                "created_at": self.created_at.isoformat(),
            }

    def start(self):
        if not self._run_task or self._run_task.done():
            self._stop_event.clear()
            # Ensure registration happens after loop starts if init fails
            async def _start_and_register():
                 # Maybe register here instead of __init__?
                 # await self.agent_registry.register(self)
                 # for skill in self.a2a_skills: ... await self.a2a_router.register_handler(...) ...
                 await self.run()
            self._run_task = asyncio.create_task(_start_and_register())
            logger.info(f"Agent {self.role} ({self.id}) run task created.")
        else:
            logger.warning(f"Agent {self.role} ({self.id}) start called but task is already running.")

    async def stop(self):
         # (Keep the async stop implementation from the previous step)
        if self._stop_event.is_set(): return
        logger.info(f"Stopping agent {self.role} ({self.id})...")
        self._stop_event.set()
        # Signal internal queue to unblock getter if waiting
        try: await self.internal_task_queue.put((float('inf'), None)) # Sentinel
        except asyncio.QueueFull: pass

        if self._run_task and not self._run_task.done():
             try:
                 # Wait briefly, then cancel if needed
                 await asyncio.wait_for(self._run_task, timeout=5.0)
             except asyncio.TimeoutError:
                 logger.warning(f"Agent {self.role} ({self.id}) run loop did not stop gracefully, cancelling.")
                 self._run_task.cancel()
                 try: await self._run_task
                 except asyncio.CancelledError: pass
             except Exception as e: logger.error(f"Error waiting for agent {self.role} stop: {e}")
        logger.info(f"Agent {self.role} ({self.id}) stopped signal processed.")
        self.status = "stopped"
