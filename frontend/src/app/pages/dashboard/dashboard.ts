import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MetricCardComponent } from '../../components/metric-card/metric-card';
import { TerminalWindow } from '../../components/terminal-window/terminal-window';
import { MetricsService } from '../../services/metrics.service';
import { SystemMetrics } from '../../models/metrics.model';
import { BytesPipe } from '../../pipes/bytes.pipe';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, MetricCardComponent, TerminalWindow, BytesPipe],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
})
export class Dashboard implements OnInit, OnDestroy {
  metrics: SystemMetrics | null = null;
  private metricsSub?: Subscription;

  constructor(
    private metricsService: MetricsService,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.metricsSub = this.metricsService.systemMetrics$.subscribe({
      next: (data) => {
        this.metrics = data;
        this.cdr.detectChanges(); // Force UI update for zoneless Angular
      },
      error: (err) => {
        console.error('Failed to get real-time metrics:', err);
      }
    });
  }

  ngOnDestroy() {
    if (this.metricsSub) {
      this.metricsSub.unsubscribe();
    }
  }
}
