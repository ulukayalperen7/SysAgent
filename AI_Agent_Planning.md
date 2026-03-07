# SysAgent: AI Integration Plan

## 1. Project Overview

**Topic & Purpose:** 
For this project, I chose the topic of personal device management. The idea is to make a "SysAgent" control panel. I have a Windows PC and a MacBook, and I wanted a single website where I can see if they are online and manage them remotely. 

**Target Users:**
The target users are developers, IT students, or anyone who uses multiple computers daily and wants to automate things between them.

**Core Features (Current Draft):**
Right now, the website is a working frontend prototype. You can navigate between:
- A Dashboard
- A Devices page (to see connected computers)
- An Agent Hub (like an app store for scripts)
- An Automations page (to link triggers and actions)
Currently, all the data you see on screen is mock data I typed into the Angular components just to show how it will look and feel. 

## 2. AI Agent Concept

**The Problem:**
When something breaks on one of my computers (like a database crashing or a script failing), I have to dig through messy log files to figure out why. It's annoying and takes time.

**What kind of agent is it?**
I plan to integrate an "Evaluator/Advisor" AI agent. 

**How it will work:**
The user won't really chat with the AI like ChatGPT all the time. Mostly, it will work in the background. 
For example, if my Windows PC crashes, an automation rule will trigger the AI. The AI will read the error logs from the PC, figure out what went wrong, and then send an alert to my SysAgent dashboard saying exactly what broke and suggesting a terminal command to fix it. 
If needed, I'll also add a small chat box where I can ask the agent follow-up questions about the error.

## 3. System Architecture (High-Level)

Because adding AI requires some heavy lifting, I can't do it all in the browser. Here is how I plan to set up the system later:

*   **Frontend (Angular):** This is what I submitted for this homework. It just shows the UI and sends requests. It doesn't run the AI.
*   **Backend (Java Spring Boot):** I will build a server to act as the middleman. The frontend will talk to the backend. The backend will hold the secret API keys for the AI (like OpenAI or Gemini) so they don't get stolen.
*   **The Devices:** My actual computers will run a small background script to listen for commands from the backend.
*   **The Flow:** 
    1. The device sends an error log to the Spring Boot backend.
    2. The backend sends that log to the Gemini API and asks, "What is wrong here?"
    3. Gemini sends the answer back to Spring Boot.
    4. Spring Boot saves it and updates the Angular frontend so I can see it on my dashboard.
