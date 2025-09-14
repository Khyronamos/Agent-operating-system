# Agent-operating-system
# APIA (Alternative Partially Integrated Autonomy)

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Framework](https://img.shields.io/badge/FastAPI-async-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

APIA is an asynchronous Python framework for building multi‑agent systems with:
- An Agent‑to‑Agent (A2A) JSON‑RPC API (with optional SSE streaming)
- Skill‑based routing and task lifecycle management
- Model Context Protocol (MCP) client integration for external tools
- A shared Knowledge Base and a lightweight orchestrator

For a deeper overview and roadmap, see [src/README/README.md](cci:7://file:///c:/Users/idmrh/Downloads/Khy%20SHI/Dev%20Journey/Fullstack%20SHI/Backend%20shi/Projects/Python/APIA.A2A/src/README/README.md:0:0-0:0).

---

## Table of Contents

- Overview
- Core Features
- Architecture
- Project Structure
- Quickstart
- Configuration (.env support)
- Running the Server
- Docker Quickstart
- API Endpoints
- Development
- Testing
- Troubleshooting
- Contributing
- License
- Security Notes

---

## Overview

APIA helps you compose specialized agents that can communicate, delegate tasks, and coordinate via a simple A2A interface. It uses FastAPI and asyncio for concurrency and clean separation of concerns.

## Core Features

- Async foundation (`asyncio`) with FastAPI
- A2A JSON‑RPC endpoint supporting send, streaming, get, cancel
- Agent system (base + specialized agents in `src/agents/`)
- Skill‑based routing with `A2ATaskRouter` and `A2ATaskManager`
- MCP client integration to call tools and servers
- Shared Knowledge Base with pluggable persistence
- Optional authentication and rate limiting middleware

## Architecture

Key locations:
- [src/main.py](cci:7://file:///c:/Users/idmrh/Downloads/Khy%20SHI/Dev%20Journey/Fullstack%20SHI/Backend%20shi/Projects/Python/APIA.A2A/src/main.py:0:0-0:0) — FastAPI app, startup/shutdown lifecycle, routes, orchestrator
- `src/core/` — primitives (exceptions, framework, task abstractions)
- `src/agents/` — base classes, registry, factory, and implementations
- `src/utils/` — config, models (Pydantic), protocols (MCP/A2A), persistence, DI
- `config/` — YAML/JSON configuration, agent blueprints, MCP definitions

On startup ([lifespan](cci:1://file:///c:/Users/idmrh/Downloads/Khy%20SHI/Dev%20Journey/Fullstack%20SHI/Backend%20shi/Projects/Python/APIA.A2A/src/main.py:114:0-260:54) in [src/main.py](cci:7://file:///c:/Users/idmrh/Downloads/Khy%20SHI/Dev%20Journey/Fullstack%20SHI/Backend%20shi/Projects/Python/APIA.A2A/src/main.py:0:0-0:0)):
1. Load settings from YAML (default: [config/config.yaml](cci:7://file:///c:/Users/idmrh/Downloads/Khy%20SHI/Dev%20Journey/Fullstack%20SHI/Backend%20shi/Projects/Python/APIA.A2A/config/config.yaml:0:0-0:0))
2. Initialize Knowledge Base, Agent Registry, Auth/RateLimit (if enabled), MCP manager, A2A router/task manager, and Agent Factory
3. Create initial agents from `settings.agent_blueprints`
4. Start the Orchestrator for periodic health checks and initial tasks

## Project Structure
APIA.A2A/ ├─ config/ │ ├─ config.yaml # local (ignored by git) │ ├─ config.example.yaml # safe template │ ├─ agent_blueprints.yaml │ ├─ auth_config.yaml │ └─ mcp_config.json ├─ src/ │ ├─ main.py │ ├─ core/ │ ├─ agents/ │ ├─ utils/ │ ├─ middleware/ │ ├─ routes/ │ ├─ tests/ │ ├─ docs/ │ └─ README/ │ ├─ README.md │ └─ requirements.txt ├─ .env.example ├─ README.md ├─ CONTRIBUTING.md ├─ LICENSE └─ .gitignore


## Quickstart

Prerequisites:
- Python 3.9+
- pip
- Node.js/npm (optional; required for some MCP servers launched via `npx`)

Setup:
```bash
# Create and activate a virtual environment
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

# Install Python dependencies
pip install -r src/README/requirements.txt

# Initialize local configuration
cp .env.example .env
cp config/config.example.yaml config/config.yaml
undefined
Configuration (.env support)
Default YAML path: 
config/config.yaml
Override with env var: APIA_CONFIG_FILE=/path/to/your.yaml
.env loading is enabled by default (via pydantic-settings)
${VAR} references inside YAML are expanded from your environment
Example YAML using a token from .env:

yaml
mcp_servers:
  - name: "github"
    connection_type: "stdio"
    command: "npx"
    args:
      - "-y"
      - "@smithery/cli@latest"
      - "run"
      - "@smithery-ai/github"
      - "--config"
      - "{\"githubPersonalAccessToken\":\"${GITHUB_PAT}\"}"
Example .env:

dotenv
GITHUB_PAT=ghp_xxx_redacted
# Optional alternative YAML path
# APIA_CONFIG_FILE=./config/alt-config.yaml
Security tip: never commit real secrets. Use .env and keep 
config.yaml
 local.

Running the Server
bash
# Load settings and run via Python
python src/main.py

# Or run with uvicorn directly
uvicorn main:app --app-dir src --host 127.0.0.1 --port 8000 --log-config=None
Web UIs and health:

Swagger UI: http://127.0.0.1:8000/docs
ReDoc: http://127.0.0.1:8000/redoc
Health: http://127.0.0.1:8000/health
Docker Quickstart
A minimal containerization flow:

Create Dockerfile in the repo root:
dockerfile
FROM python:3.11-slim AS base

WORKDIR /app

# Copy project files
COPY src/ ./src/
COPY config/ ./config/

# Install Python dependencies
RUN pip install --no-cache-dir -r src/README/requirements.txt

# Expose port
EXPOSE 8000

# Start uvicorn
CMD ["uvicorn", "main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000", "--log-config=None"]
Build and run:
bash
docker build -t apia-a2a:latest .
docker run --rm -p 8000:8000 \
  -v $(pwd)/config:/app/config \
  --env-file ./.env \
  apia-a2a:latest
If your MCP servers rely on npx, either include Node.js in your image or run those services outside the container and point APIA to them over the network.

API Endpoints
GET /health — service health
GET /agent-card — AgentCard for the instance (or AIOps agent)
GET /agents — list of all registered agent cards
POST / — A2A JSON‑RPC with methods:
tasks/send
tasks/sendSubscribe (SSE streaming)
tasks/get
tasks/cancel
See models under src/utils/models.py and handling in src/utils/protocols.py and 
src/main.py
.

Development
Entrypoint: 
src/main.py
Agents: src/agents/ (factory, registry, base, implementations)
Core: src/core/
Utilities: src/utils/ (config, models, protocols, persistence, DI)
Middleware: src/middleware/
Routes: src/routes/
Testing
bash
# Example: run a specific test module
python -m src.tests.test_mcp_demo
Troubleshooting
If startup fails, validate 
config/config.yaml
 syntax and that any npx commands exist on PATH.
MCP smoke test warnings mean MCP features are limited; install Node.js or adjust MCP config.
Windows PowerShell: use .venv\Scripts\Activate.ps1 to activate the venv.
