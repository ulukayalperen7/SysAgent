package com.sysagent.sysagent_backend.model.dto;

import java.time.LocalDateTime;
import java.util.UUID;

import com.sysagent.sysagent_backend.model.entity.NodeCommandEntity;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class NodeCommandStatusDto {
    private UUID id;
    private String taskId;
    private Long deviceId;
    private String status;
    private String output;
    private String error;
    private LocalDateTime createdAt;
    private LocalDateTime claimedAt;
    private LocalDateTime completedAt;

    public static NodeCommandStatusDto fromEntity(NodeCommandEntity command) {
        return NodeCommandStatusDto.builder()
                .id(command.getId())
                .taskId(command.getTaskId())
                .deviceId(command.getDeviceId())
                .status(command.getStatus().name())
                .output(command.getOutput())
                .error(command.getError())
                .createdAt(command.getCreatedAt())
                .claimedAt(command.getClaimedAt())
                .completedAt(command.getCompletedAt())
                .build();
    }
}
