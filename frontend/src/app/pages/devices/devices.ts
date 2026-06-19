import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { DeviceService, Device, DeviceRegistrationToken } from '../../services/device.service';
import { TaskHistoryItem } from '../../models/task.model';

@Component({
  selector: 'app-devices',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  templateUrl: './devices.html',
  styleUrl: './devices.scss',
})
export class Devices implements OnInit {
  devices: Device[] = [];
  loading = false;
  errorMessage = '';
  registrationLabel = '';
  registrationToken?: DeviceRegistrationToken;
  creatingToken = false;
  selectedDevice?: Device;
  deviceTasks: TaskHistoryItem[] = [];
  loadingTasks = false;
  taskErrorMessage = '';

  constructor(
    private deviceService: DeviceService,
    private router: Router,
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

  createRegistrationToken() {
    if (this.creatingToken) return;
    this.creatingToken = true;
    this.errorMessage = '';
    this.deviceService.createRegistrationToken(this.registrationLabel || 'New SysAgent node').subscribe({
      next: token => {
        this.registrationToken = token;
        this.creatingToken = false;
        this.cdr.detectChanges();
      },
      error: err => {
        this.errorMessage = err?.error?.message || err?.message || 'Device registration token could not be created.';
        this.creatingToken = false;
        this.cdr.detectChanges();
      }
    });
  }

  openTerminal(device: Device) {
    this.router.navigate(['/dashboard'], { queryParams: { deviceId: device.id } });
  }

  loadDeviceLogs(device: Device) {
    this.selectedDevice = device;
    this.loadingTasks = true;
    this.taskErrorMessage = '';
    this.deviceService.getDeviceTasks(device.id).subscribe({
      next: tasks => {
        this.deviceTasks = tasks;
        this.loadingTasks = false;
        this.cdr.detectChanges();
      },
      error: err => {
        this.taskErrorMessage = err?.message || 'Device logs could not be loaded.';
        this.loadingTasks = false;
        this.cdr.detectChanges();
      }
    });
  }

  remoteState(task: TaskHistoryItem): string {
    return task.remoteCommandStatus || (task.targetDeviceId ? 'PENDING' : 'LOCAL');
  }
}
