import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { DeviceService, Device } from '../../services/device.service';

@Component({
  selector: 'app-devices',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './devices.html',
  styleUrl: './devices.scss',
})
export class Devices implements OnInit {
  devices: Device[] = [];
  loading = false;
  errorMessage = '';

  constructor(
    private deviceService: DeviceService,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.fetchDevices();
  }

  private fetchDevices() {
    this.loading = true;
    this.errorMessage = '';
    this.deviceService.getDevices().subscribe({
      next: (data) => {
        this.devices = data;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Failed to fetch devices:', err);
        this.errorMessage = err?.message || 'Devices could not be loaded.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }
}
