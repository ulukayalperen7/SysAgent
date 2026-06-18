import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';

import { AutomationRule } from '../../models/automation.model';
import { AutomationService } from '../../services/automation.service';

@Component({
  selector: 'app-automations',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './automations.html',
  styleUrl: './automations.scss',
})
export class Automations implements OnInit {
  rules: AutomationRule[] = [];
  loading = false;
  errorMessage = '';

  constructor(
    private automationService: AutomationService,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.loadRules();
  }

  loadRules() {
    this.loading = true;
    this.errorMessage = '';
    this.automationService.getRules().subscribe({
      next: (rules) => {
        this.rules = rules;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        this.errorMessage = error?.message || 'Automation rules could not be loaded.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  triggerIcon(rule: AutomationRule): string {
    return {
      schedule: 'clock',
      condition: 'folder-open',
      event: 'zap',
      manual: 'mouse-pointer-click'
    }[rule.triggerType] || 'workflow';
  }

  actionIcon(rule: AutomationRule): string {
    return rule.actionType === 'agent' ? 'bot' : 'shield-check';
  }
}
