import { Component, ElementRef, ViewChild, AfterViewChecked, ChangeDetectorRef, OnInit } from '@angular/core';
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
export class TerminalWindow implements AfterViewChecked, OnInit {

  // Used to auto-scroll the terminal to the bottom after each new log entry
  @ViewChild('terminalBody') private terminalBody!: ElementRef;

  get logs(): TerminalLog[] {
    return this.terminalService.logs;
  }

  // UI States
  isThinking = false;
  isExecuting = false;

  private shouldScrollToBottom = false;

  constructor(
    private agentService: AgentService,
    private terminalService: TerminalService,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit(): void {
    this.terminalService.logs$.subscribe(logs => {
      this.shouldScrollToBottom = true; // Flag for auto-scroll on new message
      this.cdr.detectChanges();
    });
  }

  /**
   * Called by Angular after every change detection cycle.
   * Scrolls the terminal to the bottom to show the latest message.
   */
  ngAfterViewChecked(): void {
    if (this.shouldScrollToBottom) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }

  private scrollToBottom(): void {
    try {
      this.terminalBody.nativeElement.scrollTop = this.terminalBody.nativeElement.scrollHeight;
    } catch (err) {
      // Ignore scroll errors during initial render
    }
  }

  onSendClick(input: HTMLInputElement) {
    if (this.isThinking || this.isExecuting) return;
    const val = input.value.trim();
    if (val) {
      this.processCommand(val, input);
    }
  }

  onCommandEnter(event: any) {
    if (this.isThinking || this.isExecuting) return;
    const command = event.target.value.trim();
    if (command) {
      this.processCommand(command, event.target);
    }
  }

  private processCommand(command: string, inputElement: HTMLInputElement) {
    // Validate input length
    if (command.length > MAX_PROMPT_LENGTH) {
      this.terminalService.addLog({
        sender: 'system',
        text: `Message too long (${command.length}/${MAX_PROMPT_LENGTH} chars).`,
        type: 'error'
      });
      return;
    }

    // Log user message and clear input
    this.terminalService.addLog({ sender: 'user', text: `> ${command}` });
    inputElement.value = '';
    this.isThinking = true;

    this.agentService.processIntent(command).subscribe({
      next: (response: AgentIntentResponse) => {
        this.isThinking = false;
        this.terminalService.addLog({
          sender: 'ai',
          text: response.explanation,
          type: 'success'
        });

        if (response.script) {
          this.terminalService.addLog({
            sender: 'ai',
            text: `Recommended Action:`,
            script: response.script,
            taskId: response.taskId,
            type: 'warning'
          });
        }
        setTimeout(() => inputElement.focus(), 100);
      },
      error: (err) => {
        this.isThinking = false;
        this.terminalService.addLog({ sender: 'system', text: 'Connection lost. Please try again.', type: 'error' });
        console.error(err);
        setTimeout(() => inputElement.focus(), 100);
      }
    });
  }

  executeScript(logEntry: any) {
    if (!logEntry.taskId) return;

    logEntry.executing = true;
    this.isExecuting = true;

    this.agentService.executeTask(logEntry.taskId).subscribe({
      next: (output: string) => {
        logEntry.executing = false;
        this.isExecuting = false;
        // Check if output contains "Errors" (case insensitive)
        const isError = output.toLowerCase().includes('error') || output.toLowerCase().includes('fail');
        this.terminalService.addLog({
          sender: 'system',
          text: isError ? output : 'Task completed successfully',
          type: isError ? 'error' : 'success'
        });
      },
      error: (err) => {
        logEntry.executing = false;
        this.isExecuting = false;
        this.terminalService.addLog({ sender: 'system', text: 'Execution Failed: ' + err.message, type: 'error' });
      }
    });
  }
}
