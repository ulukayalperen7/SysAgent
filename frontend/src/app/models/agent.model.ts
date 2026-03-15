export interface AgentIntentRequest {
    intent: string;
    targetDeviceId?: number;
}

export interface AgentIntentResponse {
    taskId: string;
    script: string;       // Matches backend
    explanation: string;  // Matches backend
    confidenceScore?: number;
}
