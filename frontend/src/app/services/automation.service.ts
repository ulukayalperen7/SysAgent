import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import { environment } from '../../environments/environment';
import { ApiResponse } from '../models/api-response.model';
import { AutomationRule } from '../models/automation.model';

@Injectable({
    providedIn: 'root'
})
export class AutomationService {
    private apiUrl = `${environment.apiUrl}/automations`;

    constructor(private http: HttpClient) { }

    getRules(): Observable<AutomationRule[]> {
        return this.http.get<ApiResponse<AutomationRule[]>>(this.apiUrl).pipe(
            map(response => {
                if (response.status !== 'SUCCESS' || !response.data) {
                    throw new Error(response.message || 'Automation response did not include usable data.');
                }
                return response.data;
            }),
            catchError(error => {
                console.error('AutomationService: Error loading automation rules', error);
                throw error;
            })
        );
    }
}
