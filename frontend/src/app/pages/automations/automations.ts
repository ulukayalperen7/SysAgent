import { Component } from '@angular/core';

import { CommonModule } from '@angular/common';
import { LucideAngularModule, FolderOpen, Clock, Zap, FolderSearch, ShieldCheck, Blocks } from 'lucide-angular';

@Component({
  selector: 'app-automations',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './automations.html',
  styleUrl: './automations.scss',
})
export class Automations {
  activeRules = [
    {
      id: 'rule_1',
      name: 'Clean Big Downloads',
      trigger: { type: 'condition', icon: 'folder-open', text: "Folder 'Downloads' > 1GB" },
      action: { type: 'agent', icon: 'folder-search', text: "Run 'File Sorcerer' on 'Main Rig (Windows 11)'" },
      status: 'active'
    },
    {
      id: 'rule_2',
      name: 'Weekly Privacy Sweep',
      trigger: { type: 'schedule', icon: 'clock', text: "Every Friday at 18:00" },
      action: { type: 'agent', icon: 'shield-check', text: "Run 'Privacy Guardian' on 'Work MacBook'" },
      status: 'active'
    },
    {
      id: 'rule_3',
      name: 'Auto-Docker Setup',
      trigger: { type: 'event', icon: 'zap', text: "When 'docker-compose.yml' is downloaded" },
      action: { type: 'agent', icon: 'blocks', text: "Run 'Dev-Env Builder' on 'Main Rig'" },
      status: 'paused'
    }
  ];

  toggleRule(rule: any) {
    rule.status = rule.status === 'active' ? 'paused' : 'active';
  }
}
