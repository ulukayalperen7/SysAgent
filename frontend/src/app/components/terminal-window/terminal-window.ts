import { Component, ElementRef, ViewChild, AfterViewChecked, ChangeDetectorRef, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AgentService } from '../../services/agent.service';
import { TerminalService, TerminalLog } from '../../services/terminal.service';
import { Device, DeviceService } from '../../services/device.service';
import { AgentIntentResponse, TaskExecutionResponse } from '../../models/agent.model';
import { ApiResponse } from '../../models/api-response.model';

// Maximum number of characters a user can send in one message
const MAX_PROMPT_LENGTH = 4000;

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
  devices: Device[] = [];
  selectedDeviceId: number | null = null;
  private readonly threadId = this.getOrCreateThreadId();

  private shouldScrollToBottom = false;

  constructor(
    private agentService: AgentService,
    private deviceService: DeviceService,
    private terminalService: TerminalService,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit(): void {
    this.terminalService.logs$.subscribe(logs => {
      this.shouldScrollToBottom = true;
      this.cdr.detectChanges();
    });
    this.loadDevices();
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

    const targetName = this.getSelectedDeviceName();
    this.terminalService.addLog({ sender: 'user', text: `[${targetName}] > ${command}` });
    inputElement.value = '';
    this.isThinking = true;

    this.agentService.processIntent(command, this.threadId, this.selectedDeviceId).subscribe({
      next: (response: AgentIntentResponse) => {
        this.isThinking = false;
        this.terminalService.addLog({
          sender: 'ai',
          text: `> ${response.explanation}`,
          type: 'success'
        });

        if (response.script) {
          console.log('AI Response with pendingCount:', response.pendingCount);
          this.terminalService.addLog({
            sender: 'ai',
            text: `Recommended Action:`,
            script: response.script,
            taskId: response.taskId,
            targetDeviceId: this.selectedDeviceId,
            targetDeviceName: targetName,
            pendingCount: response.pendingCount ?? 0,  // carry queue info for auto-resume
            type: 'warning'
          });
        }
        setTimeout(() => inputElement.focus(), 100);
      },
      error: (err: any) => {
        this.isThinking = false;
        const message = this.extractApiErrorMessage(err, 'Connection lost. Please try again.');
        this.terminalService.addLog({ sender: 'system', text: message, type: 'error' });
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
      next: (response: ApiResponse<TaskExecutionResponse>) => {
        logEntry.executing = false;
        this.isExecuting = false;

        // Use the backend's explicit status — not string matching on output content
        if (response.status === 'SUCCESS') {
          logEntry.executed = true; // Hide button, show green badge

          // Only resume if the API told us there are pending tasks in the queue
          const hasPendingTasks = (logEntry.pendingCount ?? 0) > 0;
          if (hasPendingTasks) {
            this.terminalService.addLog({
              sender: 'system',
              text: 'Task completed successfully. Resuming queue...',
              type: 'success'
            });
            this.autoResumeQueue();
          } else {
            this.terminalService.addLog({
              sender: 'system',
              text: 'Task completed successfully.',
              type: 'success'
            });
          }
        } else {
          // WRITE/DELETE task failed — do NOT stop. Feed the error back to the AI for self-healing.
          const execError = response.data?.error || response.data?.output || response.message || 'Unknown execution error';
          this.terminalService.addLog({
            sender: 'system',
            text: `Script failed. Asking AI to self-correct...`,
            type: 'warning'
          });
          this.selfHealScript(execError, logEntry);
        }
      },
      error: (err: any) => {
        logEntry.executing = false;
        this.isExecuting = false;
        const message = this.extractApiErrorMessage(err, 'Execution failed: Unable to reach the host system.');
        this.terminalService.addLog({
          sender: 'system',
          text: message,
          type: 'error'
        });
      }
    });
  }

  private autoResumeQueue() {
    this.isThinking = true;
    this.agentService.processIntent("continue", this.threadId, this.selectedDeviceId).subscribe({
      next: (response: AgentIntentResponse) => {
        this.isThinking = false;

        // If the AI returned explanations for the next steps
        if (response.explanation && response.explanation.trim() !== '') {
          this.terminalService.addLog({
            sender: 'ai',
            text: `> ${response.explanation}`,
            type: 'success'
          });
        }

        if (response.script) {
          this.terminalService.addLog({
            sender: 'ai',
            text: `Recommended Action:`,
            script: response.script,
            taskId: response.taskId,
            targetDeviceId: this.selectedDeviceId,
            targetDeviceName: this.getSelectedDeviceName(),
            pendingCount: response.pendingCount ?? 0,
            type: 'warning'
          });
        }
      },
      error: (err: any) => {
        this.isThinking = false;
        this.terminalService.addLog({
          sender: 'system',
          text: this.extractApiErrorMessage(err, 'Queue resume failed. Please type continue to retry.'),
          type: 'error'
        });
      }
    });
  }

  /**
   * Called when a WRITE/DELETE script execution fails.
   * Sends the exact error back to the AI as context so it can reason about
   * the failure, fix the command, and re-present a new Approve button.
   */
  private selfHealScript(errorOutput: string, failedLogEntry: any) {
    this.isThinking = true;
    // Mark old entry as failed so user can see it
    failedLogEntry.executed = true;
    failedLogEntry.failed = true;

    const failedScript = this.truncateForAiContext(failedLogEntry.script || 'UNKNOWN', 1200);
    const errorContext = this.truncateForAiContext(errorOutput, 1200);
    const healPrompt = `EXEC_FAILED: The previous script failed.

Previous script:
${failedScript}

Execution error:
${errorContext}

Please analyze the exact error, generate a corrected minimal script for the same current step, and do not repeat the same failed strategy.`;

    const targetDeviceId = failedLogEntry.targetDeviceId ?? this.selectedDeviceId;
    const targetDeviceName = failedLogEntry.targetDeviceName ?? this.getSelectedDeviceName();

    this.agentService.processIntent(healPrompt, this.threadId, targetDeviceId).subscribe({
      next: (response: AgentIntentResponse) => {
        this.isThinking = false;
        if (response.explanation && response.explanation.trim() !== '') {
          this.terminalService.addLog({
            sender: 'ai',
            text: `> ${response.explanation}`,
            type: 'success'
          });
        }
        if (response.script) {
          this.terminalService.addLog({
            sender: 'ai',
            text: `Recommended Action (Corrected):`,
            script: response.script,
            taskId: response.taskId,
            targetDeviceId,
            targetDeviceName,
            pendingCount: response.pendingCount ?? 0,
            type: 'warning'
          });
        }
      },
      error: (err: any) => {
        this.isThinking = false;
        this.terminalService.addLog({
          sender: 'system',
          text: this.extractApiErrorMessage(err, 'Self-healing failed: Could not reach the AI engine.'),
          type: 'error'
        });
      }
    });
  }

  private extractApiErrorMessage(err: any, fallback: string): string {
    const apiMessage = err?.error?.message || err?.error?.data || err?.message;
    if (!apiMessage) {
      return fallback;
    }
    return `Request failed: ${apiMessage}`;
  }

  private loadDevices(): void {
    this.deviceService.getDevices().subscribe({
      next: devices => {
        this.devices = devices;
      },
      error: err => {
        this.terminalService.addLog({
          sender: 'system',
          text: this.extractApiErrorMessage(err, 'Device list could not be loaded. Local backend mode is still available.'),
          type: 'error'
        });
      }
    });
  }

  onDeviceChange(deviceId: number | null): void {
    this.selectedDeviceId = deviceId;
    this.terminalService.addLog({
      sender: 'system',
      text: `Target changed to ${this.getSelectedDeviceName()}.`,
      type: 'info'
    });
  }

  isRemoteLog(logEntry: TerminalLog): boolean {
    return !!logEntry.targetDeviceId;
  }

  private getSelectedDeviceName(): string {
    if (!this.selectedDeviceId) {
      return 'Local backend';
    }
    const device = this.devices.find(item => item.id === this.selectedDeviceId);
    return device ? device.name : `Device #${this.selectedDeviceId}`;
  }

  private truncateForAiContext(value: string, maxChars: number): string {
    if (!value || value.length <= maxChars) {
      return value;
    }
    return `${value.slice(0, maxChars)}\n...[truncated]`;
  }

  private getOrCreateThreadId(): string {
    const storageKey = 'sysagent_terminal_thread_id';
    const existing = localStorage.getItem(storageKey);
    if (existing && existing.trim().length > 0) {
      return existing;
    }

    const created = `sysagent-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
    localStorage.setItem(storageKey, created);
    return created;
  }
}
