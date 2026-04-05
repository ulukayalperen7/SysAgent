# SysAgent: Ultimate AI Operating System Orchestrator

## 1. Project Overview & Vision

**Topic & Purpose:** SysAgent is a centralized control panel and remote operating system orchestrator. It unifies the monitoring, management, and automation of distributed computing environments (Windows, macOS, Linux) under a single UI.

**The Evolution:** Going beyond simple dashboard metrics, SysAgent acts as an "AI-Native Operating System Manager." It utilizes cutting-edge multi-agent frameworks to diagnose issues, generate system scripts, and execute workflows asynchronously. 

## 2. Multi-Agent AI Architecture (Framework Distribution)

To avoid a monolithic AI block, SysAgent strategically assigns different tasks to specialized AI frameworks based on their inherent strengths. This approach ensures scalability, security, and academic rigor.

### Phase 1: CrewAI (Diagnostic & Reporting Unit) - *Implemented*
* **Role:** The System Intent and Diagnostic Pipeline.
* **Why CrewAI?** CrewAI excels at sequential role-playing. It is perfect for complex system analysis where different "experts" need to collaborate before generating an OS-level command.
* **Use Case (The System Action Request):** * A user requests: *"Right now Spotify is running, can you close it?"*
  * **Metric Analyst (Gatekeeper):** Classifies the intent as `ACTION_CLOSE` and identifies 'Spotify' as the target.
  * **Log Investigator (Specialist):** Uses the 'System Audit Tool' to scan the host OS and retrieve active process IDs for Spotify.
  * **Security Auditor (Advisor):** Evaluates the risk of terminating the process (e.g., warning about unsaved data loss).
  * **Chief Reporter (Communicator):** Synthesizes the findings and provides a human-readable explanation alongside the exact `taskkill` script.

### Phase 2: LangGraph (Stateful Workflow Executor) - *Upcoming*
* **Role:** The API Integrator, Router, and Graph-based Workflow Engine.
* **Why LangGraph?** It handles conditional loops, state persistence, and dynamic routing beautifully.
* **Use Case (Multi-Step Automation & Routing):**
  * LangGraph will sit above CrewAI to route tasks. If a user asks for a simple file backup, LangGraph manages it. If the user asks for a deep system diagnostic, LangGraph routes the state to the CrewAI pipeline and waits for the result, creating a highly efficient orchestrator.

### Phase 3: AutoGen (Autonomous Terminal Execution) - *Upcoming*
* **Role:** The Auto-Coder and Self-Correcting Execution Engine.
* **Why AutoGen?** It features built-in code execution and self-debugging capabilities.
* **Use Case (Complex Scripting):**
  * Generating complex, OS-specific PowerShell or Bash scripts on the fly, testing them in a sandboxed environment, and iteratively fixing syntax errors before presenting the final, bug-free script to the user.

## 3. System Architecture & Data Flow

The project is strictly divided to ensure security and scalability:

1. **Frontend (Angular):** The UI. It displays real-time metrics (via WebSocket) and captures user prompts.
2. **Backend (Java Spring Boot):** The Orchestrator and Security Gateway. It handles WebSocket connections, connects to local nodes via OSHI to gather hardware metrics, executes approved scripts, and manages database state. 
3. **AI Engine (Python / FastAPI):** An external microservice containing the AI frameworks (CrewAI, etc.). The Java backend sends structured JSON requests to this Python API, which runs the multi-agent logic and returns the executable results.
4. **SysAgent Nodes:** The actual host devices (Windows, Linux, macOS).

## 4. Extreme Security Measures & Permissions

Because AI will be generating OS-level commands (PowerShell/Bash script), security is the highest priority.
* **Human-In-The-Loop (HITL) Enforcement:** **NO AI COMMAND IS EVER EXECUTED AUTOMATICALLY.** The AI Engine only *proposes* a script. It is sent to the Angular frontend with an explanation. The backend will only execute the script if the authenticated user explicitly clicks "Approve & Run locally."
* **OS-Agnostic Generation:** The Java backend sends the target device's OS flag (e.g., Windows 11) to the Python Engine. The AI is strictly instructed to generate OS-specific commands.
* **Prompt Injection Prevention:** User prompts are sanitized by the Java backend (`PromptSanitizer`) and Python engine (`SecurityAnalyzer`) to prevent arbitrary code execution or system bypass attacks.
* **Database Logging:** Every generated command, along with its execution output (success/fail logs) and status (`PENDING`, `COMPLETED`), is recorded in the `tasks` database table for auditing purposes.
