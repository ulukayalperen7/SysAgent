package com.sysagent.sysagent_backend.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.sysagent.sysagent_backend.adapter.AiAgentAdapter;
import com.sysagent.sysagent_backend.model.dto.AgentIntentRequestDto;
import com.sysagent.sysagent_backend.model.dto.AgentIntentResponseDto;
import com.sysagent.sysagent_backend.model.dto.AiRuntimeStatusDto;
import com.sysagent.sysagent_backend.model.dto.SystemMetricsDto;
import com.sysagent.sysagent_backend.model.entity.TaskEntity;
import com.sysagent.sysagent_backend.model.enums.TaskStatus;
import com.sysagent.sysagent_backend.model.response.ApiResponse;
import com.sysagent.sysagent_backend.security.PromptSanitizer;
import com.sysagent.sysagent_backend.service.SystemMetricsService;
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
    private final SystemMetricsService systemMetricsService;

    @GetMapping("/runtime-status")
    public ResponseEntity<ApiResponse<AiRuntimeStatusDto>> getRuntimeStatus() {
        AiRuntimeStatusDto status = aiAgentAdapter.getRuntimeStatus();
        return ResponseEntity.ok(ApiResponse.success(status, "AI Engine runtime status loaded"));
    }

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

        // 1. Immediately create a PENDING task in the DB to track this command.
        // Spring Boot owns the task record because script execution later depends
        // on retrieving the approved script by task ID.
        TaskEntity task;
        try {
            task = taskService.createTask(sanitizedIntent, "test-user-1");
        } catch (Exception e) {
            log.error("Could not create task before AI analysis", e);
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                    .body(ApiResponse.error("Task database is unavailable. Please retry after the connection recovers."));
        }

        // 2. Fetch the current system metrics from the Local Node (OSHI)
        SystemMetricsDto currentMetrics = systemMetricsService.collectMetrics();

        // 3. Pass the intent and metrics to our AI Adapter
        String threadId = request.getThreadId();
        if (threadId == null || threadId.isBlank()) {
            threadId = "thread_" + task.getId();
        }

        AgentIntentResponseDto response = aiAgentAdapter.analyzeIntent(task.getId(), sanitizedIntent, currentMetrics, threadId);
        
        // 4. Persist generated scripts before Angular is allowed to show approval.
        // If this write fails, returning the script would create a broken approval
        // flow because /execute loads the script from the task table.
        if (!persistAnalysisResult(task.getId(), response)) {
            response.setScript(null);
            response.setExplanation(
                    appendSystemNote(
                            response.getExplanation(),
                            "I prepared the answer, but the task database timed out while saving it. "
                                    + "Please retry this command so approval/execution can be tracked safely."));
        }
        
        return ResponseEntity.ok(ApiResponse.<AgentIntentResponseDto>builder()
                .status("SUCCESS")
                .message("Agent processed intent successfully")
                .data(response)
                .build());
    }

    private boolean persistAnalysisResult(String taskId, AgentIntentResponseDto response) {
        try {
            if (response.getScript() != null && !response.getScript().isEmpty()) {
                taskService.updateTaskScript(taskId, response.getScript());
            }
            if (response.getExplanation() != null) {
                taskService.updateTaskStatus(taskId, TaskStatus.ANALYZED, null);
            }
            return true;
        } catch (Exception e) {
            log.error("Could not persist AI analysis result for task {}", taskId, e);
            return false;
        }
    }

    private String appendSystemNote(String explanation, String note) {
        String base = explanation == null ? "" : explanation.trim();
        if (base.isEmpty()) {
            return "System Note:\n" + note;
        }
        return base + "\n\nSystem Note:\n" + note;
    }
}
