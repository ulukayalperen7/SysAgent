import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-metric-card',
  standalone: true,
  templateUrl: './metric-card.html',
  styleUrl: './metric-card.scss'
})
export class MetricCardComponent {
  @Input() title: string = 'Metric';
  @Input() value: string = '0';
  @Input() unit: string = '%';
  @Input() color: string = '#00d2ff'; 
}