import { ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { LucideAngularModule } from 'lucide-angular';

import { AgentService } from '../../services/agent.service';
import { AiRuntimeStatus, RuntimeDependencyStatus } from '../../models/agent.model';

interface DependencyRow extends RuntimeDependencyStatus {
  name: string;
}

@Component({
  selector: 'app-agent-hub',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  templateUrl: './agent-hub.html',
  styleUrl: './agent-hub.scss',
})
export class AgentHub implements OnInit, OnDestroy {
  runtimeStatus: AiRuntimeStatus | null = null;
  loading = false;
  errorMessage = '';
  searchTerm = '';
  lastUpdated: Date | null = null;

  private statusSub?: Subscription;

  constructor(
    private agentService: AgentService,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.loadRuntimeStatus();
  }

  ngOnDestroy() {
    this.statusSub?.unsubscribe();
  }

  loadRuntimeStatus() {
    this.loading = true;
    this.errorMessage = '';
    this.statusSub?.unsubscribe();
    this.statusSub = this.agentService.getRuntimeStatus().subscribe({
      next: (status) => {
        this.runtimeStatus = status;
        this.lastUpdated = new Date();
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        this.errorMessage = error?.message || 'Runtime status could not be loaded.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  get dependencyRows(): DependencyRow[] {
    const dependencies = this.runtimeStatus?.runtime?.dependencies || {};
    const query = this.searchTerm.trim().toLowerCase();
    return Object.entries(dependencies)
      .map(([name, dependency]) => ({ name, ...dependency }))
      .filter(row => this.matchesQuery([row.name, row.module, row.purpose], query))
      .sort((a, b) => Number(b.required) - Number(a.required) || a.name.localeCompare(b.name));
  }

  get visibleTools(): string[] {
    return this.filterStrings(this.runtimeStatus?.mcp?.tools || []);
  }

  get visiblePromptAgents(): string[] {
    return this.filterStrings(this.runtimeStatus?.agentHub?.promptAgents || []);
  }

  get missingCount(): number {
    return (this.runtimeStatus?.runtime?.requiredMissing?.length || 0)
      + (this.runtimeStatus?.runtime?.optionalMissing?.length || 0);
  }

  private filterStrings(values: string[]): string[] {
    const query = this.searchTerm.trim().toLowerCase();
    return values
      .filter(value => this.matchesQuery([value], query))
      .sort((a, b) => a.localeCompare(b));
  }

  private matchesQuery(values: string[], query: string): boolean {
    if (!query) {
      return true;
    }
    return values.some(value => value.toLowerCase().includes(query));
  }
}
