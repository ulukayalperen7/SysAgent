package com.sysagent.sysagent_backend.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.sysagent.sysagent_backend.model.dto.NodeCommandDto;
import com.sysagent.sysagent_backend.model.dto.NodeCommandResultRequestDto;
import com.sysagent.sysagent_backend.model.entity.DeviceEntity;
import com.sysagent.sysagent_backend.model.entity.NodeCommandEntity;
import com.sysagent.sysagent_backend.model.entity.TaskEntity;
import com.sysagent.sysagent_backend.model.enums.DeviceType;
import com.sysagent.sysagent_backend.model.enums.NodeCommandStatus;
import com.sysagent.sysagent_backend.model.enums.TaskStatus;
import com.sysagent.sysagent_backend.repository.DeviceRepository;
import com.sysagent.sysagent_backend.repository.NodeCommandRepository;
import com.sysagent.sysagent_backend.security.TokenHashingService;

@ExtendWith(MockitoExtension.class)
class NodeCommandServiceTest {

    @Mock
    private DeviceRepository deviceRepository;

    @Mock
    private NodeCommandRepository nodeCommandRepository;

    @Mock
    private TaskService taskService;

    private final TokenHashingService tokenHashingService = new TokenHashingService();

    @InjectMocks
    private NodeCommandService nodeCommandService;

    @Test
    void queuesClaimsAndCompletesRemoteCommandWithNodeToken() {
        nodeCommandService = new NodeCommandService(deviceRepository, nodeCommandRepository, tokenHashingService, taskService);
        String nodeToken = "node-token";
        DeviceEntity device = device(nodeToken);
        TaskEntity task = TaskEntity.builder()
                .id("task-1")
                .ownerId("user-1")
                .targetDeviceId(10L)
                .script("Write-Output ok")
                .status(TaskStatus.ANALYZED)
                .build();

        when(deviceRepository.findById(10L)).thenReturn(Optional.of(device));
        when(nodeCommandRepository.save(any(NodeCommandEntity.class))).thenAnswer(invocation -> invocation.getArgument(0));

        NodeCommandDto queued = nodeCommandService.enqueue(task);

        assertThat(queued.getStatus()).isEqualTo("QUEUED");
        verify(taskService).updateTaskStatus("task-1", TaskStatus.IN_PROGRESS, null);

        ArgumentCaptor<NodeCommandEntity> commandCaptor = ArgumentCaptor.forClass(NodeCommandEntity.class);
        verify(nodeCommandRepository).save(commandCaptor.capture());
        NodeCommandEntity savedCommand = commandCaptor.getValue();

        when(nodeCommandRepository.findFirstByDeviceIdAndStatusOrderByCreatedAtAsc(10L, NodeCommandStatus.QUEUED))
                .thenReturn(Optional.of(savedCommand));
        NodeCommandDto claimed = nodeCommandService.claimNextCommand(nodeToken, 10L).orElseThrow();

        assertThat(claimed.getStatus()).isEqualTo("CLAIMED");

        NodeCommandResultRequestDto result = new NodeCommandResultRequestDto();
        result.setDeviceId(10L);
        result.setSuccess(true);
        result.setOutput("ok");
        when(nodeCommandRepository.findById(savedCommand.getId())).thenReturn(Optional.of(savedCommand));

        nodeCommandService.recordCommandResult(nodeToken, savedCommand.getId().toString(), result);

        assertThat(savedCommand.getStatus()).isEqualTo(NodeCommandStatus.COMPLETED);
        assertThat(savedCommand.getOutput()).isEqualTo("ok");
        verify(taskService).updateTaskStatus("task-1", TaskStatus.COMPLETED, null);
    }

    @Test
    void rejectsInvalidNodeToken() {
        nodeCommandService = new NodeCommandService(deviceRepository, nodeCommandRepository, tokenHashingService, taskService);
        when(deviceRepository.findById(10L)).thenReturn(Optional.of(device("correct-token")));

        assertThatThrownBy(() -> nodeCommandService.claimNextCommand("wrong-token", 10L))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Invalid node token.");
    }

    @Test
    void rejectsQueueWhenDeviceOwnerDoesNotMatchTaskOwner() {
        nodeCommandService = new NodeCommandService(deviceRepository, nodeCommandRepository, tokenHashingService, taskService);
        when(deviceRepository.findById(10L)).thenReturn(Optional.of(device("correct-token")));
        TaskEntity task = TaskEntity.builder()
                .id("task-2")
                .ownerId("other-user")
                .targetDeviceId(10L)
                .script("Write-Output nope")
                .build();

        assertThatThrownBy(() -> nodeCommandService.enqueue(task))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Target device does not belong to the task owner.");
    }

    private DeviceEntity device(String plainToken) {
        return DeviceEntity.builder()
                .id(10L)
                .name("Office PC")
                .ipAddress("127.0.0.1")
                .type(DeviceType.WINDOWS)
                .status("online")
                .ownerId("user-1")
                .nodeTokenHash(tokenHashingService.hash(plainToken))
                .lastSeen(LocalDateTime.now())
                .build();
    }
}
