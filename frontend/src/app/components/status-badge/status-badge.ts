import { Component, Input } from '@angular/core';
import { CommonModule, UpperCasePipe } from '@angular/common';

@Component({
  selector: 'app-status-badge',
  standalone: true,
  imports: [CommonModule, UpperCasePipe],
  templateUrl: './status-badge.html',
  styleUrl: './status-badge.scss',
})
export class StatusBadge {
  @Input() status: 'completed' | 'pending' | 'analyzed' | 'in_progress' | 'rolled_back' | 'failed' | 'unknown' = 'pending';
}
