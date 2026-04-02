import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { ApiResponse } from '../models/api-response.model';
import { environment } from '../../environments/environment';
import { AgentIntentRequest, AgentIntentResponse } from '../models/agent.model';

@Injectable({
    providedIn: 'root'
})
export class AgentService {
    private apiUrl = `${environment.apiUrl}/agent`;

    constructor(private http: HttpClient) { }

    processIntent(intent: string): Observable<any> { // Update return type if needed
        const payload: AgentIntentRequest = { intent };
        return this.http.post<ApiResponse<AgentIntentResponse>>(`${this.apiUrl}/process`, payload).pipe(
            map(response => response.data),
            catchError(error => {
                console.error('AgentService: Error processing intent', error);
                throw error;
            })
        );
    }
}
