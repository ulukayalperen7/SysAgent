package com.sysagent.sysagent_backend.controller;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.sysagent.sysagent_backend.model.entity.TaskEntity;
import com.sysagent.sysagent_backend.model.response.ApiResponse;
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

    @GetMapping
    public ResponseEntity<ApiResponse<List<TaskEntity>>> getAllTasks() {
        List<TaskEntity> tasks = taskService.getAllTasks();
        return ResponseEntity.ok(ApiResponse.<List<TaskEntity>>builder()
                .status("SUCCESS")
                .message("Tasks fetched successfully")
                .data(tasks)
                .build());
    }

    @PostMapping("/{id}/execute")
    public ResponseEntity<ApiResponse<String>> executeTask(@PathVariable("id") String taskId) {
        TaskEntity task = taskService.getTaskById(taskId);
        
        if (task.getScript() == null || task.getScript().isBlank()) {
            return ResponseEntity.badRequest().body(ApiResponse.<String>builder()
                    .status("ERROR")
                    .message("No script is associated with this task.")
                    .build());
        }

        // Guard: prevent re-executing a task that already ran
        if (task.getStatus() == TaskStatus.COMPLETED || task.getStatus() == TaskStatus.FAILED) {
            return ResponseEntity.badRequest().body(ApiResponse.<String>builder()
                    .status("ERROR")
                    .message("Task has already been executed with status: " + task.getStatus())
                    .build());
        }

        // Mark the task before execution. If this fails, do not execute because
        // Spring Boot would lose the audit trail for a risky local action.
        if (!tryUpdateStatus(taskId, TaskStatus.IN_PROGRESS)) {
            return ResponseEntity.status(503).body(ApiResponse.<String>builder()
                    .status("ERROR")
                    .message("Task database is unavailable. Script was not executed.")
                    .build());
        }

        try {
            String output = scriptExecutionService.executeScript(task.getScript());

            if (output != null && output.startsWith("EXEC_FAILED:")) {
                tryUpdateStatus(taskId, TaskStatus.FAILED);
                return ResponseEntity.ok(ApiResponse.<String>builder()
                        .status("ERROR")
                        .message("Script execution failed")
                        .data(output)
                    .build());
            }

            boolean statusSaved = tryUpdateStatus(taskId, TaskStatus.COMPLETED);
            return ResponseEntity.ok(ApiResponse.<String>builder()
                    .status("SUCCESS")
                    .message(statusSaved
                            ? "Script executed successfully"
                            : "Script executed successfully, but task status could not be saved.")
                    .data(output)
                    .build());
        } catch (Exception e) {
            tryUpdateStatus(taskId, TaskStatus.FAILED);
            return ResponseEntity.internalServerError().body(ApiResponse.<String>builder()
                    .status("ERROR")
                    .message("Failed to execute script: " + e.getMessage())
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
