package com.sysagent.sysagent_backend.model.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Read-only Agent Hub profile view for operators and the Angular UI.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AgentProfileDto {
    private String id;
    private String slug;
    private String name;
    private String description;
    private String agentType;
    private String status;
    private String ownerId;
    private String defaultModelProvider;
    private String defaultModelName;
    private String riskCeiling;
    private boolean requiresApproval;
    private int activePromptVersions;
    private int allowedMcpTools;
    private String createdAt;
    private String updatedAt;
}
