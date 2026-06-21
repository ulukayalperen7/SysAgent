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
    targetDeviceId?: number | null;
    intent: string;
    status: TaskHistoryStatus;
    timestamp: string;
    hasScript: boolean;
    hasRollbackScript: boolean;
    canUndo: boolean;
    remoteCommandId?: string | null;
    remoteCommandStatus?: NodeCommandLifecycleStatus | null;
    remoteCommandUpdatedAt?: string | null;
    remoteCommandHasOutput: boolean;
    remoteCommandHasError: boolean;
}

export type NodeCommandLifecycleStatus =
    | 'QUEUED'
    | 'CLAIMED'
    | 'COMPLETED'
    | 'FAILED';

export interface NodeCommandStatus {
    id: string;
    taskId: string;
    deviceId: number;
    status: NodeCommandLifecycleStatus;
    output?: string | null;
    error?: string | null;
    createdAt: string;
    claimedAt?: string | null;
    completedAt?: string | null;
}

export interface TaskPostCommandContext {
    id: string;
    deviceId: number;
    activeWindowTitle?: string | null;
    activeProcessName?: string | null;
    screenWidth?: number | null;
    screenHeight?: number | null;
    screenshotMimeType?: string | null;
    screenshotBase64?: string | null;
    metadataJson?: string | null;
    capturedAt?: string | null;
    createdAt?: string | null;
}

export interface PostCommandVerification {
    taskId: string;
    status: 'verified' | 'failed' | 'uncertain' | string;
    reason?: string | null;
    screenSummary?: string | null;
}
