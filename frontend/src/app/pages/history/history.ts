import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StatusBadge } from '../../components/status-badge/status-badge';
import { TaskService } from '../../services/task.service';
import { TaskHistoryItem } from '../../models/task.model';

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [CommonModule, StatusBadge],
  templateUrl: './history.html',
  styleUrl: './history.scss',
})
export class History implements OnInit {
  tasks: TaskHistoryItem[] = [];
  loading = false;
  errorMessage = '';

  constructor(
    private taskService: TaskService,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.loadHistory();
  }

  loadHistory() {
    this.loading = true;
    this.errorMessage = '';
    this.taskService.getTaskHistory().subscribe({
      next: (tasks) => {
        this.tasks = tasks;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        this.errorMessage = error?.message || 'Task history could not be loaded.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }
}
