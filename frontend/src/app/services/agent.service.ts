import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { ApiResponse } from '../models/api-response.model';
import { environment } from '../../environments/environment';
import { AgentIntentRequest, AgentIntentResponse, AiRuntimeStatus } from '../models/agent.model';

@Injectable({
    providedIn: 'root'
})
export class AgentService {
    private apiUrl = `${environment.apiUrl}/agent`;

    constructor(private http: HttpClient) { }

    processIntent(intent: string, threadId?: string): Observable<AgentIntentResponse> {
        const payload: AgentIntentRequest = { intent, threadId };
        return this.http.post<ApiResponse<AgentIntentResponse>>(`${this.apiUrl}/process`, payload).pipe(
            map(response => {
                // The backend always wraps responses. Guard here so the terminal
                // never crashes on a malformed/empty API payload.
                if (response.status !== 'SUCCESS' || !response.data) {
                    throw new Error(response.message || 'Agent response did not include usable data.');
                }
                return response.data;
            }),
            catchError(error => {
                console.error('AgentService: Error processing intent', error);
                throw error;
            })
        );
    }

    getRuntimeStatus(): Observable<AiRuntimeStatus> {
        return this.http.get<ApiResponse<AiRuntimeStatus>>(`${this.apiUrl}/runtime-status`).pipe(
            map(response => {
                if (response.status !== 'SUCCESS' || !response.data) {
                    throw new Error(response.message || 'Runtime status response did not include usable data.');
                }
                return response.data;
            }),
            catchError(error => {
                console.error('AgentService: Error loading runtime status', error);
                throw error;
            })
        );
    }

    executeTask(taskId: string): Observable<ApiResponse<string>> {
        const tasksUrl = `${environment.apiUrl}/tasks`;
        return this.http.post<ApiResponse<string>>(`${tasksUrl}/${taskId}/execute`, {}).pipe(
            catchError(error => {
                console.error('AgentService: Error executing task', error);
                throw error;
            })
        );
    }
}
