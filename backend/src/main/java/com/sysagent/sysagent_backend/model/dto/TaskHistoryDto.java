package com.sysagent.sysagent_backend.model.dto;

import java.time.LocalDateTime;

import com.sysagent.sysagent_backend.model.entity.TaskEntity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TaskHistoryDto {
    private String id;
    private String ownerId;
    private Long targetDeviceId;
    private String intent;
    private String status;
    private LocalDateTime timestamp;
    private boolean hasScript;
    private boolean hasRollbackScript;
    private boolean canUndo;
    private String remoteCommandId;
    private String remoteCommandStatus;
    private LocalDateTime remoteCommandUpdatedAt;
    private boolean remoteCommandHasOutput;
    private boolean remoteCommandHasError;

    public static TaskHistoryDto fromEntity(TaskEntity task) {
        boolean hasRollback = task.getRollbackScript() != null && !task.getRollbackScript().isBlank();
        return TaskHistoryDto.builder()
                .id(task.getId())
                .ownerId(task.getOwnerId())
                .targetDeviceId(task.getTargetDeviceId())
                .intent(task.getIntent())
                .status(task.getStatus() == null ? "unknown" : task.getStatus().name().toLowerCase())
                .timestamp(task.getTimestamp())
                .hasScript(task.getScript() != null && !task.getScript().isBlank())
                .hasRollbackScript(hasRollback)
                .canUndo(hasRollback)
                .build();
    }

    public void attachRemoteCommand(NodeCommandStatusDto command) {
        if (command == null) {
            return;
        }
        this.remoteCommandId = command.getId() == null ? null : command.getId().toString();
        this.remoteCommandStatus = command.getStatus();
        this.remoteCommandUpdatedAt = command.getCompletedAt() != null
                ? command.getCompletedAt()
                : command.getClaimedAt() != null ? command.getClaimedAt() : command.getCreatedAt();
        this.remoteCommandHasOutput = command.getOutput() != null && !command.getOutput().isBlank();
        this.remoteCommandHasError = command.getError() != null && !command.getError().isBlank();
    }
}
