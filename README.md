# SysAgent

SysAgent is a web-based dashboard prototype designed to act as a centralized control center. The main goal of this project is to allow users to manage multiple computers (nodes) remotely and utilize AI agents to automate cross-device tasks.

Currently, this repository contains the **Draft Version** of the frontend application.

Live Demo
You can view the deployed prototype here: **[https://sys-agent.vercel.app/home]**

### Why is there no backend yet?
The assignment requirements stated "Backend (if any)" for this draft phase. So, to get a working, clickable prototype done on time, I built the UI using Angular and filled it with mock data directly in the code. 
A Spring Boot backend is planned for future iterations to securely handle AI API integrations and local node WebSocket connections, but it is omitted here to keep the focus on frontend routing and design clarity.

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
