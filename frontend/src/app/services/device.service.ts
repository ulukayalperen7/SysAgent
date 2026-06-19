import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { ApiResponse } from '../models/api-response.model';
import { environment } from '../../environments/environment';

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
}
