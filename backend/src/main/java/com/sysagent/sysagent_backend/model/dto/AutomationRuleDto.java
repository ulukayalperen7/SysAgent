package com.sysagent.sysagent_backend.model.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AutomationRuleDto {
    private String id;
    private String ownerId;
    private String name;
    private String description;
    private String triggerType;
    private String triggerSummary;
    private String actionType;
    private String actionSummary;
    private String targetAgentSlug;
    private String targetDeviceScope;
    private String status;
    private boolean requiresApproval;
    private String riskLevel;
    private String scheduleExpression;
    private String lastRunAt;
    private String nextRunAt;
    private String createdAt;
    private String updatedAt;
}
