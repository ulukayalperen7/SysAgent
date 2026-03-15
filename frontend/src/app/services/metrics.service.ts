import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { SystemMetrics } from '../models/metrics.model';
import { ApiResponse } from '../models/api-response.model';

@Injectable({
    providedIn: 'root'
})
export class MetricsService {
    private apiUrl = 'http://localhost:8080/api/metrics';

    constructor(private http: HttpClient) { }

    getSystemMetrics(): Observable<SystemMetrics> {
        return this.http.get<ApiResponse<SystemMetrics>>(this.apiUrl).pipe(
            map(response => response.data),
            catchError(error => {
                console.error('MetricsService: CRITICAL HTTP ERROR fetching metrics:', error);
                throw error;
            })
        );
    }
}
