# SysAgent

SysAgent is a web-based dashboard prototype designed to act as a centralized control center. The main goal of this project is to allow users to manage multiple computers (nodes) remotely and utilize AI agents to automate cross-device tasks.

Currently, this repository contains the **Draft Version** of the frontend application.

Live Demo
You can view the deployed prototype here: **[https://sys-agent.vercel.app/home]**

### Backend Status & Architecture
I have already developed a Java Spring Boot backend for this project. However, per the assignment instructions emphasizing the draft website, this current frontend submission is temporarily disconnected from it.

To deliver a clean, functional UI prototype that can be easily deployed and reviewed right now, the application currently uses mock data injected directly into the Angular components. The existing Spring Boot backend will be fully integrated in the upcoming phases to securely handle AI API keys and local node WebSocket connections.

### Technologies
- **Frontend:** Angular 17
- **Styling:** SCSS
- **Icons:** Lucide Angular

### How to Run Locally
"Running locally" just means running the website on your own computer instead of a public server, which is how we develop web apps before putting them on the internet.

1. Clone the repo and go into the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Install the packages:
   ```bash
   npm install
   ```
3. Start the Angular dev server:
   ```bash
   npm run start
   ```
4. Open your web browser and go to `http://localhost:4200`.

### AI Agent Integration Plan
I also wrote a plan for how an AI agent will eventually be added to this website. You can find that PDF/Markdown file here: [AI_Agent_Planning.md](./AI_Agent_Planning.md).
