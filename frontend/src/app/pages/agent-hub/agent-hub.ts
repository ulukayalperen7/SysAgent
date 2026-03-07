import { Component } from '@angular/core';

import { CommonModule } from '@angular/common';
import { LucideAngularModule, FolderSearch, Blocks, ScanSearch, ShieldCheck, Download, Search } from 'lucide-angular';

@Component({
  selector: 'app-agent-hub',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './agent-hub.html',
  styleUrl: './agent-hub.scss',
})
export class AgentHub {
  agents = [
    {
      id: 'agent_1',
      name: 'File Sorcerer',
      description: 'Autonomously organizes cluttered folders using NLP content analysis.',
      icon: 'folder-search',
      downloads: '12.4k',
      version: 'v2.1.0'
    },
    {
      id: 'agent_2',
      name: 'Dev-Env Builder',
      description: 'Installs and configures Docker, Node, and Git based on your project files instantly.',
      icon: 'blocks',
      downloads: '8.9k',
      version: 'v1.4.2'
    },
    {
      id: 'agent_3',
      name: 'Log Detective',
      description: 'Scans local crash reports locally and suggests automated code fixes.',
      icon: 'scan-search',
      downloads: '4.2k',
      version: 'v0.9.1-beta'
    },
    {
      id: 'agent_4',
      name: 'Privacy Guardian',
      description: 'Wipes tracking caches and sanitizes local data to protect your anonymity.',
      icon: 'shield-check',
      downloads: '22.1k',
      version: 'v3.0.0'
    }
  ];

  deployingAgent: string | null = null;

  deployAgent(agentId: string) {
    // Simulate deployment process visually
    this.deployingAgent = agentId;
    setTimeout(() => {
      this.deployingAgent = null;
      alert('Simulation: Agent deployed to node successfully!');
    }, 1500);
  }
}
