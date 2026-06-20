package com.sysagent.sysagent_backend.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.time.LocalDateTime;
import java.util.Map;
import java.util.Optional;

import org.junit.jupiter.api.Test;

import com.sysagent.sysagent_backend.model.dto.DeviceContextSnapshotDto;
import com.sysagent.sysagent_backend.model.dto.NodeDesktopContextRequestDto;
import com.sysagent.sysagent_backend.model.entity.DeviceContextSnapshotEntity;
import com.sysagent.sysagent_backend.model.entity.DeviceEntity;
import com.sysagent.sysagent_backend.model.enums.DeviceType;
import com.sysagent.sysagent_backend.repository.DeviceContextSnapshotRepository;
import com.sysagent.sysagent_backend.repository.DeviceRepository;
import com.sysagent.sysagent_backend.security.NodeDeviceAuthService;
import com.sysagent.sysagent_backend.security.TokenHashingService;

import org.mockito.Mockito;

class DeviceContextServiceTest {

    private final DeviceContextSnapshotRepository snapshotRepository = Mockito.mock(DeviceContextSnapshotRepository.class);
    private final DeviceRepository deviceRepository = Mockito.mock(DeviceRepository.class);
    private final TokenHashingService tokenHashingService = new TokenHashingService();
    private final DeviceContextService service = new DeviceContextService(
            snapshotRepository,
            new NodeDeviceAuthService(deviceRepository, tokenHashingService));

    @Test
    void recordsOwnerScopedDesktopContextForValidNodeToken() {
        when(deviceRepository.findById(10L)).thenReturn(Optional.of(device("node-token")));
        when(snapshotRepository.save(any(DeviceContextSnapshotEntity.class)))
                .thenAnswer(invocation -> invocation.getArgument(0));

        NodeDesktopContextRequestDto request = new NodeDesktopContextRequestDto();
        request.setDeviceId(10L);
        request.setActiveWindowTitle("Visual Studio Code");
        request.setActiveProcessName("Code.exe");
        request.setScreenWidth(1920);
        request.setScreenHeight(1080);
        request.setScreenshotMimeType("image/jpeg");
        request.setScreenshotBase64("abc");
        request.setMetadata(Map.of("platform", "Windows"));

        DeviceContextSnapshotDto snapshot = service.recordSnapshot("node-token", request);

        assertThat(snapshot.getOwnerId()).isEqualTo("user-1");
        assertThat(snapshot.getActiveProcessName()).isEqualTo("Code.exe");
        assertThat(snapshot.getMetadataJson()).contains("\"platform\":\"Windows\"");
        verify(snapshotRepository).deleteOlderThanLimit(10L, "user-1", 50);
    }

    @Test
    void rejectsInvalidScreenshotMimeType() {
        when(deviceRepository.findById(10L)).thenReturn(Optional.of(device("node-token")));
        NodeDesktopContextRequestDto request = new NodeDesktopContextRequestDto();
        request.setDeviceId(10L);
        request.setScreenshotMimeType("text/plain");
        request.setScreenshotBase64("abc");

        assertThatThrownBy(() -> service.recordSnapshot("node-token", request))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Unsupported screenshot mime type.");
    }

    @Test
    void loadsLatestPostCommandContextForTask() {
        DeviceContextSnapshotEntity entity = DeviceContextSnapshotEntity.builder()
                .id(java.util.UUID.randomUUID())
                .deviceId(10L)
                .ownerId("user-1")
                .activeWindowTitle("Done")
                .activeProcessName("Code.exe")
                .metadataJson("{\"post_command\":true,\"task_id\":\"task-1\"}")
                .createdAt(LocalDateTime.now())
                .build();
        when(snapshotRepository.findLatestPostCommandContext(10L, "user-1", "task-1"))
                .thenReturn(Optional.of(entity));

        DeviceContextSnapshotDto snapshot = service
                .getLatestPostCommandContext(10L, "user-1", "task-1")
                .orElseThrow();

        assertThat(snapshot.getActiveWindowTitle()).isEqualTo("Done");
        assertThat(snapshot.getMetadataJson()).contains("\"post_command\":true");
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
