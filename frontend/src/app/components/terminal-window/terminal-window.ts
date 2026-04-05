import { Component, ElementRef, ViewChild, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AgentService } from '../../services/agent.service';
import { TerminalService, TerminalLog } from '../../services/terminal.service';
import { AgentIntentResponse } from '../../models/agent.model';

// Maximum number of characters a user can send in one message
const MAX_PROMPT_LENGTH = 500;

@Component({
  selector: 'app-terminal-window',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './terminal-window.html',
  styleUrl: './terminal-window.scss'
})
export class TerminalWindow implements AfterViewChecked {

  // Used to auto-scroll the terminal to the bottom after each new log entry
  @ViewChild('terminalBody') private terminalBody!: ElementRef;

  get logs(): TerminalLog[] {
    return this.terminalService.logs;
  }

  constructor(
    private agentService: AgentService,
    private terminalService: TerminalService
  ) { }

  /**
   * Called by Angular after every change detection cycle.
   * Scrolls the terminal to the bottom to show the latest message.
   */
  ngAfterViewChecked(): void {
    this.scrollToBottom();
  }

  private scrollToBottom(): void {
    try {
      this.terminalBody.nativeElement.scrollTop = this.terminalBody.nativeElement.scrollHeight;
    } catch (err) {
      // Ignore scroll errors during initial render
    }
  }

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
    if (!command) return;

    // Validate input length to avoid overloading the LLM
    if (command.length > MAX_PROMPT_LENGTH) {
      this.terminalService.addLog({
        sender: 'system',
        text: `Message too long (${command.length}/${MAX_PROMPT_LENGTH} chars). Please be more concise.`,
        type: 'error'
      });
      return;
    }

    // Log user message immediately and clear the input field
    this.terminalService.addLog({ sender: 'user', text: `> ${command}` });
    const inputElement = event.target;
    inputElement.value = '';
    inputElement.disabled = true;

    this.terminalService.addLog({ sender: 'system', text: 'Processing intent with AI Agent...', type: 'info' });

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
            text: `Generated Script:`,
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