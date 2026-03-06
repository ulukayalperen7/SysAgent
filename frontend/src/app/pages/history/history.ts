import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StatusBadge } from '../../components/status-badge/status-badge';
import { ActionBtn } from '../../components/action-btn/action-btn';

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [CommonModule, StatusBadge, ActionBtn],
  templateUrl: './history.html',
  styleUrl: './history.scss',
})
export class History {
  tasks = [
    { id: 'TSK-402', date: '2026-03-06 23:15', intent: 'Clean temp files', status: 'completed', canUndo: true },
    { id: 'TSK-403', date: '2026-03-06 23:45', intent: 'Kill port 8080 process', status: 'rolled_back', canUndo: false },
    { id: 'TSK-404', date: '2026-03-07 00:10', intent: 'Docker system prune', status: 'pending', canUndo: false }
  ] as any[];

  handleUndo(taskId: string) {
    const task = this.tasks.find(t => t.id === taskId);
    if (task) {
      task.status = 'rolled_back';
      task.canUndo = false;
    }
  }
}
