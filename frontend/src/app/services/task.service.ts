import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import { environment } from '../../environments/environment';
import { ApiResponse } from '../models/api-response.model';
import { NodeCommandStatus, TaskHistoryItem } from '../models/task.model';

@Injectable({
    providedIn: 'root'
})
export class TaskService {
    private apiUrl = `${environment.apiUrl}/tasks`;

    constructor(private http: HttpClient) { }

    getTaskHistory(): Observable<TaskHistoryItem[]> {
        return this.http.get<ApiResponse<TaskHistoryItem[]>>(this.apiUrl).pipe(
            map(response => {
                if (response.status !== 'SUCCESS' || !response.data) {
                    throw new Error(response.message || 'Task history response did not include usable data.');
                }
                return response.data;
            }),
            catchError(error => {
                console.error('TaskService: Error loading task history', error);
                throw error;
            })
        );
    }

    getRemoteCommandStatus(taskId: string): Observable<NodeCommandStatus | null> {
        return this.http.get<ApiResponse<NodeCommandStatus>>(`${this.apiUrl}/${taskId}/node-command`).pipe(
            map(response => {
                if (response.status !== 'SUCCESS') {
                    throw new Error(response.message || 'Remote command status response was not successful.');
                }
                return response.data ?? null;
            }),
            catchError(error => {
                console.error('TaskService: Error loading remote command status', error);
                throw error;
            })
        );
    }
}
