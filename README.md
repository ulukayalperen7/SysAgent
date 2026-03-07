# SysAgent

Hey, this is SysAgent which is a prototype for a web-based dashboard for now. The main idea is to have a control center where I can manage my different computers (nodes) and eventually use AI to automate tasks on them.

Right now, this is just the **Draft Version** of the frontend website. 

### Why is there no backend yet?
The assignment requirements stated "Backend (if any)" for this draft phase. So, to get a working, clickable prototype done on time, I built the UI using Angular and filled it with mock data directly in the code. 
I do have a Spring Boot backend planned, but I haven't connected it yet since the goal of this homework was just to show the functional web design and routing.

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

### AI Planning
I also wrote a plan for how an AI agent will eventually be added to this website. You can find that PDF/Markdown file here: [AI_Agent_Planning.md](./AI_Agent_Planning.md).
