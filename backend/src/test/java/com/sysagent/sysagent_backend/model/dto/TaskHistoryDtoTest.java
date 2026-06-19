package com.sysagent.sysagent_backend.model.dto;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.LocalDateTime;
import java.util.UUID;

import org.junit.jupiter.api.Test;

import com.sysagent.sysagent_backend.model.entity.NodeCommandEntity;
import com.sysagent.sysagent_backend.model.entity.TaskEntity;
import com.sysagent.sysagent_backend.model.enums.NodeCommandStatus;
import com.sysagent.sysagent_backend.model.enums.TaskStatus;

class TaskHistoryDtoTest {

    @Test
    void mapsTaskEntityWithoutExposingScriptBody() {
        TaskEntity task = TaskEntity.builder()
                .id("task-1")
                .ownerId("user-1")
                .intent("show cpu")
                .status(TaskStatus.ANALYZED)
                .timestamp(LocalDateTime.now())
                .script("Get-Process")
                .rollbackScript("")
                .build();

        TaskHistoryDto dto = TaskHistoryDto.fromEntity(task);

        assertThat(dto.getId()).isEqualTo("task-1");
        assertThat(dto.getStatus()).isEqualTo("analyzed");
        assertThat(dto.isHasScript()).isTrue();
        assertThat(dto.isHasRollbackScript()).isFalse();
        assertThat(dto.isCanUndo()).isFalse();
    }

    @Test
    void attachesRemoteCommandStatusSummary() {
        TaskHistoryDto dto = TaskHistoryDto.builder()
                .id("task-remote")
                .status("in_progress")
                .build();
        NodeCommandEntity command = NodeCommandEntity.builder()
                .id(UUID.randomUUID())
                .taskId("task-remote")
                .deviceId(10L)
                .status(NodeCommandStatus.FAILED)
                .error("boom")
                .createdAt(LocalDateTime.now().minusSeconds(5))
                .completedAt(LocalDateTime.now())
                .build();

        dto.attachRemoteCommand(NodeCommandStatusDto.fromEntity(command));

        assertThat(dto.getRemoteCommandStatus()).isEqualTo("FAILED");
        assertThat(dto.isRemoteCommandHasError()).isTrue();
        assertThat(dto.isRemoteCommandHasOutput()).isFalse();
        assertThat(dto.getRemoteCommandId()).isNotBlank();
    }
}
