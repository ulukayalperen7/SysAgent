package com.sysagent.sysagent_backend.controller;

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

    @PostMapping("/process")
    public ResponseEntity<ApiResponse<AgentIntentResponseDto>> processUserIntent(@RequestBody AgentIntentRequestDto request) {
        log.info("Received new natural language intent from frontend: {}", request.getIntent());

        // 1. Immediately create a PENDING task in the DB to track this command
        TaskEntity task = taskService.createTask(request.getIntent());

        // 2. Pass the intent to our AI Adapter
        AgentIntentResponseDto response = aiAgentAdapter.analyzeIntent(task.getId(), request.getIntent());
        
        return ResponseEntity.ok(ApiResponse.<AgentIntentResponseDto>builder()
                .status("SUCCESS")
                .message("Agent processed intent successfully")
                .data(response)
                .build());
    }
}
