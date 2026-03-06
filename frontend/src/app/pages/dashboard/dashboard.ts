import { Component } from '@angular/core';
import { MetricCardComponent } from '../../components/metric-card/metric-card'; 
import { TerminalWindow } from '../../components/terminal-window/terminal-window'; 

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [MetricCardComponent,TerminalWindow],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
})
export class Dashboard {
  // ...dashboard container logic can be added here later...
}
