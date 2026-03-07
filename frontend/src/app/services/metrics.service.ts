import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { SystemMetrics } from '../models/metrics.model';

@Injectable({
    providedIn: 'root'
})
export class MetricsService {
    private apiUrl = 'http://localhost:8080/api/metrics';

    constructor(private http: HttpClient) { }

    getSystemMetrics(): Observable<SystemMetrics> {
        return this.http.get<SystemMetrics>(this.apiUrl).pipe(
            catchError(error => {
                console.error('MetricsService: CRITICAL HTTP ERROR fetching metrics:', error);
                throw error;
            })
        );
    }
}
