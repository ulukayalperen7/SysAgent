import { Component } from '@angular/core';
import { CommonModule } from '@angular/common'; 

@Component({
  selector: 'app-terminal-window',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './terminal-window.html',
  styleUrl: './terminal-window.scss'
})
export class TerminalWindow {
  
  logs: { sender: string, text: string, type?: string }[] = [
    { sender: 'system', text: 'SysAgent v0.1 bootstrapped on localhost.', type: 'info' },
    { sender: 'system', text: 'Monitoring local system metrics...', type: 'info' },
    { sender: 'system', text: 'Agent ready. Type a command or natural language intent.', type: 'success' }
  ];

  onCommandEnter(event: any) {
    const command = event.target.value.trim();
    if (command) {
      this.logs.push({ sender: 'user', text: `> ${command}` });
      
      setTimeout(() => {
        this.logs.push({
          sender: 'system',
          text: 'Planned command will be generated as a dry-run script. Awaiting UI approval...',
          type: 'warning'
        });
      }, 500);

      event.target.value = '';
    }
  }
}