# SysAgent Master Documentation

## Document Purpose
This document is the product and architecture source of truth for SysAgent. Use it to understand the mission, system boundaries, runtime roles, core architectural decisions, and technology posture. It is intentionally not a changelog; implementation progress belongs in `SYSAGENT_ROADMAP.md`.

## 1. Mission
SysAgent is an enterprise-grade AI control plane for operating systems. It lets users manage local or remote machines with natural language while preserving strict human approval for risky actions.

Core mission:
- Turn natural language into safe OS operations.
- Keep full auditability and human-in-the-loop control.
- Scale from single-machine tasks to multi-step autonomous workflows.

## 2. Product Goals
- Provide a single terminal-style UX for diagnostics, operations, and automation.
- Use agent orchestration, not a single monolithic prompt.
- Keep security as a first-class runtime policy, not an afterthought.
- Maintain context across turns (memory, queue continuation, and recovery).
- Support production telemetry and traceability for debugging and optimization.

## 3. High-Level Architecture
- `Frontend` (Angular): terminal UI, approve-and-run UX, queue continuation behavior.
- `Backend` (Spring Boot): orchestrates requests, stores tasks, enforces execution lifecycle.
- `AI Engine` (FastAPI): LangGraph supervisor with CrewAI and script generation nodes.
- `Database` (Supabase/PostgreSQL): persistence for tasks, status, scripts, and audit history.
- `MCP Layer`: standardized capability access for safe read-only tools first.
- `Agent Hub`: database-backed runtime configuration for agents, intent routes, MCP permissions, risk policies, prompt versions, device scopes, and decision audit.
- `Auth Layer`: JWT login/register with PBKDF2 password hashing and server-side owner scoping.

## 4. Data Flow
1. User sends intent from terminal UI.
2. Frontend sends the JWT bearer token with the request.
3. Backend resolves the authenticated user and creates an owner-scoped task record in Supabase.
4. Backend collects current host metrics.
5. Backend sends prompt + metrics + thread/session metadata to AI Engine.
6. LangGraph decomposes, routes, and returns explanation + optional script.
7. Backend stores generated script (if present).
8. User approves script in UI for non-autonomous actions.
9. Backend revalidates execution policy, executes the script, and returns structured output.
10. Failures are fed back into self-healing loop when appropriate.

## 5. LangGraph: How It Works
LangGraph is the orchestration brain.

Responsibilities:
- Parse multi-action prompts into atomic steps (`task_queue`).
- Track state (`messages`, intent, queue, errors, retries).
- Route each step:
  - Chat path for pure conversation.
  - CrewAI path for system diagnostics.
  - Action-script path for command generation.
- Apply security/approval policy before execution.
- Continue queue until all steps are complete.
- Support retry/self-heal when execution fails.

Current posture:
- LangGraph remains the top-level workflow brain.
- Agent Hub may influence routes, policies, and prompts, but it should not replace LangGraph.
- MCP must stay below LangGraph as a capability layer.
- The next core hardening target is durable PostgreSQL/Supabase checkpointing instead of in-memory-only graph state.

## 6. CrewAI: How It Works
CrewAI is used as the diagnostics and reasoning specialist layer.

Responsibilities:
- Analyze system and process/network context.
- Produce structured explanation and candidate script.
- Support high-signal investigations before command execution.

CrewAI is not the top-level router. LangGraph decides when CrewAI should be called.

Current posture:
- CrewAI is best used for deeper diagnostic reasoning, not for every terminal request.
- Simple read-only inspection should stay on lightweight LangGraph + MCP paths.
- CrewAI agents may grow, but each additional agent needs a clear diagnostic role, tool scope, and output contract.

## 6.1 MCP: How It Works
MCP is the standardized tool and context access layer.

Current MCP tools are intentionally read-only:
- `system_get_metrics_snapshot`
- `system_list_processes`
- `system_get_top_memory_processes`
- `network_list_connections`
- `network_list_interfaces`
- `system_get_disk_partitions`
- `filesystem_list_directory`
- `filesystem_read_file`
- `filesystem_search`
- `filesystem_get_disk_usage`
- `system_get_platform_info`
- `system_list_installed_apps`
- `devops_git_status`
- `devops_docker_ps`
- `devops_list_npm_scripts`

MCP should grow first through safe read-only capabilities:
- services and startup applications,
- event log and application log readers,
- DNS and network configuration inspection.

MCP must not become the execution boundary. Write, delete, install, kill, firewall, or system mutation capabilities should remain script proposals that require Angular approval and Spring Boot execution.

## 7. Autonomy and Safety Model
- Human approval is mandatory for risky or write-like operations.
- Read-only/safe actions can execute autonomously when policy allows.
- Security checks include:
  - Prompt sanitization.
  - Command blacklist and sensitive path guards.
  - Intent-aware approval gating.
  - Backend execution-policy revalidation before any approved script runs.
- Unknown intents should default to safer handling.

## 7.1 Auth and Device Ownership
- Users register/login through the Spring Boot API.
- Passwords are hashed with PBKDF2; plaintext passwords are never stored.
- API requests use JWT bearer tokens.
- Owner IDs are resolved server-side from the authenticated token.
- Devices are registered to a user through short-lived one-time registration tokens.
- Terminal requests can carry an optional target device ID; backend validates that the selected device belongs to the authenticated user before creating the task.
- Remote-device tasks are stored with `target_device_id`, but execution is intentionally blocked until the secure node command transport exists.
- Spring forwards authenticated owner/device context to the AI Engine so LangGraph prompts and Agent Hub decision audit rows stay tied to the same user/device boundary.

## 8. Self-Healing Model
When an approved script fails:
- Execution error is returned by backend.
- Frontend sends a structured `EXEC_FAILED` recovery prompt.
- LangGraph routes this prompt to repair logic.
- AI proposes corrected script.
- User can re-approve and retry.

This enables controlled autonomy without bypassing safety.

## 9. Primary Use Cases
- Diagnose high CPU/RAM and identify problematic processes.
- Open, close, and manage applications safely.
- Multi-step DevOps setup (clone/install/run) with fallback corrections.
- Contextual follow-up requests ("is it still running?") using memory.
- Event-driven operational automation with approval checks.
- Security-blocking of destructive/system-critical commands.

## 10. Current Operating Principle
- Frontend and backend are stable foundations.
- CrewAI diagnostics pipeline is operational.
- Main improvement focus is LangGraph reliability:
  - queue continuity,
  - thread/session memory isolation,
  - robust self-healing routing,
  - consistent approval gating.
- Auth, owner scoping, and device ownership are now in place; the next remote-access step is secure node transport, not direct script execution over an untrusted shortcut.

## 11. Why Supabase
Supabase (PostgreSQL) is the source of truth for:
- task records,
- script payloads,
- execution states,
- audit history.

This makes behavior traceable and production-ready.

## 12. Near-Term Engineering Priorities
1. Move LangGraph checkpointing and long-term state from in-memory storage to PostgreSQL/Supabase.
2. Expand safe read-only MCP coverage before adding more write/action behavior.
3. Add a semantic MCP tool planner so tool selection is not limited to keyword and regex matching.
4. Bind Agent Hub prompt versions into runtime prompt construction.
5. Add an evaluation suite for read-only routing, risky approval gates, multi-step queues, Turkish/English commands, and self-healing.
6. Build remote node runtime, secure command transport, and automation execution only after Auth/device ownership is stable.

## 13. Framework Posture
Current core framework choices:
- LangGraph: keep as the main orchestrator and state machine.
- MCP: keep as the standard capability/tool layer.
- CrewAI: keep as the diagnostics specialist team.
- FastAPI: keep as the AI Engine HTTP boundary.
- Spring Boot: keep as the only approved script execution boundary.
- Angular: keep as the terminal and human approval surface.

Technology watchlist for later, not immediate adoption:
- LangSmith: tracing, evaluation, and LangGraph observability.
- OpenTelemetry: vendor-neutral logs, metrics, traces, and production diagnostics.
- LiteLLM proxy: model routing, cost controls, retries, and provider failover.
- Google ADK: useful for future experimental agents or Google/Vertex-specific runtimes, but not a replacement for the current LangGraph brain.
- pgvector/Postgres vector search: durable memory, knowledge, and retrieval after core state is stable.

Do not add a new framework just because it is powerful. Add it only when it fills a clear gap without creating a second orchestration brain.
