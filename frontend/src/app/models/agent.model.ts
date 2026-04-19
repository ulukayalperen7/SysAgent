export interface AgentIntentRequest {
    intent: string;
    targetDeviceId?: number;
}

export interface AgentIntentResponse {
    taskId: string;
    script: string;
    explanation: string;
    confidenceScore?: number;
    pendingCount?: number; // Number of tasks still queued after this response
}
