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

        // Mark task as in-progress to block concurrent duplicate calls
        taskService.updateTaskStatus(taskId, TaskStatus.IN_PROGRESS, null);

        try {
            String output = scriptExecutionService.executeScript(task.getScript());
            taskService.updateTaskStatus(taskId, TaskStatus.COMPLETED, null);
            
            return ResponseEntity.ok(ApiResponse.<String>builder()
                    .status("SUCCESS")
                    .message("Script executed successfully")
                    .data(output)
                    .build());
        } catch (Exception e) {
            taskService.updateTaskStatus(taskId, TaskStatus.FAILED, null);
            return ResponseEntity.internalServerError().body(ApiResponse.<String>builder()
                    .status("ERROR")
                    .message("Failed to execute script: " + e.getMessage())
                    .build());
        }
    }
}
