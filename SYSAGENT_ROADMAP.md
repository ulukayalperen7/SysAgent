# SysAgent Roadmap

## Document Purpose

This document is the implementation roadmap and progress log for SysAgent. Use it to decide what to build next, track completed phases, and preserve the order of work. Product scope and architectural principles live in `SYSAGENT_MASTER_DOCUMENTATION.md`.

Date: May 7, 2026

## Mission

SysAgent is a local-first, privacy-focused system administration platform. Its main product surface is the terminal: the user writes natural language, SysAgent understands the request, inspects the local system when needed, proposes safe scripts for risky actions, waits for human approval, executes only through the Spring Boot backend, and preserves task/session context.

The current system is working. The roadmap is therefore incremental: improve capability, reliability, and safety without replacing the existing architecture.

## Current Architecture

The current request path is:

```text
Angular terminal
-> Spring Boot backend
-> FastAPI AI Engine
-> LangGraph orchestrator
-> CrewAI diagnostics when needed
-> script proposal or read-only result
-> Angular approval when risky
-> Spring Boot ScriptExecutionService
```

The future MCP-enabled path is:

```text
Angular terminal
-> Spring Boot backend
-> FastAPI AI Engine
-> LangGraph orchestrator
-> CrewAI diagnostics when needed
-> MCP client
-> read-only MCP servers/tools
```

MCP is a capability layer under the AI workflow. It is not the workflow brain and it must not bypass approval.

## Angular Role

Angular remains the human-facing terminal and approval gateway.

Responsibilities:

- Show terminal conversation and task output.
- Send natural language intents to the backend.
- Display proposed scripts.
- Require the user to click "Approve & Run locally" before risky execution.
- Trigger self-healing by sending structured execution failure context back to the AI.
- Preserve the current terminal-first UX.

Angular should not execute scripts directly. Angular should not call MCP servers directly in the current architecture.

## Spring Boot Role

Spring Boot remains the gatekeeper and execution boundary.

Responsibilities:

- Create and update task records.
- Store generated scripts and task lifecycle state.
- Collect host metrics and expose metrics APIs/WebSocket updates.
- Call the FastAPI AI Engine.
- Execute approved scripts through `ScriptExecutionService`.
- Maintain auditability and rollback fields.
- Enforce the backend-side security boundary.

Spring Boot is the only layer allowed to execute approved OS scripts. Dangerous execution must not move into Python MCP tools.

## FastAPI Role

FastAPI remains the AI Engine HTTP boundary.

Responsibilities:

- Receive analysis requests from Spring Boot.
- Sanitize prompts before AI processing.
- Build the LangGraph state with prompt, metrics, OS info, and `thread_id`.
- Invoke the LangGraph orchestrator.
- Return explanation, optional script, original prompt, and pending queue count.

The public API contract should remain stable unless a later phase explicitly documents a necessary change.

## LangGraph Role

LangGraph remains the main orchestrator and state machine.

Responsibilities:

- Decompose multi-step user requests into a task queue.
- Pop and process one task at a time.
- Detect intent.
- Route chat, diagnostics, read-only inspection, and script generation.
- Decide when CrewAI should be used.
- Decide when approval is required.
- Preserve thread/session memory.
- Continue queued tasks after approval.
- Handle self-healing after execution failure.
- Produce final synthesized responses.

LangGraph is the brain of the workflow. MCP must be integrated as a tool access layer under existing nodes, not as a replacement for the graph.

## CrewAI Role

CrewAI remains the specialist diagnostics team.

Use CrewAI for deeper investigations:

- Memory or CPU pressure investigation.
- Suspicious process analysis.
- Network inspection.
- Security audit.
- Complex troubleshooting.
- "Why is my system slow?"
- "What process should I close?"

Do not use CrewAI for every simple command. Simple read-only requests and script proposals should stay lightweight through LangGraph nodes.

CrewAI reasons. MCP provides standardized tools.

## MCP Role

MCP is the standardized capability/tool layer.

MCP should answer:

- What tools are available?
- What read-only system data can be inspected?
- What filesystem resources can be safely listed or read?
- What process/network/system capabilities exist?
- What future remote nodes can expose?

Initial MCP integration must be read-only.

Initial safe MCP tools:

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

MCP must not initially expose direct shell execution, file deletion, package installation, process killing, firewall mutation, or persistent system configuration changes.

## Terminal-First Priority

The terminal is the current product focus.

The terminal should feel capable, reliable, safe, and practical. It should prioritize useful action over long academic explanations.

Read-only examples should return concise summaries and findings without approval:

- "show top memory processes"
- "list files in my Downloads folder"
- "read this log file"
- "analyze my network connections"

Risky examples should return an explanation and script proposal, then wait for approval:

- "delete all temp files"
- "close Chrome"
- "install package X"
- "move this folder"
- "change firewall rules"

## Safety Model

Human approval is mandatory for risky operations.

Risky operations include:

- File write, delete, move, or overwrite.
- Closing apps or killing processes.
- Shell command execution.
- Package install/remove/update.
- DevOps write operations.
- Network/firewall changes.
- System configuration changes.
- Persistent or destructive changes.
- Unknown actions with unclear blast radius.

For risky actions, AI and MCP may only:

- Propose a script.
- Explain what the script will do.
- Validate risk.
- Suggest rollback where possible.

Actual execution flow must remain:

```text
Angular approval
-> Spring Boot task execution endpoint
-> ScriptExecutionService
```

Security layers that must remain in place:

- Frontend prompt length guard.
- Backend prompt sanitizer.
- AI Engine prompt sanitizer.
- LangGraph intent-aware approval routing.
- `SecurityGuardian` command validation.
- Backend task lifecycle checks.
- User approval before execution.

## Do Not Break

Do not break the existing terminal flow:

```text
User prompt
-> backend task creation
-> metrics collection
-> AI Engine analysis
-> explanation/script response
-> frontend approval button for scripts
-> backend-only execution
-> execution result
-> self-healing on failure
```

Do not:

- Rewrite Angular from scratch.
- Replace Spring Boot execution with Python execution.
- Replace FastAPI.
- Rewrite the LangGraph orchestrator from scratch.
- Replace CrewAI with MCP.
- Make MCP the top-level router.
- Expose dangerous MCP execution tools in the first implementation.
- Remove existing CrewAI tools before MCP replacements are verified.
- Hardcode app-specific behavior as the main implementation path.
- Change public API contracts without documenting why.

## Phased Roadmap

### Phase 0 - Architecture Documentation and Safety Lock

Status: Completed.

Goal:

- Document the current architecture.
- Lock the safety boundaries before MCP code is added.
- Define MCP as a read-only capability layer first.

Deliverable:

- `SYSAGENT_ROADMAP.md`

### Phase 1 - Read-Only MCP Foundation

Status: Completed.

Goal:

- Add a local MCP server inside the Python AI Engine.
- Add an MCP client wrapper.
- Expose safe read-only system, process, network, platform, and filesystem tools.
- Keep the application working even if MCP fails gracefully.

Do not expose direct shell execution.

### Phase 2 - Connect LangGraph to MCP Without Rewriting It

Status: Completed.

Goal:

- Update existing LangGraph read-only/tool-access nodes to use MCP client wrappers.
- Preserve intent detection, queue behavior, memory, approval gates, and self-healing.

Target behavior:

- Read-only inspection can use MCP autonomously.
- Risky requests still produce approval-required scripts.

### Phase 3 - CrewAI Uses MCP Tool Wrappers for Diagnostics

Status: Completed.

Goal:

- Wrap MCP read-only tools as CrewAI-compatible tools.
- Keep CrewAI as the specialist diagnostics team.
- Replace direct diagnostic tool internals gradually after verification.

### Phase 4 - Terminal Command Quality Upgrade

Status: Completed.

Goal:

- Improve OS-aware script generation.
- Improve concise terminal response formatting.
- Improve unknown intent handling.
- Improve `EXEC_FAILED` repair behavior.

Preferred risky-action response shape:

```text
Understanding:
...

Proposed Action:
...

Risk Level:
Low / Medium / High

Script:
...
```

### Phase 5 - Risk Validation and Script Proposal Layer

Status: Completed.

Goal:

- Add internal logic for command proposal, risk validation, explanation, and rollback suggestions.
- Keep all risky operations approval-gated.
- Keep Spring Boot as the only execution layer.

### Phase 6 - Agent Hub Foundation

Status: In Progress.

Goal:

- Design deployable capabilities without rushing marketplace complexity.
- Map agents to allowed MCP tools, prompts, device scope, and risk levels.
- Propose database schema before implementation.
- Harden the core agent runtime before Auth, automations, and remote access.

No database tables should be created without explicit approval.

Core hardening order:

1. Move LangGraph checkpointing from in-memory `MemorySaver` to PostgreSQL/Supabase-backed persistence.
2. Expand safe read-only MCP tools before adding more write/action behavior.
3. Add a semantic MCP tool planner so tool selection is not limited to keyword and regex matching.
4. Bind Agent Hub prompt versions into runtime prompt construction.
5. Add an evaluation suite for read-only routing, risky approval gates, multi-step queues, Turkish/English commands, and self-healing.
6. Keep Auth, remote access, and automations behind this core reliability work.

Framework watchlist:

- LangSmith, OpenTelemetry, LiteLLM proxy, Google ADK, and pgvector may be useful later.
- Do not add any of them during Phase 6 unless a concrete reliability, observability, model-routing, or memory gap requires it.
- Google ADK should be treated as a future experimental agent runtime, not a replacement for LangGraph.

### Phase 7 - Automations and Scheduled Rules

Goal:

- Design safe automation rules.
- Automations should create approval tasks, not silently mutate the OS.
- Propose schema before implementation.

No database tables should be created without explicit approval.

### Phase 8 - Remote Node Future-Proofing

Goal:

- Keep MCP transport-aware.
- Document future remote device MCP servers.
- Preserve backend audit and approval for remote devices.

Future remote flow:

```text
Angular
-> Spring Boot
-> AI Engine
-> LangGraph
-> MCP client
-> remote device MCP server
-> proposed action
-> Angular approval
-> Spring Boot execution/audit
```

## Phase Progress Log

### Phase 0

Status: Completed.

Notes:

- Added the roadmap and safety contract.
- Defined MCP as a read-only capability layer for initial implementation.
- Reconfirmed LangGraph as orchestrator, CrewAI as diagnostics team, Spring Boot as execution gatekeeper, and Angular as human approval gateway.

### Phase 1

Status: Completed.

Notes:

- Added read-only local system MCP tool implementations.
- Added an optional FastMCP server wrapper for those tools.
- Added an in-process MCP client facade so LangGraph/CrewAI can use stable tool names before transport wiring.
- Added tests for tool discovery, process inspection, platform inspection, bounded file reading, and secret-like file blocking.
- Kept dangerous execution out of MCP.

### Phase 2

Status: Completed.

Notes:

- Added an MCP-backed LangGraph read-only node for safe local inspection.
- Routed supported read-only intents to MCP without rewriting the orchestrator.
- Preserved CrewAI routing for deeper diagnostic system-operation requests.
- Preserved script proposal and approval flow for risky intents.
- Added tests for MCP read-only routing and risky intent exclusion.

### Phase 3

Status: Completed.

Notes:

- Added CrewAI-compatible MCP report builders for system and network diagnostics.
- Preserved existing CrewAI tool names and YAML contracts.
- Replaced direct process/network inspection inside CrewAI tools with MCP-backed read-only wrappers.
- Kept CrewAI as the diagnostics reasoning team, not the router.
- Added tests for CrewAI MCP wrapper output contracts.

### Phase 4

Status: Completed.

Notes:

- Added deterministic terminal handling for common chat, app-control, media-control, and file-operation requests.
- Improved multi-step queue decomposition for English and Turkish connector words.
- Increased safe self-heal retries to 5.
- Improved model script cleanup so markdown fences and extra sections do not reach execution.
- Improved frontend error reporting so backend failures are visible instead of generic connection loss.

### Phase 5

Status: Completed.

Notes:

- Added a script proposal and risk validation layer.
- Added risk/rollback metadata to terminal explanations for approval-required scripts.
- Preserved Angular approval and Spring Boot-only execution.
- Added deterministic script proposals for app open/close, media next/previous/play-pause, desktop file create/write/delete, and install/uninstall proposals.
- Added Supabase/PgBouncer-safe PostgreSQL JDBC prepared-statement configuration.

### Phase 6

Status: In Progress.

Notes:

- Approved the Agent Hub foundation direction before implementation.
- Added an idempotent PostgreSQL/Supabase migration for agent profiles, prompt versions, MCP tool permissions, intent routes, device scopes, risk policies, and decision audit records.
- Added seed data for the current LangGraph/CrewAI/MCP runtime roles so hardcoded routing can be replaced gradually without breaking the terminal flow.
- Added an AI Engine Agent Hub runtime loader that reads intent routes from PostgreSQL/Supabase when available and falls back to the safe seeded defaults when unavailable.
- Added `GET /agent-hub/status` so the runtime route source, route count, target LangGraph nodes, and approval policies are visible during development and debugging.
- Added Agent Hub MCP permission filtering so read-only tool execution must be enabled for the active agent policy before the MCP client is called.
- Added Agent Hub risk policy loading for command blocking and approval gates while retaining static `SecurityGuardian` hard blocks as defense in depth.
- Added optional Agent Hub decision audit persistence from AI Engine analysis results, linked to backend task IDs when PostgreSQL/Supabase is configured.
- Clarified document roles: `SYSAGENT_MASTER_DOCUMENTATION.md` is the product and architecture source of truth, while this roadmap is the implementation order and progress log.
- Re-scoped the next Phase 6 work around core hardening before Auth: PostgreSQL/Supabase LangGraph persistence, broader read-only MCP coverage, semantic tool planning, Agent Hub prompt runtime binding, and evaluation coverage.
- Added an optional LangGraph checkpoint factory that keeps memory checkpointing as the local default and can switch to PostgreSQL/Supabase when `LANGGRAPH_CHECKPOINT_BACKEND=postgres` and `LANGGRAPH_DATABASE_URL` are configured.
- Added checkpoint backend visibility to `GET /agent-hub/status`.
- Expanded MCP read-only filesystem coverage with bounded search and disk usage tools, including Agent Hub seed permissions and LangGraph read-node formatting.
- Added the first MCP tool planner module so read-only tool selection is separated from LangGraph node code and can later evolve into a DB/catalog/evaluation-backed semantic planner.
- Bound the terminal router intent-classifier prompt to Agent Hub prompt versions with safe fallback rendering.
- Added the first routing evaluation dataset for read-only MCP routing and risky approval expectations.
- Added MCP tool usage tracking in LangGraph state so decision audit can record which read-only tools were actually called.
- Expanded MCP read-only system inventory coverage with network interface and disk partition tools.
- Added AI Engine runtime health reporting and lazy LangGraph loading so status endpoints can surface missing dependencies instead of failing during application startup.
- Added a Spring Boot `/api/agent/runtime-status` proxy so UI and future operators can inspect AI Engine, Agent Hub, checkpoint, and MCP health without calling Python directly.
- Typed the runtime-status backend contract and connected the Angular Agent Hub page to live runtime, dependency, checkpoint, prompt-agent, and MCP tool data instead of demo marketplace cards.
- Added a database-backed Agent Hub profile catalog endpoint and connected the Angular Agent Hub page to the seeded `agent_profiles` records with prompt and MCP permission counts.
- Replaced the static Angular History page with a tenant-scoped task history DTO backed by the real task table, avoiding raw script exposure in list views.
- Added a database-backed automation rule catalog and connected the Angular Automations page to real persisted rules, while keeping creation/execution disabled until core policy and Auth are ready.
- Removed remaining fake device seed behavior and disabled synthetic pairing-token UI until Auth-backed remote device registration is implemented.
- Removed the remaining mock AI adapter, stale backend log artifacts, and old debug state artifact from the source tree.
- Centralized the pre-auth owner placeholder behind `CurrentUserProvider` so JWT/Supabase Auth can replace it from one boundary later.
- Replaced app-specific CrewAI prompt examples with generic app discovery guidance.
- Added a read-only installed-app inventory MCP tool, planner coverage, Agent Hub seed registration, and routing eval coverage for dynamic app discovery.
- Added read-only DevOps MCP tools for git status, Docker container listing, and package.json script inspection.
- Added `active_step` propagation so resumed LangGraph queue steps are persisted against the concrete task instead of the literal `continue` prompt.
- Added structured task execution responses and backend execution-policy revalidation before approved scripts can run.
- Added focused backend tests for AI queue response mapping and execution-policy blocking.
- Cleaned Angular build warnings for known STOMP/SockJS CommonJS dependencies and the terminal component style budget.
- Started the Auth foundation with JWT register/login, PBKDF2 password hashing, protected Angular routes, bearer-token HTTP interceptor, and server-side `CurrentUserProvider` resolution.
- Added authenticated device registration-token generation plus a public node registration endpoint that binds a machine to the token owner.
- Added target-device task binding: terminal requests can select a registered device, backend validates ownership, and remote execution is blocked until secure node transport is implemented.
- Added owner/device context propagation from Spring to the AI Engine so LangGraph prompts and Agent Hub audit metadata can reason about the selected execution target.
- Added the first secure remote-node transport foundation: node token hash storage, heartbeat, command polling, result callback, remote command queue persistence, and frontend queued-state handling.
- Hardened Auth/CORS for the June 20, 2026 remote-access path: configurable CORS whitelist, login/register rate limiting, and production startup checks for JWT secret/CORS wildcard safety.
- Added the first installable `sysagent-node` Python CLI runtime with device registration, local token config, heartbeat, command polling, local execution, result callback, and focused config/executor tests.
- Added owner-scoped remote command status APIs plus Angular terminal polling and History refresh so queued node commands progress through `QUEUED`, `CLAIMED`, `COMPLETED`, and `FAILED` without mock data.
- Activated the Devices page action buttons: `Terminal` opens the dashboard with the selected device target, and `Logs` loads owner-scoped task history for that device.
- Improved LangGraph checkpoint status reporting so Agent Hub shows whether PostgreSQL checkpointing is truly active, merely configured, or falling back to memory.
- Added real node heartbeat CPU/RAM persistence so the Devices page no longer has to show placeholder metrics for registered runtimes.
- Added cross-platform `sysagent-node service-install/service-uninstall` planning for Windows Scheduled Task, Linux systemd user service, and macOS LaunchAgent, with explicit `--apply` for execution.
- Added the first desktop context foundation for remote nodes: node-token-protected snapshot submission, owner-scoped latest context API, active-window/process metadata, bounded screenshot storage, and Devices page preview.
- Propagated lightweight screen context summaries into the AI Engine payload for selected remote devices without embedding large screenshot payloads in every analysis request.
- Connected remote screen context to LangGraph script proposal prompts and deterministic app-reference resolution, so requests like "close this app" can resolve to the latest active process without hardcoding product-specific commands.
- Added controlled screenshot-to-text preparation: backend only includes raw screen images for screen-context requests, AI Engine can summarize them with a vision-capable Gemini model, and raw base64 is removed before LangGraph state/audit storage.
