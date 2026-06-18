export interface AgentIntentRequest {
    intent: string;
    targetDeviceId?: number;
    threadId?: string;
}

export interface AgentIntentResponse {
    taskId: string;
    script?: string | null;
    explanation: string;
    confidenceScore?: number;
    pendingCount?: number; // Number of tasks still queued after this response
}

export interface AiRuntimeStatus {
    runtime: RuntimeSummary;
    agentHub: AgentHubSummary;
    checkpoint: CheckpointSummary;
    mcp: McpSummary;
}

export interface RuntimeSummary {
    status: string;
    detail?: string | null;
    requiredMissing: string[];
    optionalMissing: string[];
    dependencies: Record<string, RuntimeDependencyStatus>;
}

export interface RuntimeDependencyStatus {
    module: string;
    required: boolean;
    available: boolean;
    purpose: string;
}

export interface AgentHubSummary {
    source: string;
    routeCount: number;
    promptAgents: string[];
}

export interface CheckpointSummary {
    configuredBackend: string;
    activeBackend: string;
    databaseUrlConfigured: boolean;
}

export interface McpSummary {
    available: boolean;
    mode: string;
    detail?: string | null;
    tools: string[];
}

export interface AgentProfile {
    id: string;
    slug: string;
    name: string;
    description?: string | null;
    agentType: string;
    status: string;
    ownerId?: string | null;
    defaultModelProvider?: string | null;
    defaultModelName?: string | null;
    riskCeiling: string;
    requiresApproval: boolean;
    activePromptVersions: number;
    allowedMcpTools: number;
    createdAt?: string | null;
    updatedAt?: string | null;
}
