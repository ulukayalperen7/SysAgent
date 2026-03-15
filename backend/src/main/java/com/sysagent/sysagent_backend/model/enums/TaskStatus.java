package com.sysagent.sysagent_backend.model.enums;

/**
 * Represents the lifecycle status of an AI-generated task or automation.
 * Used to track the progress from initial intent analysis to completion or rollback.
 */
public enum TaskStatus {
    /**
     * The task has been created and is waiting for execution or approval.
     */
    PENDING,

    /**
     * The task is currently being executed on the target node.
     */
    IN_PROGRESS,

    /**
     * The task has been successfully executed.
     */
    COMPLETED,

    /**
     * The task failed and was rolled back to the previous state.
     */
    ROLLED_BACK,

    /**
     * The task failed and could not be rolled back automatically.
     */
    FAILED
}
