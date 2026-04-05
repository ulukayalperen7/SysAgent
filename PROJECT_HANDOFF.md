# SysAgent Project Technical Handoff

## 1. Executive Summary
SysAgent is a cross-platform system monitoring and autonomous diagnostic suite. It bridges a high-performance **Java Spring Boot** backend with a sophisticated **Python-based AI Engine** powered by **CrewAI**. The system allows users to monitor metrics in real-time and interact with their OS using natural language, with a strong emphasis on security and Human-in-the-Loop (HITL) execution.

---

## 2. Architecture & Separation of Concerns

The project follows a "Brain and Hands" architecture:

### 2.1 The "Hands": Java Spring Boot Backend (Port 8080)
- **Data Persistence:** Integrated with **Supabase (PostgreSQL)** for task history and agent interactions.
- **Hardware Metrics:** Uses the **OSHI** library to stream CPU, RAM, and OS metadata via **WebSockets** to the frontend.
- **Security & Execution:** Implements `ScriptExecutionService`, which runs PowerShell commands using Base64 encoding to prevent injection. It *never* executes scripts without manual user approval.
- **AI Adapter:** The `RealAiAgentAdapterImpl` acts as the bridge to the AI Engine, handling JSON communication and parsing AI responses into structured `Explanation/Script` formats.

### 2.2 The "Brain": Python AI Engine (Port 8001)
- **Framework:** Developed using **FastAPI** and **CrewAI**.
- **Internal Pipeline:** A 4-agent sequential crew:
    1. **Metric Analyst:** Classifies intent (CHAT/INFO/FIX).
    2. **Log Investigator:** Uses tools (`psutil`) to collect raw OS/Network data.
    3. **Security Auditor:** Validates findings against a hardcoded whitelist (java, node, python, etc.) to prevent false positives.
    4. **Chief Reporter:** Synthesizes the final output with risk labels (`[SAFE]`, `[REVIEW]`, etc.).
- **Optimization:** Implements a **fast-path classifier** for common greetings/thanks, bypassing the LLM to provide near-instant (<100ms) responses.
- **Concurrency:** Uses `asyncio.Semaphore(1)` to ensure single-threaded execution of the Crew, preventing race conditions or context pollution.

### 2.3 The "Interface": Angular Frontend (Port 4200)
- **Features:** Real-time dashboard using Chart.js/WebSockets and a custom Terminal UI for AI interaction.
- **UX:** Implements auto-scrolling terminal logic and input length validation (500 chars).

---

## 3. The CrewAI Implementation
The current implementation utilizes a **Sequential Process**. 
- **Tools:** Provided via the `@tool` decorator in `tools.py`.
    - `System Audit Tool`: Ranks processes by RAM usage.
    - `Network Audit Tool`: Identifies established TCP/UDP sockets and flags suspicious ports.
- **Memory:** Intentionally disabled for now to maintain Google Gemini compatibility (CrewAI's default RAG storage requires OpenAI).

---

## 4. Future Roadmap & Integration

The architecture is designed to be **Agentic Agnostic**. The API contract between Java and Python is stable, allowing for the following upgrades:

### 4.1 LangGraph Integration
- **Goal:** Move from sequential pipelines to **Stateful Cyclic Graphs**.
- **Use Case:** Allowing the agent to "keep digging" (loops) if the first diagnostic tool doesn't yield results, or "re-trying" a fix if it fails validation.

### 4.2 AutoGen Integration
- **Goal:** Enable multi-agent conversations where agents can "debate" a security risk or work in parallel groups.
- **Use Case:** Scaling to complex multi-node environments where different agents manage different servers.

### 4.3 Multi-Node Scaling
- Implementing a "Registration Token" logic where remote devices can "call home" to the central Spring Boot backend to be monitored.

---

## 5. Security Protocols
1. **No-Auto-Execution:** Scripts are suggested by AI but *only* executed by the user.
2. **Read-Only Tools:** Python tools can read OS state but never modify it.
3. **Whitelist Defense:** Core developer tools are protected from being flagged as malware by the Security Auditor agent.
4. **Credential Isolation:** DB credentials are kept in `application-secret.properties` (ignored by Git).

---

## 6. Handoff Notes for the Next Agent
- **Port Conflicts:** Ensure 8080, 8001, and 4200 are clear before startup.
- **API Keys:** Requires `GOOGLE_API_KEY` (Gemini) in `ai_engine/.env`.
- **Parsing:** The Java adapter expects Python to return `Explanation: ... \n Script: ...`. Do not change this format without updating `RealAiAgentAdapterImpl.java`.
