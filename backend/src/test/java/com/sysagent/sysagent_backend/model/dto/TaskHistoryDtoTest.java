package com.sysagent.sysagent_backend.model.dto;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.LocalDateTime;

import org.junit.jupiter.api.Test;

import com.sysagent.sysagent_backend.model.entity.TaskEntity;
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
}
