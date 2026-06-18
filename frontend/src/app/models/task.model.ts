export type TaskHistoryStatus =
    | 'pending'
    | 'analyzed'
    | 'in_progress'
    | 'completed'
    | 'rolled_back'
    | 'failed'
    | 'unknown';

export interface TaskHistoryItem {
    id: string;
    ownerId: string;
    intent: string;
    status: TaskHistoryStatus;
    timestamp: string;
    hasScript: boolean;
    hasRollbackScript: boolean;
    canUndo: boolean;
}
