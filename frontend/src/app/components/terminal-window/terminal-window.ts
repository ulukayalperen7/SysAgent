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
    { sender: 'system', text: 'SysAgent v1.0 başlatıldı...', type: 'info' },
    { sender: 'system', text: 'Sistem metrikleri okunuyor...', type: 'info' },
    { sender: 'system', text: 'Ajan hazır. Komut bekleniyor...', type: 'success' }
  ];

  onCommandEnter(event: any) {
    const command = event.target.value.trim();
    if (command) {
      this.logs.push({ sender: 'user', text: `> ${command}` });
      
      setTimeout(() => {
        this.logs.push({ sender: 'system', text: 'İşlem AI tarafından planlanacak: Dry-Run bekleniyor...', type: 'warning' });
      }, 500);

      event.target.value = '';
    }
  }
}