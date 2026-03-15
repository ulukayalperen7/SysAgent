package com.sysagent.sysagent_backend.adapter;

import com.sysagent.sysagent_backend.model.dto.AgentIntentResponseDto;

public interface AiAgentAdapter {
    AgentIntentResponseDto analyzeIntent(String taskId, String intent);
}
