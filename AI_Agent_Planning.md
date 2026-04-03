# SysAgent: Ultimate AI Operating System Orchestrator

## 1. Project Overview & Vision

**Topic & Purpose:** SysAgent is a centralized control panel and remote operating system orchestrator. It unifies the monitoring, management, and automation of distributed computing environments (Windows, macOS, Linux) under a single UI.

**The Evolution:** Going beyond simple dashboard metrics, SysAgent acts as an "AI-Native Operating System Manager." It utilizes cutting-edge multi-agent frameworks to diagnose issues, generate system scripts, and execute workflows asynchronously. 

## 2. Multi-Agent AI Architecture (Framework Distribution)

To avoid a monolithic AI block, SysAgent strategically assigns different tasks to specialized AI frameworks based on their inherent strengths. This approach ensures scalability, security, and academic rigor as each framework is introduced progressively.

### Phase 1: CrewAI (Diagnostic & Reporting Unit) - *Current Focus*
* **Role:** The Incident Response and Diagnostic Team.
* **Why CrewAI?** CrewAI excels at role-playing and inter-agent debate. It is perfect for complex system analysis where different "experts" need to collaborate.
* **Use Case (The System Health Check):** 
  * A user reports: *"My PC is overheating and running slow."*
  * **Metric Analyst Agent:** Reviews the real-time CPU/RAM/Disk metrics provided by the Java backend.
  * **Log Investigator Agent:** Analyzes active processes and recent OS error logs.
  * **Chief Summarizer Agent:** Synthesizes the findings and provides a human-readable diagnosis along with a recommended action (e.g., *"We found 3 phantom Docker containers consuming 80% CPU. Do you want to kill them?"*).

### Phase 2: LangGraph (Stateful Workflow Executor) - *Upcoming*
* **Role:** The API Integrator and Graph-based Workflow Engine.
* **Why LangGraph?** It handles loops, state persistence, and external API integrations beautifully.
* **Use Case (Multi-Step Automation):**
  * A user requests: *"Backup my desktop documents, zip them, and alert me on MS Teams."*
  * LangGraph will construct a state machine: Step 1 (Zip Files) -> Step 2 (Check Size) -> Step 3 (Send Teams Webhook). If Step 1 fails, it loops back and retries or asks for user intervention.

### Phase 3: AutoGen (Autonomous Terminal Execution) - *Upcoming*
* **Role:** The Auto-Coder and Self-Correcting Execution Engine.
* **Why AutoGen?** It features built-in code execution and self-debugging capabilities.
* **Use Case (Complex Scripting):**
  * Generating complex, OS-specific PowerShell or Bash scripts on the fly, testing them in a sandboxed environment, and iteratively fixing syntax errors before presenting the final script to the user.

## 4. System Architecture & Data Flow

The project is strictly divided to ensure security and scalability:

1. **Frontend (Angular):** The UI. It displays real-time metrics (via WebSocket) and captures user prompts.
2. **Backend (Java Spring Boot):** The Orchestrator and Security Gateway. It handles WebSocket connections, connects to local nodes via OSHI to gather hardware metrics, stores tasks in PostgreSQL/Supabase, and manages JWT-based Tenant Isolation (Multi-tenancy). 
3. **AI Engine (Python / FastAPI):** An external microservice containing the AI frameworks (CrewAI, etc.). The Java backend sends structured JSON requests to this Python API, which runs the multi-agent logic and returns the results.
4. **SysAgent Nodes:** The actual host devices (Windows, Linux, macOS).

## 5. Extreme Security Measures & Permissions

Because AI will be generating OS-level commands (PowerShell/Bash script), security is the highest priority.
* **Human-In-The-Loop (HITL) Enforcement:** **NO AI COMMAND IS EVER EXECUTED AUTOMATICALLY.** The AI Engine only *proposes* a script. It is sent to the Angular frontend with a "Dry-Run Explanation." The backend will only execute the script if the authenticated user explicitly clicks "Confirm & Run."
* **OS-Agnostic Generation:** The Java backend sends the target device's OS flag (e.g., `os: WINDOWS`) to the Python Engine. The AI is strictly instructed to generate OS-specific commands.
* **Prompt Injection Prevention:** User prompts are sanitized by the Java backend before being forwarded to the Python AI Engine to prevent arbitrary code execution attacks.
* **Database Logging:** Every generated command, along with its execution output (success/fail logs), is permanently recorded in the `task_logs` database table for auditing purposes.
