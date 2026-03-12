import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule, Monitor, Laptop, Server, Copy } from 'lucide-angular';
import { DeviceService, Device } from '../../services/device.service';

@Component({
  selector: 'app-devices',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './devices.html',
  styleUrl: './devices.scss',
})
export class Devices implements OnInit {
  showAddModal = false;
  devices: Device[] = [];
  generatedToken = '';

  constructor(
    private deviceService: DeviceService,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.fetchDevices();
  }

  private fetchDevices() {
    this.deviceService.getDevices().subscribe({
      next: (data) => {
        this.devices = data;
        this.cdr.detectChanges(); // Force UI update
      },
      error: (err) => {
        console.error('Failed to fetch devices:', err);
      }
    });
  }

  openAddDevice() {
    this.generatedToken = 'SYSA-' + Math.random().toString(36).substring(2, 6).toUpperCase() + '-44';
    this.showAddModal = true;
  }

  closeModal() {
    this.showAddModal = false;
  }
}
