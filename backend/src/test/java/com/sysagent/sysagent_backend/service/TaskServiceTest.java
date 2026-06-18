package com.sysagent.sysagent_backend.service;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.LocalDateTime;
import java.util.List;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.mockito.Mockito.when;

import com.sysagent.sysagent_backend.model.dto.TaskHistoryDto;
import com.sysagent.sysagent_backend.model.entity.TaskEntity;
import com.sysagent.sysagent_backend.model.enums.TaskStatus;
import com.sysagent.sysagent_backend.repository.TaskRepository;

@ExtendWith(MockitoExtension.class)
class TaskServiceTest {

    @Mock
    private TaskRepository taskRepository;

    @InjectMocks
    private TaskService taskService;

    @Test
    void getsTenantScopedTaskHistoryNewestFirstFromRepository() {
        TaskEntity task = TaskEntity.builder()
                .id("task-1")
                .ownerId("test-user-1")
                .intent("open notepad")
                .status(TaskStatus.COMPLETED)
                .timestamp(LocalDateTime.now())
                .build();
        when(taskRepository.findByOwnerIdOrderByTimestampDesc("test-user-1")).thenReturn(List.of(task));

        List<TaskHistoryDto> history = taskService.getTaskHistoryByOwner("test-user-1");

        assertThat(history).hasSize(1);
        assertThat(history.get(0).getId()).isEqualTo("task-1");
        assertThat(history.get(0).getStatus()).isEqualTo("completed");
    }
}
