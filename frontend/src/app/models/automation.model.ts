export interface AutomationRule {
    id: string;
    ownerId: string;
    name: string;
    description?: string | null;
    triggerType: string;
    triggerSummary: string;
    actionType: string;
    actionSummary: string;
    targetAgentSlug?: string | null;
    targetDeviceScope: string;
    status: string;
    requiresApproval: boolean;
    riskLevel: string;
    scheduleExpression?: string | null;
    lastRunAt?: string | null;
    nextRunAt?: string | null;
    createdAt?: string | null;
    updatedAt?: string | null;
}
