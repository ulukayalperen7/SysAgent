package com.sysagent.sysagent_backend.controller;

import com.sysagent.sysagent_backend.adapter.AiAgentAdapter;
import com.sysagent.sysagent_backend.model.AgentIntentRequestDto;
import com.sysagent.sysagent_backend.model.AgentIntentResponseDto;
import com.sysagent.sysagent_backend.model.TaskEntity;
import com.sysagent.sysagent_backend.service.TaskService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping("/api/agent")
@RequiredArgsConstructor
@CrossOrigin(origins = "*") // Allow Angular frontend to call this
public class AgentController {

    private final TaskService taskService;
    private final AiAgentAdapter aiAgentAdapter;

    @PostMapping("/intent")
    public ResponseEntity<AgentIntentResponseDto> submitIntent(@RequestBody AgentIntentRequestDto request) {
        log.info("Received new natural language intent from frontend: {}", request.getIntent());
        
        // 1. Immediately create a PENDING task in the DB to track this command
        TaskEntity task = taskService.createTask(request.getIntent());
        
        // 2. Pass the intent to our AI Adapter
        // For the MVP, this immediately returns a Mock generated script.
        // In the future, this Adapter will make an HTTP call to the Python microservice.
        AgentIntentResponseDto response = aiAgentAdapter.analyzeIntent(task.getId(), request.getIntent());
        
        return ResponseEntity.ok(response);
    }
}
