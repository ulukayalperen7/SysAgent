package com.sysagent.sysagent_backend.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AgentIntentResponseDto {
    private String taskId;
    private String script;
    private String explanation;
}
