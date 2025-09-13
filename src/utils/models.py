# models.py
import uuid
import base64 # Added for FilePart handling
import re
from datetime import datetime
from typing import Optional, Dict, List, Any, Union, Literal
from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator, ConfigDict

# --- MCP Related (Placeholders/Examples) ---
class MCPToolInfo(BaseModel):
    name: str
    description: Optional[str] = None

class MCPResourceInfo(BaseModel):
    uri: str
    name: Optional[str] = None

# --- A2A Data Models (Based on Spec) ---
class A2APartMetadata(BaseModel):
    mimeType: Optional[str] = None
    schema_val: Optional[Dict[str, Any]] = Field(None, alias="schema") # Handle 'schema' keyword

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid"  # Prevent extra fields
    )

    @field_validator('mimeType')
    @classmethod
    def validate_mime_type(cls, v):
        if v is not None and not re.match(r'^[\w-]+/[\w\.-]+(?:\+[\w-]+)?$', v):
            raise ValueError(f"Invalid MIME type format: {v}")
        return v

class A2ATextPart(BaseModel):
    type: Literal["text"] = "text"  # Must be "text"
    text: str = Field(..., min_length=1)  # Require non-empty text
    metadata: Optional[A2APartMetadata] = None

    model_config = ConfigDict(extra="forbid")  # Prevent extra fields

class A2AFile(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    mimeType: Optional[str] = None
    bytes: Optional[str] = None  # base64 encoded
    uri: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode='after')
    def validate_file_content(self):
        if self.bytes is None and self.uri is None:
            raise ValueError("Either 'bytes' or 'uri' must be provided")

        if self.bytes is not None:
            try:
                # Validate that bytes is valid base64
                base64.b64decode(self.bytes)
            except Exception:
                raise ValueError("Invalid base64 encoding in 'bytes' field")

        if self.uri is not None and not (self.uri.startswith('http://') or self.uri.startswith('https://')):
            raise ValueError("URI must start with 'http://' or 'https://'")

        return self

    @field_validator('mimeType')
    @classmethod
    def validate_mime_type(cls, v):
        if v is not None and not re.match(r'^[\w-]+/[\w\.-]+(?:\+[\w-]+)?$', v):
            raise ValueError(f"Invalid MIME type format: {v}")
        return v

class A2AFilePart(BaseModel):
    type: Literal["file"] = "file"  # Must be "file"
    file: A2AFile
    metadata: Optional[A2APartMetadata] = None

    model_config = ConfigDict(extra="forbid")

class A2ADataPart(BaseModel):
    type: Literal["data"] = "data"  # Must be "data"
    data: Dict[str, Any] = Field(..., min_length=1)  # Require non-empty data
    metadata: Optional[A2APartMetadata] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator('data')
    @classmethod
    def validate_data_not_empty(cls, v):
        if not v:
            raise ValueError("Data dictionary cannot be empty")
        return v

A2APart = Union[A2ATextPart, A2AFilePart, A2ADataPart]

class A2AMessage(BaseModel):
    role: Literal["user", "agent"] = Field(...)  # Must be "user" or "agent"
    parts: List[A2APart] = Field(..., min_length=1)  # Require at least one part
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator('parts')
    @classmethod
    def validate_parts_not_empty(cls, v):
        if not v:
            raise ValueError("Message must contain at least one part")
        return v

class A2AArtifact(BaseModel):
    name: Optional[str] = Field(None, min_length=1)  # If provided, must be non-empty
    description: Optional[str] = None
    parts: List[A2APart] = Field(..., min_length=1)  # Require at least one part
    metadata: Optional[Dict[str, Any]] = None
    index: int = Field(0, ge=0)  # Must be non-negative
    append: Optional[bool] = False
    lastChunk: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator('parts')
    @classmethod
    def validate_parts_not_empty(cls, v):
        if not v:
            raise ValueError("Artifact must contain at least one part")
        return v

class A2ATaskState(BaseModel):
    state: Literal[
        "submitted", "working", "input-required",
        "completed", "canceled", "failed", "unknown"
    ] = Field(...)  # Must be one of the valid states
    message: Optional[A2AMessage] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(extra="forbid")

class A2ATask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), min_length=1)
    sessionId: Optional[str] = Field(None, min_length=1)  # If provided, must be non-empty
    status: A2ATaskState = Field(default_factory=lambda: A2ATaskState(state="submitted"))
    history: List[A2AMessage] = Field(default_factory=list)  # Default to empty list
    artifacts: List[A2AArtifact] = Field(default_factory=list)  # Default to empty list
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator('id')
    @classmethod
    def validate_id_format(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Task ID must be a non-empty string")
        return v

class A2ATaskSendParams(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), min_length=1)
    sessionId: Optional[str] = Field(None, min_length=1)  # If provided, must be non-empty
    message: A2AMessage
    acceptedOutputModes: List[str] = Field(
        default=["text/plain", "application/json"],
        min_length=1  # Require at least one output mode
    )
    historyLength: Optional[int] = Field(0, ge=0)  # Must be non-negative if provided
    # pushNotification: Optional[PushNotificationConfig] # Skipping
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        extra="allow"  # Allow extra fields like skill_id temporarily if needed
    )

    @field_validator('id')
    @classmethod
    def validate_id_format(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Task ID must be a non-empty string")
        return v

    @field_validator('metadata')
    @classmethod
    def validate_metadata(cls, v):
        if v is not None and 'skill_id' not in v:
            # Not raising an error, but logging a warning would be good here
            # We can't log directly from a validator, so we'll handle this in the router
            pass
        return v

class A2ATaskStatusUpdateEventResult(BaseModel):
    id: str = Field(..., min_length=1)  # Require non-empty ID
    status: A2ATaskState
    final: bool = False
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="forbid")

class A2ATaskArtifactUpdateEventResult(BaseModel):
    id: str = Field(..., min_length=1)  # Require non-empty ID
    artifact: A2AArtifact
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="forbid")

A2ATaskUpdateEventResult = Union[A2ATaskStatusUpdateEventResult, A2ATaskArtifactUpdateEventResult]

class A2AJsonRpcRequest(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"  # Must be "2.0"
    id: Union[str, int] = Field(..., description="Request identifier")
    method: str = Field(..., min_length=1)  # Require non-empty method
    params: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator('method')
    @classmethod
    def validate_method(cls, v):
        valid_methods = ["tasks/send", "tasks/sendSubscribe", "tasks/get", "tasks/cancel"]
        if v not in valid_methods:
            raise ValueError(f"Method must be one of: {', '.join(valid_methods)}")
        return v

class A2AJsonRpcSuccessResponse(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"  # Must be "2.0"
    id: Union[str, int] = Field(..., description="Request identifier")
    result: Any

    model_config = ConfigDict(extra="forbid")

class A2AJsonRpcErrorData(BaseModel):
    code: int
    message: str = Field(..., min_length=1)  # Require non-empty message
    data: Optional[Any] = None

    model_config = ConfigDict(extra="forbid")

class A2AJsonRpcErrorResponse(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"  # Must be "2.0"
    id: Union[str, int, None]
    error: A2AJsonRpcErrorData

    model_config = ConfigDict(extra="forbid")

# Agent Card Models
class A2AAgentProvider(BaseModel):
    organization: str = Field(..., min_length=1)  # Require non-empty organization
    url: HttpUrl

    model_config = ConfigDict(extra="forbid")

class A2AAgentCapabilities(BaseModel):
    streaming: bool = False
    pushNotifications: bool = False
    stateTransitionHistory: bool = False

    model_config = ConfigDict(extra="forbid")

class A2AAgentAuthentication(BaseModel):
    schemes: List[str] = Field(default=["None"], min_length=1)  # Require at least one scheme
    credentials: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

class A2AAgentSkill(BaseModel):
    id: str = Field(..., min_length=1)  # Require non-empty ID
    name: str = Field(..., min_length=1)  # Require non-empty name
    description: str = Field(..., min_length=1)  # Require non-empty description
    tags: List[str] = Field(default_factory=list)  # Default to empty list
    examples: List[str] = Field(default_factory=list)  # Default to empty list
    inputModes: Optional[List[str]] = None
    outputModes: Optional[List[str]] = None

    model_config = ConfigDict(extra="forbid")

class AgentCard(BaseModel):
    name: str = Field(..., min_length=1)  # Require non-empty name
    description: str = Field(..., min_length=1)  # Require non-empty description
    url: HttpUrl
    provider: Optional[A2AAgentProvider] = None
    version: str = Field("0.1.0", pattern=r'^\d+\.\d+\.\d+$')  # Semantic versioning format
    documentationUrl: Optional[HttpUrl] = None
    capabilities: A2AAgentCapabilities = Field(default_factory=A2AAgentCapabilities)
    authentication: A2AAgentAuthentication = Field(default_factory=A2AAgentAuthentication)
    defaultInputModes: List[str] = Field(
        default=["text/plain", "application/json"],
        min_length=1  # Require at least one input mode
    )
    defaultOutputModes: List[str] = Field(
        default=["text/plain", "application/json"],
        min_length=1  # Require at least one output mode
    )
    skills: List[A2AAgentSkill] = Field(default_factory=list)  # Default to empty list

    model_config = ConfigDict(extra="forbid")
