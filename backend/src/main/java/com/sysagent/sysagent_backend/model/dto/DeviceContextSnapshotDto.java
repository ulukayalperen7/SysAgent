package com.sysagent.sysagent_backend.model.dto;

import java.time.LocalDateTime;
import java.util.UUID;

import com.sysagent.sysagent_backend.model.entity.DeviceContextSnapshotEntity;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class DeviceContextSnapshotDto {
    private UUID id;
    private Long deviceId;
    private String ownerId;
    private String activeWindowTitle;
    private String activeProcessName;
    private Integer screenWidth;
    private Integer screenHeight;
    private String screenshotMimeType;
    private String screenshotBase64;
    private String metadataJson;
    private LocalDateTime capturedAt;
    private LocalDateTime createdAt;

    public static DeviceContextSnapshotDto fromEntity(DeviceContextSnapshotEntity entity) {
        return DeviceContextSnapshotDto.builder()
                .id(entity.getId())
                .deviceId(entity.getDeviceId())
                .ownerId(entity.getOwnerId())
                .activeWindowTitle(entity.getActiveWindowTitle())
                .activeProcessName(entity.getActiveProcessName())
                .screenWidth(entity.getScreenWidth())
                .screenHeight(entity.getScreenHeight())
                .screenshotMimeType(entity.getScreenshotMimeType())
                .screenshotBase64(entity.getScreenshotBase64())
                .metadataJson(entity.getMetadataJson())
                .capturedAt(entity.getCapturedAt())
                .createdAt(entity.getCreatedAt())
                .build();
    }
}
