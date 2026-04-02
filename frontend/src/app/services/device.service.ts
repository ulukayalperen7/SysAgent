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
    cpuUsage: number; // changed from cpu
    ramUsage: number; // changed from ram
    type: string;
    lastSeen?: string; // Added to match backend
}

@Injectable({
    providedIn: 'root'
})
export class DeviceService {
    private apiUrl = `${environment.apiUrl}/devices`;

    constructor(private http: HttpClient) { }

    getDevices(): Observable<Device[]> {
        return this.http.get<ApiResponse<Device[]>>(this.apiUrl).pipe(
            map(response => response.data),
            catchError(error => {
                console.error('DeviceService: Error fetching devices', error);
                throw error;
            })
        );
    }
}
