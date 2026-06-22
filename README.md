# SysAgent

SysAgent is an AI-assisted operating system control plane. It provides a terminal-style web UI where a user can describe system tasks in natural language, review the proposed action, and approve execution through a backend-controlled audit path.

The project is still under active development. The current focus is the core orchestration, security boundary, device ownership, and controlled desktop automation foundation.

## What It Does

- Turns natural language into safe OS actions.
- Keeps risky actions behind human approval.
- Stores tasks, scripts, results, device state, and audit history in PostgreSQL/Supabase.
- Supports local backend execution and registered remote node execution.
- Uses LangGraph as the main AI workflow orchestrator.
- Uses MCP for safe read-only system tools.
- Uses a Python node runtime for registered machines.
- Supports desktop context snapshots for approved remote automation flows.

Example request:

```text
Create a file named sysagent-demo.txt on my Desktop and write a short note that says SysAgent is ready for controlled desktop automation.
```

SysAgent responds with an explanation, risk level, rollback note, and a script proposal. The script is not executed until the user approves it.

## Architecture

```text
Angular Web UI
-> Spring Boot Backend
-> FastAPI AI Engine
-> LangGraph Orchestrator
-> CrewAI / MCP / Script Proposal Layer
-> Approval Gate
-> Backend or registered Node Runtime execution
-> Result, audit, and optional repair flow
```

Main folders:

- `frontend` - Angular UI, terminal, auth screens, devices, agent hub, automations, and history pages.
- `backend` - Spring Boot API, auth, task lifecycle, device ownership, execution policy, node command queue, and Supabase/PostgreSQL persistence.
- `ai_engine` - FastAPI AI service with LangGraph, CrewAI, MCP tools, Agent Hub runtime config, script proposal, and verification logic.
- `node_runtime` - Python CLI runtime installed on a user machine to heartbeat, poll approved commands, execute locally, and send results back.

## Security Model

SysAgent is designed around a simple rule: AI can propose, but the trusted backend enforces and executes.

Current safety layers include:

- JWT login/register with server-side owner scoping.
- PBKDF2 password hashing.
- Configurable CORS allowlist.
- Login/register rate limiting.
- Production startup checks for weak JWT secrets and wildcard CORS.
- Optional shared key between backend and AI Engine using `X-SysAgent-AI-Key`.
- One-time device registration tokens.
- Hashed node runtime tokens.
- Owner-scoped tasks, devices, results, and desktop context.
- Backend execution-policy validation before approved scripts run.
- Human approval for risky write, delete, install, kill, GUI, and shell actions.
- Raw SQL logging disabled by default.
- Secrets and local node config excluded from Git.

Do not commit `.env`, `application-secret.properties`, Supabase service keys, AI provider keys, node config files, or private certificates.

## Current Status

Implemented:

- Auth foundation.
- Agent Hub database-backed configuration foundation.
- Task history and audit flow.
- Remote node registration and command polling.
- Node heartbeat, result callback, and status tracking.
- MCP read-only tools for system, filesystem, network, inventory, and devops inspection.
- Controlled script proposal with risk metadata.
- Basic GUI automation foundation with approval and verification feedback.
- Desktop context snapshot support for remote nodes.

Still planned:

- Production-grade packaged installers for the node runtime.
- Stronger visual workflow repair for complex desktop applications.
- More complete cross-platform GUI helper support.
- Durable LangGraph checkpointing as the default runtime mode.
- Broader evaluation coverage for multi-step desktop automation.

## Local Development

### Backend

```powershell
cd backend
mvn spring-boot:run
```

Default backend URL:

```text
http://localhost:8080
```

### AI Engine

```powershell
cd ai_engine
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

Default AI Engine URL:

```text
http://localhost:8001
```

### Frontend

```powershell
cd frontend
npm install
npm start
```

Default frontend URL:

```text
http://localhost:4200
```

### Node Runtime

```powershell
cd node_runtime
python -m pip install .
sysagent-node status
```

After creating a device registration token from the web UI:

```powershell
sysagent-node bootstrap --server http://localhost:8080 --token <registration-token> --install-service
sysagent-node run
```

## Important Environment Variables

Common backend variables:

```env
SYSAGENT_AUTH_JWT_SECRET=<strong-secret>
SYSAGENT_CORS_ALLOWED_ORIGINS=http://localhost:4200
SYSAGENT_PRODUCTION=false
SYSAGENT_PUBLIC_BACKEND_URL=http://localhost:8080
SYSAGENT_AI_ENGINE_API_KEY=<optional-shared-ai-engine-key>
```

Common AI Engine variables:

```env
AI_ENGINE_API_KEY=<optional-shared-ai-engine-key>
GEMINI_API_KEY=<provider-key>
GOOGLE_API_KEY=<provider-key>
OPENAI_API_KEY=<provider-key>
```

Use only the provider key needed for your configured model. Keep all real values in local environment files or deployment secrets.

## Tests

Backend:

```powershell
cd backend
mvn test
```

AI Engine:

```powershell
cd ai_engine
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

Frontend:

```powershell
cd frontend
npm run build
```

## Documentation

- `SYSAGENT_MASTER_DOCUMENTATION.md` explains the product scope, architecture, security model, and framework decisions.
- `SYSAGENT_ROADMAP.md` tracks implementation phases and completed work.
- `node_runtime/README.md` explains the machine runtime CLI.

## License

No license has been selected yet.
