import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MetricCardComponent } from '../../components/metric-card/metric-card';
import { TerminalWindow } from '../../components/terminal-window/terminal-window';
import { MetricsService } from '../../services/metrics.service';
import { SystemMetrics } from '../../models/metrics.model';
import { BytesPipe } from '../../pipes/bytes.pipe';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, MetricCardComponent, TerminalWindow, BytesPipe],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
})
export class Dashboard implements OnInit, OnDestroy {
  metrics: SystemMetrics | null = null;
  private intervalId: any;

  constructor(
    private metricsService: MetricsService,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.fetchMetrics();
    // Poll the API every 3 seconds
    this.intervalId = setInterval(() => {
      this.fetchMetrics();
    }, 3000);
  }

  ngOnDestroy() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
    }
  }

  private fetchMetrics() {
    this.metricsService.getSystemMetrics().subscribe({
      next: (data) => {
        this.metrics = data;
        this.cdr.detectChanges(); // Force UI update for zoneless Angular
      },
      error: (err) => {
        console.error('Failed to fetch metrics:', err);
      }
    });
  }
}
