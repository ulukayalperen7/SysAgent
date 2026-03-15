import { Component } from '@angular/core';
import { CommonModule } from '@angular/common'; 
import { FormsModule } from '@angular/forms'; // Added Forms Module
import { AgentService } from '../../services/agent.service'; // Added Agent Service
import { AgentIntentResponse } from '../../models/agent.model';

@Component({
  selector: 'app-terminal-window',
  standalone: true,
  imports: [CommonModule, FormsModule], // Added FormsModule to imports
  templateUrl: './terminal-window.html',
  styleUrl: './terminal-window.scss'
})
export class TerminalWindow {
  
  logs: { sender: string, text: string, type?: string, script?: string }[] = [ // Added script optional property
    { sender: 'system', text: 'SysAgent v0.1 bootstrapped on localhost.', type: 'info' },
    { sender: 'system', text: 'Monitoring local system metrics...', type: 'info' },
    { sender: 'system', text: 'Agent ready. Type a command or natural language intent.', type: 'success' }
  ];

  constructor(private agentService: AgentService) {} // Inject AgentService

  onCommandEnter(event: any) {
    const command = event.target.value.trim();
    if (command) {
      // 1. Log user command instantly
      this.logs.push({ sender: 'user', text: `> ${command}` });
      const inputElement = event.target;
      inputElement.value = ''; // Clear input
      inputElement.disabled = true; // Disable input while processing

      this.logs.push({ sender: 'system', text: 'Processing intent with AI Agent...', type: 'info' });

      // 2. Call Backend Agent Service
      this.agentService.processIntent(command).subscribe({
        next: (response: AgentIntentResponse) => {
            // Remove the temporary "processing" log if you want, or just append
            this.logs.push({ 
                sender: 'ai', 
                text: `Analysis: ${response.explanation}`, // Updated property
                type: 'success' 
            });

            if (response.script) { // Updated property
                this.logs.push({ 
                    sender: 'ai', 
                    text: `Generated Script:\n`, 
                    script: response.script,
                    type: 'warning' 
                });
            }
            
            inputElement.disabled = false;
            setTimeout(() => inputElement.focus(), 100);
        },
        error: (err) => {
            this.logs.push({ sender: 'system', text: 'Error connecting to Agent backend.', type: 'error' });
            console.error(err);
            inputElement.disabled = false;
            setTimeout(() => inputElement.focus(), 100);
        }
      });
    }
  }
}