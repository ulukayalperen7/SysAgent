package com.sysagent.sysagent_backend.model.entity;

import java.time.LocalDateTime;

import com.sysagent.sysagent_backend.model.enums.TaskStatus;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Represents an AI-driven automation task requested by the user.
 * Tracks the original intent, the generated script, and the execution status.
 */
@Entity
@Table(name = "tasks")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TaskEntity {
    
    /**
     * Unique identifier for the task (UUID usually).
     */
    @Id
    @Column(nullable = false, unique = true)
    private String id;

    /**
     * The ID of the user who owns this task.
     * Prevents users from viewing or managing other users' agent tasks.
     */
    @Column(nullable = false)
    private String ownerId;

    /**
     * Optional device selected by the user for this task.
     * Null means the current backend host/local execution path.
     */
    private Long targetDeviceId;
    
    /**
     * The original natural language request from the user (e.g., "Clean logs older than 7 days").
     */
    @Column(nullable = false, columnDefinition = "TEXT")
    private String intent;
    
    /**
     * The generated script proposed by the AI Agent.
     */
    @Column(columnDefinition = "TEXT")
    private String script;
    
    /**
     * Current lifecycle status of the task.
     */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private TaskStatus status;
    
    /**
     * When the task was created.
     */
    @Column(nullable = false)
    private LocalDateTime timestamp;
    
    /**
     * A script to revert changes if the task fails or is manually rolled back.
     * Stored as TEXT to allow large scripts.
     */
    @Column(columnDefinition = "TEXT")
    private String rollbackScript;
}
