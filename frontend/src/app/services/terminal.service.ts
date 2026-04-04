import { Injectable } from '@angular/core';

export interface TerminalLog {
    sender: string;
    text: string;
    type?: string;
    script?: string;
    taskId?: string;
    executing?: boolean;
}

@Injectable({
    providedIn: 'root'
})
export class TerminalService {
    private _logs: TerminalLog[] = [
        { sender: 'system', text: 'SysAgent v0.1 bootstrapped on localhost.', type: 'info' },
        { sender: 'system', text: 'Monitoring local system metrics...', type: 'info' },
        { sender: 'system', text: 'Agent ready. Type a command or natural language intent.', type: 'success' }
    ];

    get logs(): TerminalLog[] {
        return this._logs;
    }

    addLog(log: TerminalLog) {
        this._logs.push(log);
    }

    clearLogs() {
        this._logs = [];
    }
}
