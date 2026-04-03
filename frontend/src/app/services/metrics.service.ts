import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { SystemMetrics } from '../models/metrics.model';
import { ApiResponse } from '../models/api-response.model';
import { Client } from '@stomp/stompjs';
import SockJS from 'sockjs-client';

@Injectable({
    providedIn: 'root'
})
export class MetricsService {
    private apiUrl = `${environment.apiUrl}/metrics`;
    
    private stompClient: Client | null = null;
    private systemMetricsSubject = new Subject<SystemMetrics>();
    
    // Observable that components can subscribe to for real-time updates
    public systemMetrics$ = this.systemMetricsSubject.asObservable();

    constructor(private http: HttpClient) { 
        this.initializeWebSocketConnection();
    }

    private initializeWebSocketConnection() {
        // Derive WebSocket URL from apiUrl (assuming apiUrl is like http://localhost:8080/api)
        // We need it to be http://localhost:8080/ws-metrics
        const wsUrl = environment.apiUrl.replace('/api', '') + '/ws-metrics';

        this.stompClient = new Client({
            // Use SockJS as the WebSocket factory since that's what backend uses (.withSockJS())
            webSocketFactory: () => new SockJS(wsUrl),
            reconnectDelay: 5000,
            debug: (str) => {
                // Uncomment to see STOMP debug logs
                // console.log(str);
            },
        });

        this.stompClient.onConnect = (frame) => {
            console.log('Connected to WebSocket for metrics');
            this.stompClient?.subscribe('/topic/system-metrics', (message) => {
                if (message.body) {
                    const metrics: SystemMetrics = JSON.parse(message.body);
                    // Push new data to subscribers
                    this.systemMetricsSubject.next(metrics);
                }
            });
        };

        this.stompClient.onStompError = (frame) => {
            console.error('Broker reported error: ' + frame.headers['message']);
            console.error('Additional details: ' + frame.body);
        };

        this.stompClient.activate();
    }

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
