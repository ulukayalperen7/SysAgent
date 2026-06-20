import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { ApiResponse } from '../models/api-response.model';
import { environment } from '../../environments/environment';
import { TaskHistoryItem } from '../models/task.model';

export interface Device {
    id: number;
    name: string;
    ipAddress: string; // added to match backend
    status: string;
    cpuUsage: number | null; // changed from cpu
    ramUsage: number | null; // changed from ram
    type: string;
    lastSeen?: string; // Added to match backend
}

export interface DeviceRegistrationToken {
    token: string;
    expiresAt: string;
    bootstrapCommand: string;
}

export interface DeviceContextSnapshot {
    id: string;
    deviceId: number;
    activeWindowTitle?: string | null;
    activeProcessName?: string | null;
    screenWidth?: number | null;
    screenHeight?: number | null;
    screenshotMimeType?: string | null;
    screenshotBase64?: string | null;
    metadataJson?: string | null;
    capturedAt?: string | null;
    createdAt?: string | null;
}

@Injectable({
    providedIn: 'root'
})
export class DeviceService {
    private apiUrl = `${environment.apiUrl}/devices`;

    constructor(private http: HttpClient) { }

    getDevices(): Observable<Device[]> {
        return this.http.get<ApiResponse<Device[]>>(this.apiUrl).pipe(
            map(response => response.data ?? []),
            catchError(error => {
                console.error('DeviceService: Error fetching devices', error);
                throw error;
            })
        );
    }

    createRegistrationToken(label: string): Observable<DeviceRegistrationToken> {
        return this.http.post<ApiResponse<DeviceRegistrationToken>>(`${this.apiUrl}/registration-token`, { label }).pipe(
            map(response => {
                if (response.status !== 'SUCCESS' || !response.data) {
                    throw new Error(response.message || 'Device registration token could not be created.');
                }
                return response.data;
            }),
            catchError(error => {
                console.error('DeviceService: Error creating registration token', error);
                throw error;
            })
        );
    }

    getDeviceTasks(deviceId: number): Observable<TaskHistoryItem[]> {
        return this.http.get<ApiResponse<TaskHistoryItem[]>>(`${this.apiUrl}/${deviceId}/tasks`).pipe(
            map(response => {
                if (response.status !== 'SUCCESS' || !response.data) {
                    throw new Error(response.message || 'Device task history could not be loaded.');
                }
                return response.data;
            }),
            catchError(error => {
                console.error('DeviceService: Error loading device tasks', error);
                throw error;
            })
        );
    }

    getLatestDeviceContext(deviceId: number): Observable<DeviceContextSnapshot | null> {
        return this.http.get<ApiResponse<DeviceContextSnapshot | null>>(`${this.apiUrl}/${deviceId}/context/latest`).pipe(
            map(response => response.data ?? null),
            catchError(error => {
                console.error('DeviceService: Error loading device context', error);
                throw error;
            })
        );
    }
}
