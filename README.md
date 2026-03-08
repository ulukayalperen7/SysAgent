# SysAgent

SysAgent is a web-based dashboard prototype designed to act as a centralized control center. The main goal of this project is to allow users to manage multiple computers (nodes) remotely and utilize AI agents to automate cross-device tasks.

Currently, this repository contains the **Draft Version** of the frontend application, operating as a Single Page Application (SPA).

### Live Demo
You can view the deployed prototype here: **[https://sys-agent.vercel.app/home](https://sys-agent.vercel.app/home)**

### Core Features (Draft Version)
The current frontend prototype includes the following functional sections:
- **Home Page:** Outlines the vision and capabilities of SysAgent.
- **Dashboard:** Provides a comprehensive system summary and rapid statistics.
- **Devices:** Tracks connected nodes in real-time with hardware metrics.
- **Agent Hub:** A marketplace directory of ready-to-use execution scripts.
- **Automations:** A visual rule engine interface to define Trigger-Action workflows.

### Technologies Used
- **Frontend Framework:** Angular 17+
- **Styling:** SCSS 
- **Icons:** Lucide Angular
- **Deployment:** Vercel

### Backend Status & Future Architecture
I have already developed a Java Spring Boot backend for this project. However, per the assignment instructions emphasizing the draft website, this current frontend submission is temporarily disconnected from it. 

To deliver a clean, functional UI prototype, the application currently uses mock data injected directly into the Angular components. The existing Spring Boot backend and the local AI Engine (Ollama) will be fully integrated in the upcoming phases to securely handle natural language automation and local node WebSocket connections.

### How to Run Locally

Follow these instructions to run the Angular development server on your local machine:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ulukayalperen7/SysAgent.git
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
   *(Alternatively, you can use `ng serve`)*

5. **View the application:**
   Open your web browser and navigate to `http://localhost:4200`.

### AI Agent Integration Plan
The comprehensive planning document describing the future AI integration, problem statement, and system architecture can be found in the repository: **[AI_Agent_Planning.md](./AI_Agent_Planning.md)**.
