import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { ApiResponse } from '../models/api-response.model';

export interface AuthUser {
    id: string;
    email: string;
    displayName?: string | null;
}

export interface AuthResponse {
    token: string;
    tokenType: string;
    expiresInSeconds: number;
    user: AuthUser;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
    private readonly apiUrl = `${environment.apiUrl}/auth`;
    private readonly tokenKey = 'sysagent_auth_token';
    private readonly userKey = 'sysagent_auth_user';
    private readonly userSubject = new BehaviorSubject<AuthUser | null>(this.loadStoredUser());

    readonly user$ = this.userSubject.asObservable();

    constructor(private http: HttpClient, private router: Router) { }

    get token(): string | null {
        return localStorage.getItem(this.tokenKey);
    }

    get currentUser(): AuthUser | null {
        return this.userSubject.value;
    }

    isAuthenticated(): boolean {
        return !!this.token && !!this.currentUser;
    }

    register(email: string, password: string, displayName: string): Observable<AuthResponse> {
        return this.http.post<ApiResponse<AuthResponse>>(`${this.apiUrl}/register`, { email, password, displayName }).pipe(
            map(this.unwrapAuthResponse),
            tap(response => this.storeSession(response))
        );
    }

    login(email: string, password: string): Observable<AuthResponse> {
        return this.http.post<ApiResponse<AuthResponse>>(`${this.apiUrl}/login`, { email, password }).pipe(
            map(this.unwrapAuthResponse),
            tap(response => this.storeSession(response))
        );
    }

    logout(): void {
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem(this.userKey);
        localStorage.removeItem('sysagent_terminal_thread_id');
        this.userSubject.next(null);
        this.router.navigate(['/login']);
    }

    private unwrapAuthResponse(response: ApiResponse<AuthResponse>): AuthResponse {
        if (response.status !== 'SUCCESS' || !response.data?.token) {
            throw new Error(response.message || 'Authentication failed.');
        }
        return response.data;
    }

    private storeSession(response: AuthResponse): void {
        localStorage.setItem(this.tokenKey, response.token);
        localStorage.setItem(this.userKey, JSON.stringify(response.user));
        this.userSubject.next(response.user);
    }

    private loadStoredUser(): AuthUser | null {
        const raw = localStorage.getItem(this.userKey);
        if (!raw) {
            return null;
        }
        try {
            return JSON.parse(raw) as AuthUser;
        } catch {
            localStorage.removeItem(this.userKey);
            return null;
        }
    }
}
