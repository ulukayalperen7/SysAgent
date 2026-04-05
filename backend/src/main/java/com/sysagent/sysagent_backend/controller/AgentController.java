package com.sysagent.sysagent_backend.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.sysagent.sysagent_backend.adapter.AiAgentAdapter;
import com.sysagent.sysagent_backend.model.dto.AgentIntentRequestDto;
import com.sysagent.sysagent_backend.model.dto.AgentIntentResponseDto;
import com.sysagent.sysagent_backend.model.entity.TaskEntity;
import com.sysagent.sysagent_backend.model.response.ApiResponse;
import com.sysagent.sysagent_backend.service.TaskService;

import com.sysagent.sysagent_backend.service.SystemMetricsService;
import com.sysagent.sysagent_backend.model.dto.SystemMetricsDto;
import com.sysagent.sysagent_backend.security.PromptSanitizer;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j

@RestController
@RequestMapping("/api/agent")
@RequiredArgsConstructor
@CrossOrigin(origins = "*") // Allow Angular frontend to call this
public class AgentController {

    private final TaskService taskService;
    private final AiAgentAdapter aiAgentAdapter;
    private final SystemMetricsService systemMetricsService;

    @PostMapping("/process")
    public ResponseEntity<ApiResponse<AgentIntentResponseDto>> processUserIntent(@RequestBody AgentIntentRequestDto request) {
        log.info("Received new natural language intent from frontend: {}", request.getIntent());

        if (request.getIntent() == null || request.getIntent().trim().isEmpty()) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(ApiResponse.error("Intent cannot be empty."));
        }

        String sanitizedIntent = PromptSanitizer.sanitize(request.getIntent());
        if (sanitizedIntent.isEmpty()) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(ApiResponse.error("Intent cannot be empty."));
        }

        // 1. Immediately create a PENDING task in the DB to track this command
        // For Phase 2, we use a hardcoded default ownerId. This will be dynamic in Phase 3.
        TaskEntity task = taskService.createTask(sanitizedIntent, "test-user-1");

        // 2. Fetch the current system metrics from the Local Node (OSHI)
        SystemMetricsDto currentMetrics = systemMetricsService.collectMetrics();

        // 3. Pass the intent and metrics to our AI Adapter
        AgentIntentResponseDto response = aiAgentAdapter.analyzeIntent(task.getId(), sanitizedIntent, currentMetrics);
        
        // 4. Save the generated script back to the DB so it can be executed later via /execute
        if (response.getScript() != null && !response.getScript().isEmpty()) {
            taskService.updateTaskScript(task.getId(), response.getScript());
        }
        
        return ResponseEntity.ok(ApiResponse.<AgentIntentResponseDto>builder()
                .status("SUCCESS")
                .message("Agent processed intent successfully")
                .data(response)
                .build());
    }
}
