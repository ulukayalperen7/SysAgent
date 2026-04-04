from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from core.config import get_llm
from agents.crewai.tools import system_audit_tool
import os

@CrewBase
class SystemDiagnosticsCrew():
    """System Diagnostics Crew for analyzing metrics and suggesting commands"""

    # We use dynamic paths to ensure they load properly from the package root
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        super().__init__()
        self.llm = get_llm()

    @agent
    def metric_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['metric_analyst'],
            llm=self.llm,
            verbose=True,
            allow_delegation=True
        )

    @agent
    def log_investigator(self) -> Agent:
        return Agent(
            config=self.agents_config['log_investigator'],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            tools=[system_audit_tool]
        )

    @agent
    def chief_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config['chief_reporter'],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['analysis_task'],
        )

    @task
    def investigation_task(self) -> Task:
        return Task(
            config=self.tasks_config['investigation_task'],
        )

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task'],
        )

    @crew
    def crew(self) -> Crew:
        """Crew configuration and execution process"""
        return Crew(
            agents=self.agents, # Automatically identifies '@agent' decorators
            tasks=self.tasks,   # Automatically identifies '@task' decorators
            process=Process.sequential,
            verbose=True
        )
