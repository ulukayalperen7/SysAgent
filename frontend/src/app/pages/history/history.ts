import { ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription, timer } from 'rxjs';
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
export class History implements OnInit, OnDestroy {
  tasks: TaskHistoryItem[] = [];
  loading = false;
  errorMessage = '';
  private refreshSub?: Subscription;

  constructor(
    private taskService: TaskService,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.refreshSub = timer(0, 5000).subscribe(() => this.loadHistory());
  }

  ngOnDestroy() {
    this.refreshSub?.unsubscribe();
  }

  loadHistory() {
    this.loading = this.tasks.length === 0;
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
