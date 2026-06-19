package com.sysagent.sysagent_backend.model.dto;

import java.time.LocalDateTime;
import java.util.UUID;

import com.sysagent.sysagent_backend.model.entity.NodeCommandEntity;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class NodeCommandDto {
    private UUID id;
    private String taskId;
    private String script;
    private String status;
    private LocalDateTime createdAt;

    public static NodeCommandDto fromEntity(NodeCommandEntity command) {
        return NodeCommandDto.builder()
                .id(command.getId())
                .taskId(command.getTaskId())
                .script(command.getScript())
                .status(command.getStatus().name())
                .createdAt(command.getCreatedAt())
                .build();
    }
}
