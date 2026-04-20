# SysAgent Master Documentation

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

## 4. Data Flow
1. User sends intent from terminal UI.
2. Backend creates a task record in Supabase.
3. Backend collects current host metrics.
4. Backend sends prompt + metrics + thread/session metadata to AI Engine.
5. LangGraph decomposes, routes, and returns explanation + optional script.
6. Backend stores generated script (if present).
7. User approves script in UI for non-autonomous actions.
8. Backend executes script and returns output.
9. Failures are fed back into self-healing loop when appropriate.

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

## 6. CrewAI: How It Works
CrewAI is used as the diagnostics and reasoning specialist layer.

Responsibilities:
- Analyze system and process/network context.
- Produce structured explanation and candidate script.
- Support high-signal investigations before command execution.

CrewAI is not the top-level router. LangGraph decides when CrewAI should be called.

## 7. Autonomy and Safety Model
- Human approval is mandatory for risky or write-like operations.
- Read-only/safe actions can execute autonomously when policy allows.
- Security checks include:
  - Prompt sanitization.
  - Command blacklist and sensitive path guards.
  - Intent-aware approval gating.
- Unknown intents should default to safer handling.

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

## 11. Why Supabase
Supabase (PostgreSQL) is the source of truth for:
- task records,
- script payloads,
- execution states,
- audit history.

This makes behavior traceable and production-ready.

## 12. Near-Term Engineering Priorities
1. Stabilize thread-aware memory in LangGraph sessions.
2. Fix queue auto-resume consistency after approvals.
3. Harden self-heal trigger and recovery prompt handling.
4. Unify approval gating across all script-producing branches.
5. Improve intent safety boundaries for unknown/ambiguous requests.
6. Add regression tests for queue, retry, and recovery flows.
