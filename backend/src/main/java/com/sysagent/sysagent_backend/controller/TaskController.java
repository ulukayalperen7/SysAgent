package com.sysagent.sysagent_backend.controller;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.sysagent.sysagent_backend.model.entity.TaskEntity;
import com.sysagent.sysagent_backend.model.dto.TaskHistoryDto;
import com.sysagent.sysagent_backend.model.dto.TaskExecutionResponseDto;
import com.sysagent.sysagent_backend.model.dto.DeviceDto;
import com.sysagent.sysagent_backend.model.response.ApiResponse;
import com.sysagent.sysagent_backend.security.CurrentUserProvider;
import com.sysagent.sysagent_backend.security.ScriptPolicyValidator;
import com.sysagent.sysagent_backend.service.DeviceService;
import com.sysagent.sysagent_backend.service.NodeCommandService;
import com.sysagent.sysagent_backend.service.TaskService;
import com.sysagent.sysagent_backend.service.ScriptExecutionService;
import com.sysagent.sysagent_backend.model.enums.TaskStatus;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RestController
@RequestMapping("/api/tasks")
@RequiredArgsConstructor
@CrossOrigin(origins = "*") // Allow Angular frontend to call this
public class TaskController {

    private final TaskService taskService;
    private final ScriptExecutionService scriptExecutionService;
    private final CurrentUserProvider currentUserProvider;
    private final ScriptPolicyValidator scriptPolicyValidator;
    private final DeviceService deviceService;
    private final NodeCommandService nodeCommandService;

    @GetMapping
    public ResponseEntity<ApiResponse<List<TaskHistoryDto>>> getTaskHistory() {
        List<TaskHistoryDto> tasks = taskService.getTaskHistoryByOwner(currentUserProvider.getCurrentUserId());
        return ResponseEntity.ok(ApiResponse.<List<TaskHistoryDto>>builder()
                .status("SUCCESS")
                .message("Tasks fetched successfully")
                .data(tasks)
                .build());
    }

    @PostMapping("/{id}/execute")
    public ResponseEntity<ApiResponse<TaskExecutionResponseDto>> executeTask(@PathVariable("id") String taskId) {
        TaskEntity task = taskService.getTaskById(taskId);
        if (!currentUserProvider.getCurrentUserId().equals(task.getOwnerId())) {
            return ResponseEntity.status(403).body(ApiResponse.<TaskExecutionResponseDto>builder()
                    .status("ERROR")
                    .message("Task does not belong to the current user.")
                    .build());
        }
        
        if (task.getScript() == null || task.getScript().isBlank()) {
            return ResponseEntity.badRequest().body(ApiResponse.<TaskExecutionResponseDto>builder()
                    .status("ERROR")
                    .message("No script is associated with this task.")
                    .build());
        }

        // Guard: prevent re-executing a task that already ran
        if (task.getStatus() == TaskStatus.COMPLETED || task.getStatus() == TaskStatus.FAILED) {
            return ResponseEntity.badRequest().body(ApiResponse.<TaskExecutionResponseDto>builder()
                    .status("ERROR")
                    .message("Task has already been executed with status: " + task.getStatus())
                    .build());
        }

        DeviceDto targetDevice = null;
        String osName = System.getProperty("os.name", "unknown");
        if (task.getTargetDeviceId() != null) {
            try {
                targetDevice = deviceService.getOwnedDevice(task.getTargetDeviceId(), currentUserProvider.getCurrentUserId());
                osName = targetDevice.getType() == null ? osName : targetDevice.getType().name();
            } catch (IllegalArgumentException e) {
                return ResponseEntity.status(403).body(ApiResponse.<TaskExecutionResponseDto>builder()
                        .status("ERROR")
                        .message(e.getMessage())
                        .build());
            }
        }
        ScriptPolicyValidator.PolicyDecision policy = scriptPolicyValidator.validate(task.getScript(), osName);
        if (!policy.allowed()) {
            tryUpdateStatus(taskId, TaskStatus.FAILED);
            return ResponseEntity.badRequest().body(ApiResponse.<TaskExecutionResponseDto>builder()
                    .status("ERROR")
                    .message("Script blocked by execution policy")
                    .data(TaskExecutionResponseDto.builder()
                            .taskId(taskId)
                            .status(TaskStatus.FAILED.name())
                            .error(policy.reason())
                            .build())
                    .build());
        }

        if (task.getTargetDeviceId() != null) {
            try {
                nodeCommandService.enqueue(task);
            } catch (IllegalArgumentException e) {
                return ResponseEntity.status(400).body(ApiResponse.<TaskExecutionResponseDto>builder()
                        .status("ERROR")
                        .message(e.getMessage())
                        .build());
            }
            return ResponseEntity.ok(ApiResponse.<TaskExecutionResponseDto>builder()
                    .status("SUCCESS")
                    .message("Remote command queued for the selected device.")
                    .data(TaskExecutionResponseDto.builder()
                            .taskId(taskId)
                            .status(TaskStatus.IN_PROGRESS.name())
                            .output("REMOTE_COMMAND_QUEUED")
                            .build())
                    .build());
        }

        // Mark the task before execution. If this fails, do not execute because
        // Spring Boot would lose the audit trail for a risky local action.
        if (!tryUpdateStatus(taskId, TaskStatus.IN_PROGRESS)) {
            return ResponseEntity.status(503).body(ApiResponse.<TaskExecutionResponseDto>builder()
                    .status("ERROR")
                    .message("Task database is unavailable. Script was not executed.")
                    .build());
        }

        try {
            String output = scriptExecutionService.executeScript(task.getScript());

            if (output != null && output.startsWith("EXEC_FAILED:")) {
                tryUpdateStatus(taskId, TaskStatus.FAILED);
                return ResponseEntity.ok(ApiResponse.<TaskExecutionResponseDto>builder()
                        .status("ERROR")
                        .message("Script execution failed")
                        .data(TaskExecutionResponseDto.builder()
                                .taskId(taskId)
                                .status(TaskStatus.FAILED.name())
                                .error(output)
                                .build())
                    .build());
            }

            boolean statusSaved = tryUpdateStatus(taskId, TaskStatus.COMPLETED);
            return ResponseEntity.ok(ApiResponse.<TaskExecutionResponseDto>builder()
                    .status("SUCCESS")
                    .message(statusSaved
                            ? "Script executed successfully"
                            : "Script executed successfully, but task status could not be saved.")
                    .data(TaskExecutionResponseDto.builder()
                            .taskId(taskId)
                            .status(TaskStatus.COMPLETED.name())
                            .output(output)
                            .build())
                    .build());
        } catch (Exception e) {
            tryUpdateStatus(taskId, TaskStatus.FAILED);
            return ResponseEntity.internalServerError().body(ApiResponse.<TaskExecutionResponseDto>builder()
                    .status("ERROR")
                    .message("Failed to execute script: " + e.getMessage())
                    .data(TaskExecutionResponseDto.builder()
                            .taskId(taskId)
                            .status(TaskStatus.FAILED.name())
                            .error(e.getMessage())
                            .build())
                    .build());
        }
    }

    private boolean tryUpdateStatus(String taskId, TaskStatus status) {
        try {
            taskService.updateTaskStatus(taskId, status, null);
            return true;
        } catch (Exception e) {
            log.error("Could not update task {} to {}", taskId, status, e);
            return false;
        }
    }
}
