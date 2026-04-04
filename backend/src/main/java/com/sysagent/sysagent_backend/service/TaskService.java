package com.sysagent.sysagent_backend.service;

import com.sysagent.sysagent_backend.model.entity.TaskEntity;
import com.sysagent.sysagent_backend.model.enums.TaskStatus;
import com.sysagent.sysagent_backend.repository.TaskRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class TaskService {

    private final TaskRepository taskRepository;

    @Transactional
    public TaskEntity createTask(String intent, String ownerId) {
        TaskEntity task = TaskEntity.builder()
                .id(UUID.randomUUID().toString())
                .intent(intent)
                .ownerId(ownerId) // Fixed: Set ownerId to satisfy DB constraint
                .status(TaskStatus.PENDING)
                .timestamp(LocalDateTime.now())
                .build();
                
        log.info("Created new PENDING task with ID: {} for user: {}", task.getId(), ownerId);
        return taskRepository.save(task);
    }

    @Transactional(readOnly = true)
    public List<TaskEntity> getAllTasks() {
        return taskRepository.findAll();
    }
    
    @Transactional
    public TaskEntity updateTaskStatus(String taskId, TaskStatus status, String rollbackScript) {
        TaskEntity task = taskRepository.findById(taskId)
                .orElseThrow(() -> new IllegalArgumentException("Task not found with ID: " + taskId));
                
        task.setStatus(status);
        if (rollbackScript != null) {
            task.setRollbackScript(rollbackScript);
        }
        
        log.info("Updated status for task {} to {}", taskId, status);
        return taskRepository.save(task);
    }
}
