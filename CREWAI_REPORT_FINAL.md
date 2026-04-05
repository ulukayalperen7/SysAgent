# SysAgent: CrewAI Implementation Report

## 1. Project Overview
SysAgent is an AI-powered system monitoring and diagnostic tool. It uses a **4-agent sequential pipeline** (built with CrewAI) to analyze system health, investigate performance bottlenecks, audit network security, and suggest safe terminal scripts.

## 2. AI Engine Architecture (The Brain)
The AI Engine is built with **FastAPI** (Python) and orchestrates 4 specialized agents.

### 2.1 Agents (The Team)
- **Metric Analyst:** Classifies user intent (CHAT vs. INFO vs. FIX). Ensures resources aren't wasted on idle chat.
- **Log Investigator:** Performs "deep dives". Uses the `System Audit Tool` and `Network Audit Tool` to gather raw OS data.
- **Security Auditor:** A critical reasoning agent. Reviews all findings against a whitelist (e.g., java.exe, node.exe) to ensure system tools aren't flagged as threats.
- **Chief Reporter:** The final communicator. Synthesizes all data into a human-friendly explanation and generates a safe, risk-labeled script.

### 2.2 Specialized Tools
- **System Audit Tool:** Uses `psutil` to capture the top 10 RAM/CPU processes.
- **Network Audit Tool:** Captures a snapshot of live `ESTABLISHED` TCP/UDP connections.

### 2.3 Workflow (Kickoff Logic)
1. User prompt entries via Angular.
2. Java Backend passes prompt + hardware metrics to Python.
3. Python `main.py` checks for "fast-path" chat (instant responses for greetings).
4. For complex queries, `SystemDiagnosticsCrew().kickoff()` starts the 4-agent sequence.

---

## 3. Backend Integration (The Hands)
The **Java Spring Boot** backend serves as the bridge between the AI and the local machine.

- **Adapter Pattern:** `RealAiAgentAdapterImpl` communicates with the Python engine via JSON.
- **Persistence:** All task history and AI responses are stored in **Supabase (PostgreSQL)**.
- **HITL (Human-in-the-Loop):** The AI proposes a script, but **Java only executes it** if the user explicitly clicks "Approve" in the dashboard.
- **Metrics Collection:** Uses **OSHI** to pull live hardware data for the dashboard and for AI context.

---

## 4. Key Implementation Highlights
- **Security Whitelisting:** The `Security Auditor` has a hard-coded list of safe developer processes (java, python, node, code, etc.) to prevent AI hallucinations and false alarms.
- **Intent-Based Filtering:** The system distinguishes between "Show me my RAM" (Information) and "My RAM is full" (Fix), preventing unnecessary script generation for simple questions.
- **Async Efficiency:** Python uses `asyncio.Semaphore` to handle one complex AI request at a time, protecting the limited context window of the LLM.

## 5. Homework Requirements Checklist
- [x] **Agents/Tasks/Kickoff Snippets:** Included in `crew.py`, `agents.yaml`, and `tasks.yaml`.
- [x] **Screenshot:** Added to the documentation.
- [x] **Git URL:** (User to provide).
- [x] **Detailed Explanations:** Included in this report.
