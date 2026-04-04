import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms'; // Added Forms Module
import { AgentService } from '../../services/agent.service'; // Added Agent Service
import { TerminalService, TerminalLog } from '../../services/terminal.service';
import { AgentIntentResponse } from '../../models/agent.model';

@Component({
  selector: 'app-terminal-window',
  standalone: true,
  imports: [CommonModule, FormsModule], // Added FormsModule to imports
  templateUrl: './terminal-window.html',
  styleUrl: './terminal-window.scss'
})
export class TerminalWindow {

  get logs(): TerminalLog[] {
    return this.terminalService.logs;
  }

  constructor(
    private agentService: AgentService,
    private terminalService: TerminalService
  ) { }

  executeScript(logEntry: any) {
    if (!logEntry.taskId) return;

    logEntry.executing = true;
    this.terminalService.addLog({ sender: 'system', text: `Executing Task [${logEntry.taskId}]...`, type: 'info' });

    this.agentService.executeTask(logEntry.taskId).subscribe({
      next: (output: string) => {
        logEntry.executing = false;
        this.terminalService.addLog({ sender: 'system', text: 'Execution Output:\n' + output, type: 'success' });
      },
      error: (err) => {
        logEntry.executing = false;
        this.terminalService.addLog({ sender: 'system', text: 'Execution Failed: ' + err.message, type: 'error' });
      }
    });
  }

  onCommandEnter(event: any) {
    const command = event.target.value.trim();
    if (command) {
      // 1. Log user command instantly
      this.terminalService.addLog({ sender: 'user', text: `> ${command}` });
      const inputElement = event.target;
      inputElement.value = ''; // Clear input
      inputElement.disabled = true; // Disable input while processing

      this.terminalService.addLog({ sender: 'system', text: 'Processing intent with AI Agent...', type: 'info' });

      // 2. Call Backend Agent Service
      this.agentService.processIntent(command).subscribe({
        next: (response: AgentIntentResponse) => {
          this.terminalService.addLog({
            sender: 'ai',
            text: `Analysis: ${response.explanation}`,
            type: 'success'
          });

          if (response.script) {
            this.terminalService.addLog({
              sender: 'ai',
              text: `Generated Script:\n`,
              script: response.script,
              taskId: response.taskId,
              type: 'warning'
            });
          }

          inputElement.disabled = false;
          setTimeout(() => inputElement.focus(), 100);
        },
        error: (err) => {
          this.terminalService.addLog({ sender: 'system', text: 'Error connecting to Agent backend.', type: 'error' });
          console.error(err);
          inputElement.disabled = false;
          setTimeout(() => inputElement.focus(), 100);
        }
      });
    }
  }
}