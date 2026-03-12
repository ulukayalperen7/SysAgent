import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { catchError } from 'rxjs/operators';

export interface Device {
    id: number;
    name: string;
    status: string;
    cpu: number;
    ram: number;
    type: string;
}

@Injectable({
    providedIn: 'root'
})
export class DeviceService {
    private apiUrl = 'http://localhost:8080/api/devices';

    constructor(private http: HttpClient) { }

    getDevices(): Observable<Device[]> {
        return this.http.get<Device[]>(this.apiUrl).pipe(
            catchError(error => {
                console.error('DeviceService: Error fetching devices', error);
                throw error;
            })
        );
    }
}
