"""
crew.py — CrewAI Crew Assembly for SysAgent AI Engine.

This file wires together agents and tasks into a sequential pipeline.
The execution order is strictly:
  metric_analyst → log_investigator → security_auditor → chief_reporter

Each agent only uses tools appropriate for its role. The security_auditor
is a reasoning-only agent — it does not call tools, it reviews tool output
from the log_investigator via shared CrewAI context.

Date: 2026-04-04
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from core.config import get_llm
from agents.crewai.tools import system_audit_tool, network_audit_tool


@CrewBase
class SystemDiagnosticsCrew():
    """System Diagnostics Crew — 4-agent sequential pipeline with security review."""

    # Path to YAML config files (relative to the package root, resolved by CrewBase)
    agents_config = 'config/agents.yaml'
    tasks_config  = 'config/tasks.yaml'

    def __init__(self):
        super().__init__()
        self.llm = get_llm()

    # ------------------------------------------------------------------
    # Agent Definitions
    # ------------------------------------------------------------------

    @agent
    def metric_analyst(self) -> Agent:
        """
        First agent in the pipeline.
        Classifies the user intent and reviews high-level hardware metrics.
        Does not need tools — it reasons from the metrics provided in the prompt.
        """
        return Agent(
            config=self.agents_config['metric_analyst'],
            llm=self.llm,
            verbose=True,
            allow_delegation=False  # Does not pass work to other agents
        )

    @agent
    def log_investigator(self) -> Agent:
        """
        Second agent in the pipeline.
        Runs tools to gather live process and network data when a real issue is found.
        Has access to both the System Audit Tool and the Network Audit Tool.
        """
        return Agent(
            config=self.agents_config['log_investigator'],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            tools=[system_audit_tool, network_audit_tool]  # Both read-only tools
        )

    @agent
    def security_auditor(self) -> Agent:
        """
        Third agent in the pipeline.
        Reviews the Log Investigator's output for security anomalies.
        Reasoning-only — does NOT call tools. It reads context from previous tasks.
        Outputs a risk rating: SAFE / LOW_RISK / REVIEW.
        """
        return Agent(
            config=self.agents_config['security_auditor'],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
            # No tools — intentional. Security Auditor reasons from passed context only.
        )

    @agent
    def chief_reporter(self) -> Agent:
        """
        Final agent in the pipeline.
        Synthesizes all findings into a user-facing explanation and (optionally) a script.
        Outputs the structured 'Explanation: / Script:' format every time.
        """
        return Agent(
            config=self.agents_config['chief_reporter'],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    # ------------------------------------------------------------------
    # Task Definitions
    # ------------------------------------------------------------------

    @task
    def analysis_task(self) -> Task:
        """Task 1: Classify intent and assess hardware metrics."""
        return Task(config=self.tasks_config['analysis_task'])

    @task
    def investigation_task(self) -> Task:
        """Task 2: Run audit tools and gather live system data."""
        return Task(config=self.tasks_config['investigation_task'])

    @task
    def security_review_task(self) -> Task:
        """Task 3: Review investigation findings for security anomalies."""
        return Task(config=self.tasks_config['security_review_task'])

    @task
    def reporting_task(self) -> Task:
        """Task 4: Write the final explanation and script for the user."""
        return Task(config=self.tasks_config['reporting_task'])

    # ------------------------------------------------------------------
    # Crew Assembly
    # ------------------------------------------------------------------

    @crew
    def crew(self) -> Crew:
        """
        Assembles all agents and tasks into a sequential crew.
        Tasks execute in definition order: analyst → investigator → auditor → reporter.
        Memory is intentionally disabled — it requires OpenAI embeddings (ChromaDB),
        which conflicts with the Gemini-only setup used in this project.
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
