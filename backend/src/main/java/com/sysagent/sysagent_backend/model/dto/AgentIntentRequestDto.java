package com.sysagent.sysagent_backend.model.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Request payload for AI-driven intent analysis.
 * Contains the natural language command that the user wants to execute.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class AgentIntentRequestDto {
    
    /**
     * The task description or command in natural language (e.g., "Install Docker on this server").
     */
    private String intent;
    
    /**
     * The ID of the target device where this intent should be executed.
     */
    private Long deviceId;
}
