import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface TerminalLog {
    sender: string;
    text: string;
    type?: string;
    script?: string;
    taskId?: string;
    targetDeviceId?: number | null;
    targetDeviceName?: string;
    executing?: boolean;
    executed?: boolean; // Track if the action was successfully performed
    failed?: boolean;   // Track if the execution failed (for self-healing UI State)
    pendingCount?: number; // Number of tasks remaining in the queue
}

@Injectable({
    providedIn: 'root'
})
export class TerminalService {
    private _logs: TerminalLog[] = [
        { sender: 'system', text: 'SysAgent v0.1 bootstrapped on the backend host.', type: 'info' },
        { sender: 'system', text: 'Monitoring system metrics...', type: 'info' },
        { sender: 'system', text: 'Agent ready. Type a command or natural language intent.', type: 'success' }
    ];

    private logsSubject = new BehaviorSubject<TerminalLog[]>(this._logs);
    public logs$: Observable<TerminalLog[]> = this.logsSubject.asObservable();

    get logs(): TerminalLog[] {
        return this._logs;
    }

    addLog(log: TerminalLog) {
        this._logs.push(log);
        this.logsSubject.next([...this._logs]);
    }

    clearLogs() {
        this._logs = [];
        this.logsSubject.next(this._logs);
    }
}
