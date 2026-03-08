# SysAgent: AI Integration Plan

## 1. Project Overview

**Topic & Purpose:** For this project, I chose the domain of remote system and personal device management. The core objective is to develop "SysAgent," a centralized control panel. The platform aims to unify the management, monitoring, and automation of distributed computing environments (e.g., Windows PCs, MacBooks, and Linux servers) under a single web interface.

**Target Users:** The primary target audience includes software developers, IT students, and tech enthusiasts who operate multiple machines daily and want to streamline repetitive cross-device tasks.

**Core Features (Current Draft):** The current deployment serves as a functional frontend prototype built as a Single Page Application (SPA). The interface includes:
* **Dashboard & Devices:** To monitor connected nodes and their resource usage.
* **Agent Hub:** A directory of ready-to-use execution scripts.
* **Automations:** A visual interface to define automated workflows.

*(Note: Within the scope of this assignment, the data rendered on the screen is mock data integrated directly into the Angular components to demonstrate UI layout and structural behavior).*

## 2. AI Agent Concept

**The Problem:** Currently, managing multiple devices requires writing complex bash or PowerShell scripts for simple automations, memorizing different OS commands, and manually navigating through distinct interfaces. This process is highly inefficient and creates a barrier for quick, cross-platform task execution.

**Agent Type:** To solve this, SysAgent will integrate a **"Natural Language Automation Executor & Advisor"** AI agent. 

**User Interaction & Workflow:** The primary goal of the AI is to translate natural human language into actionable system commands and automation rules.
* **Natural Language Input:** Instead of writing code, the user simply types a prompt into the SysAgent dashboard (e.g., *"Find and compress all log files larger than 1GB in my Windows server's Downloads folder"*).
* **Intent Parsing & Code Generation:** The AI agent analyzes this intent and automatically constructs the correct, OS-specific execution script or JSON-formatted "Trigger → Action" rule.
* **User Approval (Dry-Run):** For security, the AI does not execute commands autonomously. It presents the generated script to the user as a pending action. The command is only dispatched to the target node after the user clicks "Confirm."
* **Secondary Capability (Log Diagnostics):** As an additional background feature, if a system crashes, the AI can optionally review the error logs and suggest a terminal command to fix the issue.

## 3. System Architecture (High-Level)

To ensure security and protect API keys, the heavy AI processing is completely decoupled from the frontend browser. The future architecture is structured as follows:

* **Frontend (Angular):** The user interface submitted for this assignment. It captures the user's natural language prompts and displays the AI's generated scripts for approval.
* **Backend (Java Spring Boot):** Acts as the secure central mediator. It receives the natural language text from the frontend and forwards it to the AI Engine. It also securely stores API keys (like the Gemini API) or manages connections to local models, ensuring no sensitive credentials are exposed to the client.
* **AI Engine (External API or Local LLM):** The core intelligence that processes the text. It returns the exact terminal commands or diagnostic summaries back to the Spring Boot server.
* **SysAgent Nodes (Target Devices):** Lightweight background services running on the host machines. Once the user approves an AI-generated script on the frontend, the backend sends the command via WebSocket to the specific node for local execution.

**Example Data Flow:**
1. User types *"Clear temporary files"* on the Angular frontend.
2. Angular sends this text to the Spring Boot backend via REST API.
3. Spring Boot securely queries the local AI model (e.g., Llama-3 via Ollama) to generate the appropriate shell script for the target device.
4. The AI returns the script to Spring Boot, which passes it to Angular for user review.
5. User clicks "Execute", and Spring Boot sends the final command to the target node.
