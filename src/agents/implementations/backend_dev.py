# agents/implemtations/backend_dev.py
import asyncio
import logging
import random
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from core.framework import APIA_BaseAgent
from utils.protocols import A2ATaskContext, A2ATaskResult
from utils.models import A2AArtifact, A2ATextPart, A2ADataPart, A2AMessage
from utils.memory import AgentMemory
from agents.specialized import APIA_SpecializedAgent

logger = logging.getLogger(__name__)

class APIA_BackendDevelopmentAgent(APIA_SpecializedAgent):
    """
    Backend Development Agent for creating APIs and implementing business logic.

    This agent specializes in backend development tasks such as:
    - Creating API endpoints
    - Implementing business logic
    - Handling data validation
    - Setting up authentication and authorization
    """

    async def _initialize_domain_resources(self):
        """Initialize backend development resources."""
        # Initialize API patterns
        self._api_patterns = {
            "rest": {
                "get": "def get_{resource}(...):\n    \"\"\"Get {resource} endpoint.\"\"\"\n    # Implementation\n    return response",
                "post": "def create_{resource}(...):\n    \"\"\"Create {resource} endpoint.\"\"\"\n    # Implementation\n    return response",
                "put": "def update_{resource}(...):\n    \"\"\"Update {resource} endpoint.\"\"\"\n    # Implementation\n    return response",
                "delete": "def delete_{resource}(...):\n    \"\"\"Delete {resource} endpoint.\"\"\"\n    # Implementation\n    return response"
            },
            "graphql": {
                "query": "type Query {\n    {resource}(id: ID!): {Resource}\n    {resources}: [{Resource}]\n}",
                "mutation": "type Mutation {\n    create{Resource}(input: {Resource}Input!): {Resource}\n    update{Resource}(id: ID!, input: {Resource}Input!): {Resource}\n    delete{Resource}(id: ID!): Boolean\n}"
            }
        }

        # Initialize supported frameworks
        self._supported_frameworks = ["fastapi", "flask", "django", "express"]

        logger.info(f"Backend Development Agent ({self.id}) initialized domain resources")

    async def _register_skills(self):
        """Register backend development skills."""
        await super()._register_skills()

        # Register backend-specific skills
        self._skill_registry.update({
            "create_api_endpoint": {
                "name": "Create API Endpoint",
                "description": "Create a new API endpoint with the specified functionality",
                "examples": [
                    "Create a REST API endpoint for user authentication",
                    "Implement a GraphQL query for product data"
                ]
            },
            "implement_business_logic": {
                "name": "Implement Business Logic",
                "description": "Implement business logic for a specific feature or requirement",
                "examples": [
                    "Implement the order processing workflow",
                    "Create the user registration business logic"
                ]
            },
            "setup_authentication": {
                "name": "Setup Authentication",
                "description": "Set up authentication and authorization for an API",
                "examples": [
                    "Implement JWT authentication for the API",
                    "Set up role-based access control"
                ]
            }
        })

    async def _handle_domain_task(self, context: A2ATaskContext, subtask_id: str,
                                 subtask_description: str) -> A2ATaskResult:
        """
        Handle backend development tasks.

        Args:
            context: Task context
            subtask_id: ID of the subtask
            subtask_description: Description of the subtask

        Returns:
            Task result with generated code and documentation
        """
        # Analyze the task to determine what needs to be created
        task_analysis = self._analyze_backend_task(subtask_description)

        # Determine the appropriate framework and patterns
        framework = self._determine_framework(context, task_analysis)

        # Generate the API code
        api_code = await self._generate_api_code(task_analysis, framework)

        # Generate documentation
        documentation = self._generate_documentation(task_analysis, api_code)

        # Simulate work time
        await asyncio.sleep(random.uniform(1.0, 2.0))

        # Return the results
        return A2ATaskResult(
            status="completed",
            message=A2AMessage(
                role="agent",
                parts=[A2ATextPart(text=f"Backend development task completed: {subtask_description}")]
            ),
            artifacts=[
                A2AArtifact(
                    name=f"api_code_{subtask_id}",
                    description="Generated API Code",
                    parts=[
                        A2ATextPart(text=api_code)
                    ]
                ),
                A2AArtifact(
                    name=f"api_docs_{subtask_id}",
                    description="API Documentation",
                    parts=[
                        A2ATextPart(text=documentation)
                    ]
                )
            ]
        )

    def _analyze_backend_task(self, task_description: str) -> Dict[str, Any]:
        """
        Analyze a backend task to determine its requirements.

        Args:
            task_description: Description of the task

        Returns:
            Dictionary with task analysis
        """
        # Simple keyword-based analysis
        task_lower = task_description.lower()

        # Determine API type
        api_type = "rest"  # Default
        if "graphql" in task_lower:
            api_type = "graphql"

        # Determine HTTP methods
        methods = []
        if "get" in task_lower or "retrieve" in task_lower or "fetch" in task_lower:
            methods.append("get")
        if "create" in task_lower or "post" in task_lower or "add" in task_lower:
            methods.append("post")
        if "update" in task_lower or "put" in task_lower or "modify" in task_lower:
            methods.append("put")
        if "delete" in task_lower or "remove" in task_lower:
            methods.append("delete")

        # If no methods specified, default to all
        if not methods:
            methods = ["get", "post", "put", "delete"]

        # Determine resource
        resource = "item"  # Default
        resource_keywords = [
            "user", "product", "order", "customer", "account",
            "transaction", "payment", "invoice", "item", "category"
        ]

        for keyword in resource_keywords:
            if keyword in task_lower:
                resource = keyword
                break

        # Determine if authentication is needed
        needs_auth = "auth" in task_lower or "login" in task_lower or "secure" in task_lower

        return {
            "api_type": api_type,
            "methods": methods,
            "resource": resource,
            "needs_auth": needs_auth
        }

    def _determine_framework(self, context: A2ATaskContext, task_analysis: Dict[str, Any]) -> str:
        """
        Determine the appropriate framework for the task.

        Args:
            context: Task context
            task_analysis: Analysis of the task

        Returns:
            Framework name
        """
        # Check if framework is specified in context
        framework = None

        if context.metadata and "framework" in context.metadata:
            framework = context.metadata["framework"]

        if context.get_data_parts():
            data = context.get_data_parts()[0]
            if "framework" in data:
                framework = data["framework"]

        # If not specified, determine based on task
        if not framework:
            task_lower = context.get_text_parts()[0].lower() if context.get_text_parts() else ""

            for fw in self._supported_frameworks:
                if fw in task_lower:
                    framework = fw
                    break

        # Default to FastAPI if not specified or found
        if not framework or framework not in self._supported_frameworks:
            framework = "fastapi"

        return framework

    async def _generate_api_code(self, task_analysis: Dict[str, Any], framework: str) -> str:
        """
        Generate API code based on task analysis and framework.

        Args:
            task_analysis: Analysis of the task
            framework: Framework to use

        Returns:
            Generated API code
        """
        api_type = task_analysis["api_type"]
        methods = task_analysis["methods"]
        resource = task_analysis["resource"]
        needs_auth = task_analysis["needs_auth"]

        # Capitalize resource for class names
        resource_cap = resource.capitalize()

        # Generate code based on framework
        if framework == "fastapi":
            return self._generate_fastapi_code(resource, resource_cap, methods, needs_auth)
        elif framework == "flask":
            return self._generate_flask_code(resource, resource_cap, methods, needs_auth)
        else:
            # Default to FastAPI
            return self._generate_fastapi_code(resource, resource_cap, methods, needs_auth)

    def _generate_fastapi_code(self, resource: str, resource_cap: str,
                              methods: List[str], needs_auth: bool) -> str:
        """Generate FastAPI code."""
        code = f"""from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
"""

        if needs_auth:
            code += """from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

# Security settings
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

"""

        # Add models
        code += f"""
# Models
class {resource_cap}Base(BaseModel):
    name: str
    description: Optional[str] = None

class {resource_cap}Create({resource_cap}Base):
    pass

class {resource_cap}({resource_cap}Base):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

"""

        # Add API endpoints
        code += f"""
# API endpoints
app = FastAPI()

"""

        if needs_auth:
            code += """
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Authentication logic
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Token validation logic
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    # Get user from database
    user = get_user(username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user

"""

        # Add CRUD endpoints
        if "get" in methods:
            auth_dep = ", current_user: User = Depends(get_current_user)" if needs_auth else ""
            code += f"""
@app.get("/{resource}s/", response_model=List[{resource_cap}])
async def read_{resource}s({auth_dep}):
    """get all {resource}s."""
    # Implementation
    return [{resource}_db]

@app.get("/{resource}s/{{id}}", response_model={resource_cap})
async def read_{resource}(id: int{auth_dep}):
    """Get a specific {resource}."""
    # Implementation
    return {resource}_db
"""

        if "post" in methods:
            auth_dep = ", current_user: User = Depends(get_current_user)" if needs_auth else ""
            code += f"""
@app.post("/{resource}s/", response_model={resource_cap}, status_code=status.HTTP_201_CREATED)
async def create_{resource}({resource}: {resource_cap}Create{auth_dep}):
    """Create a new {resource}."""
    # Implementation
    new_{resource} = {resource_cap}(
        id=1,
        **{resource}.dict(),
        created_at=datetime.now()
    )
    return new_{resource}
"""

        if "put" in methods:
            auth_dep = ", current_user: User = Depends(get_current_user)" if needs_auth else ""
            code += f"""
@app.put("/{resource}s/{{id}}", response_model={resource_cap})
async def update_{resource}(id: int, {resource}: {resource_cap}Create{auth_dep}):
    """Update a {resource}."""
    # Implementation
    updated_{resource} = {resource_cap}(
        id=id,
        **{resource}.dict(),
        created_at=datetime.now()
    )
    return updated_{resource}
"""

        if "delete" in methods:
            auth_dep = ", current_user: User = Depends(get_current_user)" if needs_auth else ""
            code += f"""
@app.delete("/{resource}s/{{id}}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_{resource}(id: int{auth_dep}):
    """Delete a {resource}."""
    # Implementation
    return None
"""

        return code

    def _generate_flask_code(self, resource: str, resource_cap: str,
                            methods: List[str], needs_auth: bool) -> str:
        """Generate Flask code."""
        # Similar implementation for Flask
        code = f"""from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
"""

        if needs_auth:
            code += """from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
"""

        code += """
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
"""

        if needs_auth:
            code += """app.config["JWT_SECRET_KEY"] = "your-secret-key"
jwt = JWTManager(app)
"""

        code += """
db = SQLAlchemy(app)

"""

        # Add models
        code += f"""
# Models
class {resource_cap}(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {{
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat()
        }}

"""

        if needs_auth:
            code += """
@app.route("/login", methods=["POST"])
def login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    # Check username and password
    # ...

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)

"""

        # Add CRUD endpoints
        if "get" in methods:
            auth_decorator = "@jwt_required()" if needs_auth else ""
            code += f"""
@app.route("/{resource}s", methods=["GET"])
{auth_decorator}
def get_{resource}s():
    """Get all {resource}s."""
    {resource}s = {resource_cap}.query.all()
    return jsonify([{resource}.to_dict() for {resource} in {resource}s])

@app.route("/{resource}s/<int:id>", methods=["GET"])
{auth_decorator}
def get_{resource}(id):
    """Get a specific {resource}."""
    {resource} = {resource_cap}.query.get_or_404(id)
    return jsonify({resource}.to_dict())
"""

        if "post" in methods:
            auth_decorator = "@jwt_required()" if needs_auth else ""
            code += f"""
@app.route("/{resource}s", methods=["POST"])
{auth_decorator}
def create_{resource}():
    """Create a new {resource}."""
    data = request.get_json()
    new_{resource} = {resource_cap}(
        name=data["name"],
        description=data.get("description", "")
    )
    db.session.add(new_{resource})
    db.session.commit()
    return jsonify(new_{resource}.to_dict()), 201
"""

        if "put" in methods:
            auth_decorator = "@jwt_required()" if needs_auth else ""
            code += f"""
@app.route("/{resource}s/<int:id>", methods=["PUT"])
{auth_decorator}
def update_{resource}(id):
    """Update a {resource}."""
    {resource} = {resource_cap}.query.get_or_404(id)
    data = request.get_json()

    {resource}.name = data["name"]
    {resource}.description = data.get("description", {resource}.description)

    db.session.commit()
    return jsonify({resource}.to_dict())
"""

        if "delete" in methods:
            auth_decorator = "@jwt_required()" if needs_auth else ""
            code += f"""
@app.route("/{resource}s/<int:id>", methods=["DELETE"])
{auth_decorator}
def delete_{resource}(id):
    """Delete a {resource}."""
    {resource} = {resource_cap}.query.get_or_404(id)
    db.session.delete({resource})
    db.session.commit()
    return "", 204
"""

        code += """
if __name__ == "__main__":
    app.run(debug=True)
"""

        return code

    def _generate_documentation(self, task_analysis: Dict[str, Any], api_code: str) -> str:
        """
        Generate documentation for the API.

        Args:
            task_analysis: Analysis of the task
            api_code: Generated API code

        Returns:
            API documentation in Markdown format
        """
        resource = task_analysis["resource"]
        resource_cap = resource.capitalize()
        methods = task_analysis["methods"]
        needs_auth = task_analysis["needs_auth"]

        docs = f"""# {resource_cap} API Documentation

This document provides documentation for the {resource_cap} API endpoints.

## Overview

The API provides the following endpoints for managing {resource}s:

"""

        if "get" in methods:
            docs += f"""
### Get All {resource_cap}s

**Endpoint:** `GET /{resource}s/`

**Description:** Retrieve a list of all {resource}s.

**Response:** Array of {resource_cap} objects

```json
[
  {{
    "id": 1,
    "name": "Example {resource_cap}",
    "description": "This is an example {resource}",
    "created_at": "2023-06-15T14:30:45.123456"
  }}
]
```

### Get {resource_cap} by ID

**Endpoint:** `GET /{resource}s/{{{resource}_id}}`

**Description:** Retrieve a specific {resource} by ID.

**Response:** {resource_cap} object

```json
{{
  "id": 1,
  "name": "Example {resource_cap}",
  "description": "This is an example {resource}",
  "created_at": "2023-06-15T14:30:45.123456"
}}
```

"""

        if "post" in methods:
            docs += f"""
### Create {resource_cap}

**Endpoint:** `POST /{resource}s/`

**Description:** Create a new {resource}.

**Request Body:**

```json
{{
  "name": "New {resource_cap}",
  "description": "This is a new {resource}"
}}
```

**Response:** Created {resource_cap} object

```json
{{
  "id": 1,
  "name": "New {resource_cap}",
  "description": "This is a new {resource}",
  "created_at": "2023-06-15T14:30:45.123456"
}}
```

"""

        if "put" in methods:
            docs += f"""
### Update {resource_cap}

**Endpoint:** `PUT /{resource}s/{{{resource}_id}}`

**Description:** Update an existing {resource}.

**Request Body:**

```json
{{
  "name": "Updated {resource_cap}",
  "description": "This is an updated {resource}"
}}
```

**Response:** Updated {resource_cap} object

```json
{{
  "id": 1,
  "name": "Updated {resource_cap}",
  "description": "This is an updated {resource}",
  "created_at": "2023-06-15T14:30:45.123456"
}}
```

"""

        if "delete" in methods:
            docs += f"""
### Delete {resource_cap}

**Endpoint:** `DELETE /{resource}s/{{{resource}_id}}`

**Description:** Delete a {resource}.

**Response:** No content (204)

"""

        if needs_auth:
            docs += f"""
## Authentication

This API requires authentication. To authenticate, you need to:

1. Obtain an access token by sending a POST request to `/token` with your credentials
2. Include the access token in the Authorization header of your requests:
   `Authorization: Bearer your_access_token`

### Get Access Token

**Endpoint:** `POST /token`

**Request Body:**

```json
{{
  "username": "your_username",
  "password": "your_password"
}}
```

**Response:**

```json
{{
  "access_token": "your_access_token",
  "token_type": "bearer"
}}
```

"""

        return docs