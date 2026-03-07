import { Component } from '@angular/core';

import { CommonModule } from '@angular/common';
import { LucideAngularModule, Monitor, Laptop, Server, Copy } from 'lucide-angular';

@Component({
  selector: 'app-devices',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './devices.html',
  styleUrl: './devices.scss',
})
export class Devices {
  showAddModal = false;

  devices = [
    {
      id: 1,
      name: 'Main Rig (Windows 11)',
      status: 'online',
      cpu: 34,
      ram: 45,
      type: 'windows',
    },
    {
      id: 2,
      name: 'Work MacBook (macOS Sonoma)',
      status: 'offline',
      cpu: 0,
      ram: 0,
      type: 'macos',
    },
  ];

  generatedToken = '';

  openAddDevice() {
    this.generatedToken = 'SYSA-' + Math.random().toString(36).substring(2, 6).toUpperCase() + '-44';
    this.showAddModal = true;
  }

  closeModal() {
    this.showAddModal = false;
  }
}
