# SysAgent

SysAgent is a centralized control panel and web-based dashboard designed to orchestrate multiple operating systems (nodes) remotely. Going beyond traditional metrics, it acts as an "AI-Native Operating System Manager," utilizing multi-agent AI workflows to automate cross-device tasks, diagnose issues, and execute OS-level commands safely.

### Live Demo
You can view the deployed frontend prototype here: **[https://sys-agent.vercel.app/home](https://sys-agent.vercel.app/home)**

### Core Features (v1.0 - CrewAI Integrated)
- **Home Page:** Outlines the vision and capabilities of SysAgent.
- **Dashboard:** Provides a comprehensive system summary and rapid statistics.
- **Devices:** Tracks connected nodes in real-time with live hardware metrics (CPU, RAM, Disk).
- **Agent Terminal:** A natural language interface where users can command the AI to analyze the system or execute tasks (e.g., "Close Spotify").
- **Human-in-the-Loop Execution:** AI proposes scripts, but execution requires strict user approval.

### Technologies Used
- **Frontend:** Angular 17+, SCSS, Lucide Angular (Deployed via Vercel)
- **Backend Hub:** Java Spring Boot, PostgreSQL, OSHI (System Metrics), WebSocket
- **AI Engine:** Python, FastAPI, CrewAI, LiteLLM

### Architecture Status
The system operates on a decoupled architecture. The Angular frontend communicates with the Java Spring Boot Backend, which manages security, state, and WebSocket telemetry. When a natural language command is issued, the backend seamlessly routes the prompt and real-time system metrics to the isolated Python FastAPI AI Engine, which runs the CrewAI multi-agent pipeline to return a structured execution script.

### How to Run Locally (Frontend)

Follow these instructions to run the Angular development server on your local machine:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/ulukayalperen7/SysAgent.git](https://github.com/ulukayalperen7/SysAgent.git)
   ```

2. **Navigate to the project folder:**
   ```bash
   cd SysAgent/frontend
   ```

3. **Install dependencies:**
   ```bash
   npm install
   ```

4. **Start the development server:**
   ```bash
   npm run start
   ```

5. **View the application:**
   Open your web browser and navigate to `http://localhost:4200`.

### AI Agent Integration Plan
For a deep dive into the multi-agent architecture (CrewAI, LangGraph, AutoGen) and security protocols, refer to the planning document: **[AI_Agent_Planning.md](./AI_Agent_Planning.md)**.
