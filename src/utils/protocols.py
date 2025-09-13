# protocols.py
import json
import uuid
import asyncio
import logging
import base64
import time
from datetime import datetime
from typing import Optional, Callable, Dict, List, Any, Set, Tuple, Union

import httpx
try:
    from sse_starlette.sse import EventSourceResponse
except ImportError:
    logging.warning("sse_starlette not installed; SSE endpoints disabled.")
    class EventSourceResponse:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("SSE not available: install sse_starlette")

# Assuming modules are importable
from utils.config import MCPServerConfig
from utils.models import (
    AgentCard, A2ATask, A2AMessage, A2APart, A2AArtifact, A2ATaskState,
    A2ATaskSendParams, A2AJsonRpcRequest, A2AJsonRpcSuccessResponse,
    A2AJsonRpcErrorResponse, A2AJsonRpcErrorData, A2ATaskStatusUpdateEventResult,
    A2ATaskArtifactUpdateEventResult, A2ATaskUpdateEventResult, A2ATextPart,
    A2AFilePart, A2ADataPart
)
from core.exceptions import ConfigurationError, ActionFailedError, APIAException, A2AError, AgentNotFoundError
from core.framework import APIA_KnowledgeBase # For TaskManager

logger = logging.getLogger(__name__)

# --- MCP ---
import os

# Import real MCP components
try:
    from mcp import ClientSession, StdioServerParameters, TcpServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.client.tcp import tcp_client
    USE_MOCK = False
    logger.info("Using real MCP library components.")
except ImportError:
    logger.warning("MCP library not found, using mock implementation.")
    USE_MOCK = True

# Define mock implementations for testing or when MCP is not available
class MockMCPClientSession:
    async def initialize(self):
        logger.debug("Mock MCP session initialized")
        pass

    async def close(self):
        logger.debug("Mock MCP session closed")
        pass

    async def call_tool(self, tool_name: str, params: dict) -> dict:
        logger.debug(f"MCP MOCK: Calling tool '{tool_name}' with {params}")
        await asyncio.sleep(0.1)
        if tool_name == "add": return {"content": params.get("a",0) + params.get("b",0)}
        if tool_name == "search_nodes": return {"content": [{"name": "mock_entity", "observations": [f"related to {params.get('query')}"]}]}
        return {"content": f"Result for {tool_name}"}

    async def list_tools(self):
        return {"tools": [{"name": "add"}, {"name":"search_nodes"}]}

class MockStdioContext:
    async def __aenter__(self):
        return (None, None)

    async def __aexit__(self, *args):
        pass

async def mock_stdio_client(params):
    logger.debug(f"MCP MOCK: Connecting stdio: {params}")
    return MockStdioContext()

# Use mock or real implementations based on availability
if USE_MOCK:
    logger.warning("Using mock MCP implementation.")
    ClientSession = MockMCPClientSession
    StdioServerParameters = dict
    TcpServerParameters = dict
    stdio_client = mock_stdio_client

    async def tcp_client(host, port):
        logger.debug(f"MCP MOCK: Connecting TCP: {host}:{port}")
        return MockStdioContext()


# --- MCP Client Manager ---
class MCPClientManager:
    def __init__(self, config: List[MCPServerConfig]):
        self.config = config
        self._sessions: Dict[str, ClientSession] = {}
        self._contexts: Dict[str, Any] = {}  # Store connection contexts for cleanup
        self._locks: Dict[str, asyncio.Lock] = {}
        self._connection_tasks: Dict[str, asyncio.Task] = {}
        logger.info(f"MCPClientManager initialized with {len(config)} server configs.")

    async def _connect(self, server_name: str):
        if server_name not in self._locks: # Ensure lock exists before acquiring
            self._locks[server_name] = asyncio.Lock()

        async with self._locks[server_name]:
            if server_name in self._sessions:
                # Return existing session if it's already connected
                return self._sessions[server_name]

            server_conf = next((c for c in self.config if c.name == server_name), None)
            if not server_conf:
                raise ConfigurationError(f"MCP server config not found: {server_name}")

            logger.info(f"MCP connecting: {server_name} ({server_conf.connection_type})")
            try:
                session = None
                context = None

                if server_conf.connection_type == 'stdio':
                    if USE_MOCK:
                        # Mock implementation
                        params = StdioServerParameters(
                            command=server_conf.command,
                            args=server_conf.args,
                            env=server_conf.env
                        )
                        context = await stdio_client(params)
                        await context.__aenter__()
                        session = ClientSession()
                        await session.initialize()
                    else:
                        # Real implementation
                        params = StdioServerParameters(
                            command=server_conf.command,
                            args=server_conf.args or [],
                            env=server_conf.env or {}
                        )
                        context = stdio_client(params)
                        client, server = await context.__aenter__()
                        session = ClientSession(client)
                        await session.initialize()

                elif server_conf.connection_type == 'tcp':
                    if USE_MOCK:
                        # Mock implementation for TCP
                        context = await tcp_client(server_conf.host, server_conf.port)
                        await context.__aenter__()
                        session = ClientSession()
                        await session.initialize()
                    else:
                        # Real implementation for TCP
                        if not server_conf.host or not server_conf.port:
                            raise ConfigurationError(f"TCP connection requires host and port for {server_name}")
                        context = tcp_client(server_conf.host, server_conf.port)
                        client, server = await context.__aenter__()
                        session = ClientSession(client)
                        await session.initialize()
                else:
                    raise ConfigurationError(f"Unsupported MCP connection type: {server_conf.connection_type}")

                if session:
                    self._sessions[server_name] = session
                    self._contexts[server_name] = context  # Store context for cleanup
                    logger.info(f"MCP connected: {server_name}.")
                    # Remove completed connection task reference
                    if server_name in self._connection_tasks:
                        del self._connection_tasks[server_name]
                    return session
                else:
                    raise ConnectionError(f"MCP session creation failed for {server_name}")

            except Exception as e:
                logger.error(f"MCP connect failed for {server_name}: {e}", exc_info=True)
                if server_name in self._connection_tasks:
                    del self._connection_tasks[server_name]
                if server_name in self._sessions:
                    del self._sessions[server_name] # Clean up failed attempt
                if server_name in self._contexts:
                    try:
                        await self._contexts[server_name].__aexit__(None, None, None)
                    except Exception as exit_err:
                        logger.error(f"Error closing context during connection failure for {server_name}: {exit_err}")
                    del self._contexts[server_name]
                raise ConnectionError(f"MCP connection failed for {server_name}") from e

    async def get_session(self, server_name: str) -> ClientSession:
        if server_name in self._sessions:
             # Return existing session
             return self._sessions[server_name]

        if server_name not in self._locks:
             self._locks[server_name] = asyncio.Lock()

        # Check if a connection task is already running or recently completed/failed
        if server_name not in self._connection_tasks or self._connection_tasks[server_name].done():
             logger.debug(f"Creating/Retrying MCP connection task for: {server_name}")
             self._connection_tasks[server_name] = asyncio.create_task(self._connect(server_name))

        try:
            return await self._connection_tasks[server_name]
        except Exception as e:
             # The _connect method already logs details. Re-raise for caller.
             raise ConnectionError(f"Failed to get MCP session for {server_name}") from e

    async def call_tool(self, server_name: str, tool_name: str, params: dict) -> Any:
        try:
            session = await self.get_session(server_name)
            logger.info(f"MCP: Calling tool '{tool_name}' on '{server_name}' with params: {params}")
            result = await session.call_tool(tool_name, params)
            logger.debug(f"MCP: Result for '{tool_name}' from '{server_name}': {result}")
            # Extract content from result based on MCP response format
            return result.get("content") if isinstance(result, dict) else result
        except Exception as e:
            logger.error(f"MCP tool call failed for {server_name}.{tool_name}: {e}", exc_info=True)
            raise ActionFailedError(f"MCP tool call {server_name}.{tool_name} failed") from e

    async def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """List available tools on the specified MCP server."""
        try:
            session = await self.get_session(server_name)
            result = await session.list_tools()
            return result.get("tools", []) if isinstance(result, dict) else result
        except Exception as e:
            logger.error(f"MCP list_tools failed for {server_name}: {e}", exc_info=True)
            raise ActionFailedError(f"Failed to list tools for {server_name}") from e

    async def close_all(self):
        logger.info("Closing all MCP connections...")
        # Cancel any pending connection tasks first
        for name, task in list(self._connection_tasks.items()):
            if not task.done():
                task.cancel()
                try:
                    await task # Allow cancellation to process
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.error(f"Error cancelling MCP connect task {name}: {e}")
            del self._connection_tasks[name] # Remove reference

        # Close established sessions and contexts
        for name in list(self._sessions.keys()):
            try:
                # Close session first
                if name in self._sessions:
                    await self._sessions[name].close()
                    del self._sessions[name]

                # Then exit context
                if name in self._contexts:
                    await self._contexts[name].__aexit__(None, None, None)
                    del self._contexts[name]

                logger.info(f"Closed MCP connection: {name}")
            except Exception as e:
                logger.error(f"Error closing MCP connection {name}: {e}")
                # Continue with other connections even if one fails

        logger.info("MCP connections closed.")


# --- A2A Client Manager ---
class A2AClientManager:
    # (Keep the async A2AClientManager implementation from the previous step)
    def __init__(self, base_url: Optional[str] = None):
        self.http_client = httpx.AsyncClient(timeout=30.0, event_hooks={'response': [self._log_response]})
        self.remote_agents: Dict[str, AgentCard] = {} # URL -> AgentCard cache
        self.auth_tokens: Dict[str, Tuple[str, float]] = {} # URL -> (token, expiry_timestamp)
        logger.info("A2AClientManager initialized.")

    async def _log_response(self, response):
        # Helper to log response status for debugging
        await response.aread() # Ensure body is loaded for logging if needed later
        logger.debug(f"A2A Client HTTP Response: {response.status_code} {response.reason_phrase} - URL: {response.url}")

    async def authenticate(self, agent_url: str, agent_id: str, api_key: str) -> bool:
        """Authenticate with an A2A agent and store the token.

        Args:
            agent_url: URL of the agent
            agent_id: ID of the agent
            api_key: API key for the agent

        Returns:
            True if authentication succeeded, False otherwise
        """
        # Ensure URL has scheme
        if not agent_url.startswith(('http://', 'https://')):
             agent_url = f"http://{agent_url}" # Default to http

        # Normalize URL for consistency
        normalized_url = agent_url.rstrip('/')
        auth_url = f"{normalized_url}/auth/agent-token"

        try:
            logger.info(f"A2A Client: Authenticating with {normalized_url} as agent {agent_id}")

            # Send authentication request
            response = await self.http_client.post(
                auth_url,
                data={
                    "agent_id": agent_id,
                    "api_key": api_key
                }
            )
            response.raise_for_status()
            token_data = response.json()

            # Store token with expiry
            token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 1800)  # Default to 30 minutes
            expiry = time.time() + expires_in

            self.auth_tokens[normalized_url] = (token, expiry)
            logger.info(f"A2A Client: Successfully authenticated with {normalized_url}")
            return True

        except Exception as e:
            logger.error(f"A2A authentication failed for {agent_url}: {e}", exc_info=True)
            return False

    async def _get_auth_header(self, agent_url: str) -> Optional[Dict[str, str]]:
        """Get authentication header for an agent URL if available.

        Args:
            agent_url: URL of the agent

        Returns:
            Authentication header dict or None if not authenticated
        """
        # Normalize URL for consistency
        normalized_url = agent_url.rstrip('/')

        # Check if we have a token
        if normalized_url in self.auth_tokens:
            token, expiry = self.auth_tokens[normalized_url]

            # Check if token is expired
            if time.time() < expiry:
                return {"Authorization": f"Bearer {token}"}
            else:
                # Token expired, remove it
                del self.auth_tokens[normalized_url]
                logger.info(f"A2A Client: Token for {normalized_url} expired")

        return None

    async def discover_agent(self, agent_url: str) -> AgentCard:
        # Ensure URL has scheme
        if not agent_url.startswith(('http://', 'https://')):
             agent_url = f"http://{agent_url}" # Default to http

        # Normalize URL for cache key
        normalized_url = agent_url.rstrip('/')
        if normalized_url in self.remote_agents:
            return self.remote_agents[normalized_url]

        card_url = f"{normalized_url}/agent-card"
        try:
            logger.info(f"A2A Client: Discovering agent at {card_url}")
            response = await self.http_client.get(card_url)
            response.raise_for_status()
            card_data = response.json()
            card = AgentCard(**card_data)
            if not card.url: card.url = normalized_url # Populate if missing
            self.remote_agents[normalized_url] = card
            logger.info(f"A2A Client: Discovered agent '{card.name}' at {normalized_url}")
            return card
        except httpx.RequestError as e:
            logger.error(f"A2A discovery failed for {agent_url}: Network error {e}")
            raise ConnectionError(f"Cannot connect to A2A agent at {agent_url}") from e
        except Exception as e:
            logger.error(f"A2A discovery failed for {agent_url}: Invalid card or other error {e}", exc_info=True)
            raise APIAException(f"Failed to discover/parse agent card at {agent_url}") from e

    async def _send_json_rpc(self, target_url: str, method: str, params: Optional[dict] = None) -> dict:
        request_id = str(uuid.uuid4())
        # Use exclude_none=True to avoid sending null optional fields
        rpc_request = A2AJsonRpcRequest(id=request_id, method=method, params=params)
        request_payload = rpc_request.model_dump(by_alias=True, exclude_none=True)
        logger.debug(f"A2A Client Request: POST {target_url} | Method: {method} | Payload: {request_payload}")
        # Get authentication headers if available
        headers = await self._get_auth_header(target_url)

        try:
            response = await self.http_client.post(target_url, json=request_payload, headers=headers)
            # Logging is handled by hook now

            # Handle authentication errors
            if response.status_code == 401:
                logger.warning(f"Authentication failed for {target_url}. Token may have expired.")
                # Clear the token if it exists
                normalized_url = target_url.rstrip('/')
                if normalized_url in self.auth_tokens:
                    del self.auth_tokens[normalized_url]

            response.raise_for_status()
            rpc_response = response.json()

            if "error" in rpc_response:
                 error_data = rpc_response["error"]
                 # Try parsing into model for better structure if possible
                 try: error_obj = A2AJsonRpcErrorData(**error_data)
                 except Exception: error_obj = A2AJsonRpcErrorData(code=-32000, message=str(error_data))
                 logger.error(f"A2A RPC Error from {target_url} method {method}: {error_obj}")
                 raise A2AError(message=error_obj.message, code=error_obj.code, data=error_obj.data)
            elif "result" in rpc_response:
                 logger.debug(f"A2A Client Result: {rpc_response['result']}")
                 return rpc_response["result"]
            else:
                 logger.error(f"Invalid JSON-RPC response from {target_url}: {rpc_response}")
                 raise APIAException("Invalid JSON-RPC response received")

        except httpx.RequestError as e:
            logger.error(f"A2A RPC request failed for {target_url} method {method}: Network error {e}")
            raise ConnectionError(f"Network error during A2A request to {target_url}") from e
        except A2AError: raise # Re-raise A2A specific errors
        except Exception as e:
            logger.error(f"A2A RPC request failed for {target_url} method {method}: {e}", exc_info=True)
            raise APIAException(f"Generic error during A2A request to {target_url}") from e

    async def send_task(self, target_agent_url: str, params: A2ATaskSendParams, stream_callback: Optional[Callable] = None) -> A2ATask:
        target_url = target_agent_url.rstrip('/')
        # Normalize URL before discovery/sending
        if not target_url.startswith(('http://', 'https://')):
             target_url = f"http://{target_url}"

        card = await self.discover_agent(target_url)

        method = "tasks/send"
        use_streaming = False
        if stream_callback and card.capabilities.streaming:
             method = "tasks/sendSubscribe"
             use_streaming = True

        logger.info(f"A2A Client: Sending task {params.id} to {target_url} using method {method}")
        request_params = params.model_dump(exclude_none=True, by_alias=True)

        if not use_streaming:
            result_data = await self._send_json_rpc(target_url, method, request_params)
            return A2ATask(**result_data)
        else:
            # SSE Streaming Logic (as implemented previously)
            request_id = str(uuid.uuid4())
            rpc_request = A2AJsonRpcRequest(id=request_id, method=method, params=request_params)
            request_payload = rpc_request.model_dump(by_alias=True, exclude_none=True)
            last_known_task_state = None
            stream_exc = None

            try:
                async with self.http_client.stream("POST", target_url, json=request_payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            try:
                                data_str = line[len("data:"):].strip()
                                if not data_str: continue
                                event_data = json.loads(data_str)

                                if "error" in event_data:
                                    error_data = event_data["error"]
                                    try: error_obj = A2AJsonRpcErrorData(**error_data)
                                    except Exception: error_obj = A2AJsonRpcErrorData(code=-32000, message=str(error_data))
                                    logger.error(f"A2A SSE Error received: {error_obj}")
                                    stream_exc = A2AError(message=error_obj.message, code=error_obj.code, data=error_obj.data)
                                    if stream_callback: await stream_callback(stream_exc)
                                    # Decide if stream should stop on error
                                    break # Stop streaming on error for now

                                elif "result" in event_data:
                                    result = event_data["result"]
                                    event_obj = None
                                    try:
                                        if "status" in result and "final" in result:
                                            event_obj = A2ATaskStatusUpdateEventResult(**result)
                                            last_known_task_state = event_obj.status # Update last known state
                                        elif "artifact" in result:
                                            event_obj = A2ATaskArtifactUpdateEventResult(**result)
                                    except Exception as parse_exc:
                                         logger.warning(f"Failed to parse SSE result structure: {parse_exc} - Data: {result}")
                                         continue # Skip malformed event

                                    if event_obj and stream_callback:
                                         await stream_callback(event_obj)

                                    if isinstance(event_obj, A2ATaskStatusUpdateEventResult) and event_obj.final:
                                         logger.info(f"A2A SSE stream finished for task {params.id}")
                                         break # Exit loop
                            except json.JSONDecodeError: logger.warning(f"Failed to decode SSE data line: {line}")
                            except Exception as e:
                                 logger.error(f"Error processing SSE event: {e}", exc_info=True)
                                 stream_exc = e
                                 if stream_callback: await stream_callback(e)
                                 break # Stop streaming on processing error

            except httpx.RequestError as e:
                logger.error(f"A2A SSE request failed for {target_url}: Network error {e}")
                raise ConnectionError(f"Network error during A2A stream request to {target_url}") from e
            except Exception as e:
                logger.error(f"A2A SSE request failed for {target_url}: {e}", exc_info=True)
                raise APIAException(f"Error during A2A stream request to {target_url}") from e

            # After streaming, construct or fetch final Task object
            if stream_exc:
                # If stream ended due to error, reflect that
                raise APIAException("A2A stream ended with error") from stream_exc
            elif last_known_task_state:
                # Return a task with the last known state
                return A2ATask(id=params.id, sessionId=params.sessionId, status=last_known_task_state)
            else:
                # Stream might have ended without final state or error, fetch status
                logger.warning(f"A2A SSE stream for {params.id} ended without final state. Fetching.")
                try:
                    return await self.get_task(target_agent_url, params.id)
                except Exception as fetch_exc:
                     logger.error(f"Failed to fetch task status after incomplete stream for {params.id}: {fetch_exc}")
                     raise APIAException(f"Stream incomplete and failed to fetch final status for task {params.id}") from fetch_exc

    async def get_task(self, target_agent_url: str, task_id: str, history_length: int = 0) -> A2ATask:
        target_url = target_agent_url.rstrip('/')
        if not target_url.startswith(('http://', 'https://')): target_url = f"http://{target_url}"
        params = {"id": task_id, "historyLength": history_length}
        logger.info(f"A2A Client: Getting task {task_id} from {target_url}")
        result_data = await self._send_json_rpc(target_url, "tasks/get", params)
        return A2ATask(**result_data)

    async def cancel_task(self, target_agent_url: str, task_id: str) -> A2ATask:
        target_url = target_agent_url.rstrip('/')
        if not target_url.startswith(('http://', 'https://')): target_url = f"http://{target_url}"
        params = {"id": task_id}
        logger.info(f"A2A Client: Canceling task {task_id} on {target_url}")
        result_data = await self._send_json_rpc(target_url, "tasks/cancel", params)
        return A2ATask(**result_data)

    async def close(self):
        await self.http_client.aclose()
        logger.info("A2AClientManager HTTP client closed.")


# --- A2A Server Components ---

class A2ATaskRouter:
    # (Keep the async Router implementation with skill routing from the previous step)
    def __init__(self):
        self._handlers: Dict[str, Callable] = {} # skill_id -> async handler(context)
        self._default_handler: Optional[Callable] = None
        self._lock = asyncio.Lock()
        logger.info("A2ATaskRouter initialized.")

    async def register_handler(self, skill_id: str, handler: Callable):
        async with self._lock:
            if skill_id in self._handlers:
                logger.warning(f"Overwriting A2A handler for skill: {skill_id}")
            if not asyncio.iscoroutinefunction(handler):
                 logger.error(f"Attempted to register non-async function as A2A handler for skill '{skill_id}'. Handler NOT registered.")
                 return # Do not register non-async handlers
            self._handlers[skill_id] = handler
            logger.info(f"Registered A2A handler for skill: {skill_id}")

    async def register_default_handler(self, handler: Callable):
         async with self._lock:
            if not asyncio.iscoroutinefunction(handler):
                 logger.error("Attempted to register non-async function as default A2A handler. Handler NOT registered.")
                 return
            self._default_handler = handler
            logger.info("Registered default A2A handler.")

    async def get_handler(self, skill_id: Optional[str] = None) -> Optional[Callable]:
        """Gets a specific handler if skill_id matches, otherwise the default."""
        async with self._lock:
            if skill_id and skill_id in self._handlers:
                logger.debug(f"Router found specific handler for skill: {skill_id}")
                return self._handlers[skill_id]
            elif self._default_handler:
                logger.debug(f"Router falling back to default handler (skill requested: {skill_id}).")
                return self._default_handler
            else:
                logger.warning(f"Router has no specific handler for skill '{skill_id}' and no default handler.")
                return None

class A2ATaskContext:
    # (Keep the Context implementation with FilePart handling from the previous step)
    def __init__(self, task: A2ATask, update_queue: Optional[asyncio.Queue] = None):
        self.task = task
        self._update_queue = update_queue

    @property
    def task_id(self) -> str: return self.task.id
    @property
    def session_id(self) -> Optional[str]: return self.task.sessionId
    @property
    def incoming_message(self) -> Optional[A2AMessage]:
        return self.task.history[-1] if self.task.history else None
    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        msg = self.incoming_message
        return msg.metadata if msg else None

    def get_text_parts(self) -> List[str]:
        texts = []
        msg = self.incoming_message
        if msg:
            for part in msg.parts:
                if isinstance(part, A2ATextPart): texts.append(part.text)
        return texts

    def get_file_parts(self) -> List[A2AFilePart]:
        files = []
        msg = self.incoming_message
        if msg:
            for part in msg.parts:
                if isinstance(part, A2AFilePart): files.append(part)
        return files

    async def process_file_part(self, file_part: A2AFilePart, max_size_bytes: int = 10 * 1024 * 1024) -> bytes:
        """Process a file part and return the binary data.

        Args:
            file_part: The A2AFilePart to process
            max_size_bytes: Maximum allowed file size in bytes (default: 10MB)

        Returns:
            The decoded file content as bytes

        Raises:
            ValueError: If the file part is invalid or too large
            NotImplementedError: If URI fetching is requested but not implemented
        """
        # We trust the type annotation, but could add runtime check if needed
        # This is unreachable due to the type annotation, but kept for documentation
        # if not isinstance(file_part, A2AFilePart):
        #     raise ValueError(f"Expected A2AFilePart, got {type(file_part).__name__}")

        # Log file information
        logger.info(f"Processing file part: Name={file_part.file.name}, Mime={file_part.file.mimeType}, HasBytes={bool(file_part.file.bytes)}, URI={file_part.file.uri}")

        # Process based on content source
        if file_part.file.bytes:
            try:
                # Validate base64 format
                if not isinstance(file_part.file.bytes, str):
                    raise ValueError(f"Base64 bytes must be a string, got {type(file_part.file.bytes).__name__}")

                # Check if the string looks like base64 (rough check)
                if len(file_part.file.bytes) % 4 != 0 or not all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in file_part.file.bytes):
                    raise ValueError("Invalid base64 format: contains invalid characters or incorrect padding")

                # Decode the base64 data
                file_bytes = base64.b64decode(file_part.file.bytes)

                # Check file size
                if len(file_bytes) > max_size_bytes:
                    raise ValueError(f"File size ({len(file_bytes)} bytes) exceeds maximum allowed size ({max_size_bytes} bytes)")

                # Validate MIME type if provided
                if file_part.file.mimeType:
                    # Basic MIME type validation could be expanded
                    if not isinstance(file_part.file.mimeType, str) or '/' not in file_part.file.mimeType:
                        logger.warning(f"Invalid MIME type format: {file_part.file.mimeType}")

                return file_bytes
            except Exception as e:
                logger.error(f"Failed to decode base64 bytes for file {file_part.file.name}: {e}")
                raise ValueError(f"Invalid base64 data for file {file_part.file.name}: {str(e)}") from e
        elif file_part.file.uri:
            # Validate URI
            if not isinstance(file_part.file.uri, str):
                raise ValueError(f"URI must be a string, got {type(file_part.file.uri).__name__}")

            if not file_part.file.uri.startswith(("http://", "https://")):
                raise ValueError(f"URI must start with http:// or https://, got: {file_part.file.uri}")

            logger.warning(f"Fetching from URI ({file_part.file.uri}) is not securely implemented.")
            # --- Placeholder for secure implementation ---
            # Example using httpx (requires client instance)
            # async with httpx.AsyncClient() as client:
            #    response = await client.get(file_part.file.uri, timeout=30.0)
            #    response.raise_for_status()
            #    content = response.content
            #
            #    # Check file size
            #    if len(content) > max_size_bytes:
            #        raise ValueError(f"File size ({len(content)} bytes) exceeds maximum allowed size ({max_size_bytes} bytes)")
            #
            #    return content
            raise NotImplementedError("Secure URI fetching for file parts is not implemented.")
        else:
            raise ValueError("File part has neither bytes nor URI.")

    def get_data_parts(self) -> List[Dict[str, Any]]:
        """Extract data from all data parts in the incoming message."""
        data_parts = []
        msg = self.incoming_message
        if msg:
            for part in msg.parts:
                if isinstance(part, A2ADataPart):
                    data_parts.append(part.data)
        return data_parts

    async def update_status(self, state: str, message_text: Optional[str] = None, final: bool = False):
        if not self._update_queue:
            logger.warning(f"Streaming update ignored for task {self.task_id}: No update queue.")
            return

        status_message = A2AMessage(role="agent", parts=[A2ATextPart(text=message_text)]) if message_text else None
        status = A2ATaskState(state=state, message=status_message)
        update_event = A2ATaskStatusUpdateEventResult(id=self.task_id, status=status, final=final)
        await self._update_queue.put(update_event)
        logger.debug(f"A2A Task {self.task_id}: Sent status update '{state}' (Final={final})")

    async def yield_artifact(self, artifact: A2AArtifact):
        if not self._update_queue:
            logger.warning(f"Streaming artifact ignored for task {self.task_id}: No update queue.")
            return

        update_event = A2ATaskArtifactUpdateEventResult(id=self.task_id, artifact=artifact)
        await self._update_queue.put(update_event)
        logger.debug(f"A2A Task {self.task_id}: Sent artifact (index {artifact.index})")

class A2ATaskResult:
    # (Keep the Result implementation from the previous step)
    def __init__(self, status: str = "completed", message: Optional[A2AMessage] = None, artifacts: Optional[List[A2AArtifact]] = None):
        self.final_status = A2ATaskState(state=status, message=message)
        self.artifacts = artifacts or []


class A2ATaskManager:
    """Manages A2A tasks, including routing, execution, and lifecycle management."""
    def __init__(self, knowledge_base: APIA_KnowledgeBase, task_router: A2ATaskRouter):
        self._tasks: Dict[str, A2ATask] = {} # In-memory task store
        self._task_locks: Dict[str, asyncio.Lock] = {}
        self._streaming_queues: Dict[str, asyncio.Queue] = {} # task_id -> queue
        self._global_lock = asyncio.Lock() # Protects _tasks, _task_locks, _streaming_queues dicts
        self.kb = knowledge_base
        self.router = task_router
        self.a2a_dlq: List[Tuple[str, str, str]] = [] # task_id, method, reason

        # Task cleanup configuration
        self._cleanup_interval_seconds = 3600  # Run cleanup every hour
        self._task_max_age_seconds = 86400  # Keep tasks for 24 hours
        self._cleanup_task: Optional[asyncio.Task] = None
        self._stop_cleanup = asyncio.Event()

        # Start the cleanup task
        try:
            self._cleanup_task = asyncio.create_task(self._run_periodic_cleanup())
            logger.info("A2ATaskManager initialized with periodic cleanup.")
        except RuntimeError:
            logger.warning("Could not start cleanup task during init (event loop might not be running).")
            logger.info("A2ATaskManager initialized without cleanup task.")

    async def _get_task_lock(self, task_id: str) -> asyncio.Lock:
        async with self._global_lock:
            if task_id not in self._task_locks:
                self._task_locks[task_id] = asyncio.Lock()
            return self._task_locks[task_id]

    async def _update_task_state(self, task_id: str, status: Optional[A2ATaskState] = None, history_append: Optional[A2AMessage] = None, artifacts: Optional[List[A2AArtifact]] = None, replace_artifacts: bool = False):
        """Safely updates the task object in the store."""
        # Does not need task lock itself, assumes caller holds it
        if task_id not in self._tasks:
            logger.error(f"Attempted to update non-existent task {task_id}")
            return # Or raise?

        task = self._tasks[task_id]
        if status:
            task.status = status
            task.status.timestamp = datetime.now() # Update timestamp on status change
        if history_append:
            task.history = (task.history or []) + [history_append]
        if artifacts is not None or replace_artifacts:
            task.artifacts = artifacts if artifacts is not None else [] # Replace/clear
        # No need to reassign task to self._tasks[task_id] as it's mutated in place

    async def _add_to_dlq(self, task_id: Optional[str], method: str, reason: str):
         async with self._global_lock:
              tid = task_id or "unknown"
              self.a2a_dlq.append((tid, method, reason))
              dlq_count = len(self.a2a_dlq)
              # Update metric without await if KB update itself handles locking
              await self.kb.update_metric("a2a_tasks", "dlq_count", dlq_count)
              logger.error(f"A2A Task {tid} (Method: {method}) sent to DLQ: {reason}. DLQ size: {dlq_count}")

    async def _get_handler_for_task(self, params: A2ATaskSendParams) -> Callable:
        """Determines the handler based on skill ID."""
        skill_id = params.message.metadata.get("skill_id") if params.message and params.message.metadata else None
        handler = await self.router.get_handler(skill_id=skill_id)
        if not handler:
            logger.error(f"No A2A handler found for task {params.id} (Skill ID: {skill_id})")
            await self._add_to_dlq(params.id, "tasks/send", f"No suitable handler found (Skill ID: {skill_id})")
            raise A2AError(f"No suitable agent handler found for skill '{skill_id}'", code=-32601)
        return handler

    # --- A2A Method Implementations ---
    async def _validate_task_params(self, params: A2ATaskSendParams) -> None:
        """Validate task parameters before processing.

        Args:
            params: The task parameters to validate

        Raises:
            A2AError: If the parameters are invalid
        """
        # Check for required message parts
        if not params.message or not params.message.parts:
            raise A2AError("Task message must contain at least one part", code=-32602)

        # Check for skill_id in metadata
        if not params.message.metadata or "skill_id" not in params.message.metadata:
            logger.warning(f"Missing skill_id in task metadata for task {params.id}")
            # Not raising an error, just logging a warning

        # Validate message parts
        for part in params.message.parts:
            if isinstance(part, A2AFilePart):
                # Check if file has either bytes or URI
                if not part.file.bytes and not part.file.uri:
                    raise A2AError(f"File part must have either bytes or URI", code=-32602)

                # Check MIME type if provided
                if part.file.mimeType and not isinstance(part.file.mimeType, str):
                    raise A2AError(f"Invalid MIME type: must be a string", code=-32602)

                # Check URI format if provided
                if part.file.uri and not part.file.uri.startswith(("http://", "https://")):
                    raise A2AError(f"Invalid URI format: must start with http:// or https://", code=-32602)

            elif isinstance(part, A2ATextPart):
                # Check text content
                if not part.text or not isinstance(part.text, str):
                    raise A2AError(f"Text part must contain non-empty text", code=-32602)

            elif isinstance(part, A2ADataPart):
                # Check data content
                if not part.data or not isinstance(part.data, dict):
                    raise A2AError(f"Data part must contain non-empty dictionary", code=-32602)

    async def handle_task_send(self, params: A2ATaskSendParams) -> A2ATask:
        # Validate task parameters
        await self._validate_task_params(params)

        task_id = params.id
        session_id = params.sessionId or str(uuid.uuid4())
        handler = await self._get_handler_for_task(params) # Use helper

        async with await self._get_task_lock(task_id):
             if task_id in self._tasks:
                 task = self._tasks[task_id]
                 if task.status.state not in ["input-required", "completed", "working", "submitted", "canceled"]:
                     logger.warning(f"Task {task_id} cannot receive message in state: {task.status.state}")
                     raise A2AError(f"Task {task_id} in invalid state {task.status.state}", code=-32004)
                 task.history = (task.history or []) + [params.message]
                 task.sessionId = session_id
                 task.status = A2ATaskState(state="working") # Mark as working
                 # Do not replace artifacts on simple send, allow accumulation? Or clear? Depends. Let's keep old ones.
                 self._update_task_state(task_id, status=task.status, history_append=None, replace_artifacts=False)
             else:
                 task = A2ATask(
                     id=task_id, sessionId=session_id,
                     status=A2ATaskState(state="working"),
                     history=[params.message], metadata=params.metadata
                 )
                 self._tasks[task_id] = task
                 await self.kb.update_metric("a2a_tasks", "received", await self.kb.get_metric("a2a_tasks", "received", 0) + 1)

             task_copy = task.model_copy(deep=True) # Pass copy to handler

        # Execute handler outside lock
        try:
            context = A2ATaskContext(task=task_copy)
            result: A2ATaskResult = await handler(context)
            # Update state inside lock
            async with await self._get_task_lock(task_id):
                 self._update_task_state(task_id, status=result.final_status, artifacts=result.artifacts, replace_artifacts=True) # Replace artifacts with final result
                 if result.final_status.state == "completed": await self.kb.update_metric("a2a_tasks", "completed", await self.kb.get_metric("a2a_tasks", "completed", 0) + 1)
                 elif result.final_status.state == "failed":
                     await self.kb.update_metric("a2a_tasks", "failed", await self.kb.get_metric("a2a_tasks", "failed", 0) + 1)
                     await self._add_to_dlq(task_id, "tasks/send", f"Handler failed: {result.final_status.message}")
        except Exception as e:
            logger.error(f"Error executing A2A handler for task {task_id}: {e}", exc_info=True)
            error_message = A2AMessage(role="agent", parts=[A2ATextPart(text=f"Internal error: {e}")])
            failed_status = A2ATaskState(state="failed", message=error_message)
            async with await self._get_task_lock(task_id): # Lock to update state
                 self._update_task_state(task_id, status=failed_status, replace_artifacts=True) # Clear artifacts on handler crash
                 await self.kb.update_metric("a2a_tasks", "failed", await self.kb.get_metric("a2a_tasks", "failed", 0) + 1)
                 await self._add_to_dlq(task_id, "tasks/send", f"Handler exception: {e}")

        # Return final task state after potential update
        async with await self._get_task_lock(task_id):
            return self._tasks[task_id].model_copy(deep=True)

    async def handle_task_send_subscribe(self, params: A2ATaskSendParams, update_queue: asyncio.Queue):
        """Handles tasks/sendSubscribe background execution and streaming."""
        # Validate task parameters
        await self._validate_task_params(params)

        task_id = params.id
        session_id = params.sessionId or str(uuid.uuid4())
        handler = await self._get_handler_for_task(params) # Use helper

        task_lock = await self._get_task_lock(task_id)
        async with task_lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                if task.status.state not in ["input-required", "completed", "working", "submitted", "canceled"]:
                    await update_queue.put(A2AError(f"Task in invalid state {task.status.state}", code=-32004))
                    return
                task.history = (task.history or []) + [params.message]
                task.sessionId = session_id
                task.status = A2ATaskState(state="working")
                self._update_task_state(task_id, status=task.status, history_append=None, replace_artifacts=False) # Keep old artifacts for now
            else:
                task = A2ATask(
                    id=task_id, sessionId=session_id,
                    status=A2ATaskState(state="working"),
                    history=[params.message], metadata=params.metadata
                )
                self._tasks[task_id] = task
                await self.kb.update_metric("a2a_tasks", "received", await self.kb.get_metric("a2a_tasks", "received", 0) + 1)
            task_copy = task.model_copy(deep=True)

        # Execute handler outside initial lock, but acquire it for final update
        final_status = None
        final_artifacts = None
        try:
            context = A2ATaskContext(task=task_copy, update_queue=update_queue)
            # Initial working status update
            await context.update_status("working", message_text="Task submitted for processing...")
            result: A2ATaskResult = await handler(context)
            final_status = result.final_status
            final_artifacts = result.artifacts
            # Send final status update via queue
            await context.update_status(final_status.state, message_text=final_status.message.parts[0].text if final_status.message else None, final=True)
        except Exception as e:
            logger.error(f"Error executing streaming A2A handler for task {task_id}: {e}", exc_info=True)
            error_message = A2AMessage(role="agent", parts=[A2ATextPart(text=f"Internal error: {e}")])
            final_status = A2ATaskState(state="failed", message=error_message)
            # Send final error status update via queue
            try:
                await context.update_status(final_status.state, message_text=error_message.parts[0].text, final=True)
            except Exception as q_err: # Catch errors putting final error status to queue
                 logger.error(f"Failed to send final error status update to queue for task {task_id}: {q_err}")
            await self._add_to_dlq(task_id, "tasks/sendSubscribe", f"Handler exception: {e}")
        finally:
             # Update task state in manager *after* streaming finishes/fails
             if final_status: # Ensure we have a final status
                 async with task_lock: # Acquire lock for final update
                     self._update_task_state(task_id, status=final_status, artifacts=final_artifacts, replace_artifacts=True)
                     metric_category = "completed" if final_status.state == "completed" else "failed"
                     if metric_category == "failed": await self._add_to_dlq(task_id, "tasks/sendSubscribe", f"Stream handler failed: {final_status.message}")
                     await self.kb.update_metric("a2a_tasks", metric_category, await self.kb.get_metric("a2a_tasks", metric_category, 0) + 1)


    async def handle_task_get(self, task_id: str, history_length: int) -> A2ATask:
        async with await self._get_task_lock(task_id):
            task = self._tasks.get(task_id)
            if not task:
                raise A2AError(f"Task {task_id} not found", code=-32001)
            task_copy = task.model_copy(deep=True)
            if history_length >= 0 and task_copy.history:
                task_copy.history = task_copy.history[-history_length:]
            elif history_length == 0:
                task_copy.history = []
            return task_copy

    async def handle_task_cancel(self, task_id: str) -> A2ATask:
         async with await self._get_task_lock(task_id):
            task = self._tasks.get(task_id)
            if not task:
                raise A2AError(f"Task {task_id} not found", code=-32001)
            if task.status.state in ["completed", "failed", "canceled"]:
                 logger.warning(f"Task {task_id} cannot be canceled, state: {task.status.state}")
                 # Return current state
            else:
                 logger.info(f"Canceling A2A Task {task_id}")
                 canceled_status = A2ATaskState(state="canceled")
                 # TODO: Signal cancellation to the running handler task if possible
                 self._update_task_state(task_id, status=canceled_status, replace_artifacts=True) # Clear artifacts on cancel?
                 # Update metric?
                 await self.kb.update_metric("a2a_tasks", "canceled", await self.kb.get_metric("a2a_tasks", "canceled", 0) + 1)

            return self._tasks[task_id].model_copy(deep=True)

    async def _add_to_dlq(self, task_id: str, method: str, reason: str):
        """Add a task to the dead letter queue."""
        self.a2a_dlq.append((task_id, method, reason))
        logger.warning(f"A2A DLQ: {method} task {task_id} - {reason}")
        # Could also persist to KB or external store

    async def _run_periodic_cleanup(self):
        """Periodically clean up old tasks to prevent memory leaks."""
        logger.info("Starting periodic task cleanup")
        while not self._stop_cleanup.is_set():
            try:
                # Wait for the cleanup interval
                await asyncio.wait_for(
                    self._stop_cleanup.wait(),
                    timeout=self._cleanup_interval_seconds
                )
                # If we get here because _stop_cleanup was set, break the loop
                if self._stop_cleanup.is_set():
                    break
            except asyncio.TimeoutError:
                # Timeout means it's time to run cleanup
                try:
                    await self._cleanup_old_tasks()
                except Exception as e:
                    logger.error(f"Error during task cleanup: {e}", exc_info=True)

        logger.info("Periodic task cleanup stopped")

    async def _cleanup_old_tasks(self):
        """Clean up tasks that are completed, failed, or canceled and older than max_age_seconds."""
        now = datetime.now()
        tasks_to_remove = []

        # First pass: identify tasks to remove under the global lock
        async with self._global_lock:
            for task_id, task in list(self._tasks.items()):
                # Check if task is in a terminal state
                if task.status.state in ["completed", "failed", "canceled"]:
                    # Calculate age based on last status update timestamp
                    if task.status.timestamp:
                        age_seconds = (now - task.status.timestamp).total_seconds()
                        if age_seconds > self._task_max_age_seconds:
                            tasks_to_remove.append(task_id)
                    else:
                        # If no timestamp, use a conservative approach based on task creation
                        created_at = task.createdAt if hasattr(task, 'createdAt') else None
                        if created_at:
                            age_seconds = (now - created_at).total_seconds()
                            if age_seconds > self._task_max_age_seconds:
                                tasks_to_remove.append(task_id)

            logger.info(f"Task cleanup: identified {len(tasks_to_remove)} tasks to remove")

        # Second pass: remove tasks one by one with individual locks
        for task_id in tasks_to_remove:
            try:
                await self._remove_task(task_id)
            except Exception as e:
                logger.error(f"Error removing task {task_id} during cleanup: {e}")

    async def _remove_task(self, task_id: str):
        """Remove a task and its associated resources."""
        async with await self._get_task_lock(task_id):
            # Remove the task from the tasks dictionary
            if task_id in self._tasks:
                del self._tasks[task_id]

            # Clean up the streaming queue if it exists
            async with self._global_lock:
                if task_id in self._streaming_queues:
                    # Close the queue
                    self._streaming_queues[task_id].put_nowait(None)  # Signal end of stream
                    del self._streaming_queues[task_id]

        # Remove the task lock
        async with self._global_lock:
            if task_id in self._task_locks:
                del self._task_locks[task_id]

        logger.debug(f"Removed task {task_id} and its resources")

    async def stop_cleanup(self):
        """Stop the periodic cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._stop_cleanup.set()
            try:
                await self._cleanup_task
                logger.info("Task cleanup stopped gracefully")
            except Exception as e:
                logger.error(f"Error stopping task cleanup: {e}")
                if not self._cleanup_task.done():
                    self._cleanup_task.cancel()
                    try:
                        await self._cleanup_task
                    except asyncio.CancelledError:
                        logger.info("Task cleanup cancelled")
            self._cleanup_task = None
