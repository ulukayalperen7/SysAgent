import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-action-btn',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './action-btn.html',
  styleUrl: './action-btn.scss',
})
export class ActionBtn {
  @Input() label: string = 'Action';
  @Input() type: 'primary' | 'danger' | 'warning' | 'outline' = 'primary';
  @Output() onClick = new EventEmitter<void>();

  handleClick() {
    this.onClick.emit();
  }
}
