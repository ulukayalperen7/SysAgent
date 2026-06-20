package com.sysagent.sysagent_backend.service;

import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.util.Collection;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.sysagent.sysagent_backend.model.dto.DeviceContextSnapshotDto;
import com.sysagent.sysagent_backend.model.dto.NodeDesktopContextRequestDto;
import com.sysagent.sysagent_backend.model.entity.DeviceContextSnapshotEntity;
import com.sysagent.sysagent_backend.model.entity.DeviceEntity;
import com.sysagent.sysagent_backend.repository.DeviceContextSnapshotRepository;
import com.sysagent.sysagent_backend.security.NodeDeviceAuthService;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class DeviceContextService {

    private static final int MAX_SCREENSHOT_BASE64_LENGTH = 2_500_000;
    private static final int MAX_SNAPSHOTS_PER_DEVICE = 50;

    private final DeviceContextSnapshotRepository snapshotRepository;
    private final NodeDeviceAuthService nodeDeviceAuthService;

    @Transactional
    public DeviceContextSnapshotDto recordSnapshot(String nodeToken, NodeDesktopContextRequestDto request) {
        DeviceEntity device = nodeDeviceAuthService.authenticateDevice(request.getDeviceId(), nodeToken);
        DeviceContextSnapshotEntity snapshot = DeviceContextSnapshotEntity.builder()
                .id(UUID.randomUUID())
                .deviceId(device.getId())
                .ownerId(device.getOwnerId())
                .activeWindowTitle(clean(request.getActiveWindowTitle(), 240))
                .activeProcessName(clean(request.getActiveProcessName(), 160))
                .screenWidth(validDimension(request.getScreenWidth()))
                .screenHeight(validDimension(request.getScreenHeight()))
                .screenshotMimeType(cleanMimeType(request.getScreenshotMimeType(), request.getScreenshotBase64()))
                .screenshotBase64(cleanScreenshot(request.getScreenshotBase64()))
                .metadataJson(toMetadataJson(request.getMetadata()))
                .capturedAt(parseCapturedAt(request.getCapturedAt()))
                .createdAt(LocalDateTime.now())
                .build();
        DeviceContextSnapshotEntity saved = snapshotRepository.save(snapshot);
        snapshotRepository.deleteOlderThanLimit(device.getId(), device.getOwnerId(), MAX_SNAPSHOTS_PER_DEVICE);
        return DeviceContextSnapshotDto.fromEntity(saved);
    }

    @Transactional(readOnly = true)
    public Optional<DeviceContextSnapshotDto> getLatestForOwner(Long deviceId, String ownerId) {
        return snapshotRepository.findFirstByDeviceIdAndOwnerIdOrderByCreatedAtDesc(deviceId, ownerId)
                .map(DeviceContextSnapshotDto::fromEntity);
    }

    private String clean(String value, int maxLength) {
        if (value == null) {
            return null;
        }
        String cleaned = value.trim();
        return cleaned.length() > maxLength ? cleaned.substring(0, maxLength) : cleaned;
    }

    private Integer validDimension(Integer value) {
        if (value == null || value <= 0 || value > 16_384) {
            return null;
        }
        return value;
    }

    private String cleanMimeType(String mimeType, String screenshotBase64) {
        if (screenshotBase64 == null || screenshotBase64.isBlank()) {
            return null;
        }
        String cleaned = clean(mimeType, 80);
        if (cleaned == null) {
            return null;
        }
        if (!cleaned.equals("image/png") && !cleaned.equals("image/jpeg") && !cleaned.equals("image/webp")) {
            throw new IllegalArgumentException("Unsupported screenshot mime type.");
        }
        return cleaned;
    }

    private String cleanScreenshot(String screenshotBase64) {
        if (screenshotBase64 == null || screenshotBase64.isBlank()) {
            return null;
        }
        String cleaned = screenshotBase64.trim();
        if (cleaned.length() > MAX_SCREENSHOT_BASE64_LENGTH) {
            throw new IllegalArgumentException("Screenshot payload is too large.");
        }
        return cleaned;
    }

    private String toMetadataJson(Map<String, Object> metadata) {
        if (metadata == null || metadata.isEmpty()) {
            return "{}";
        }
        return toJson(metadata);
    }

    private String toJson(Object value) {
        if (value == null) {
            return "null";
        }
        if (value instanceof String text) {
            return "\"" + escapeJson(text) + "\"";
        }
        if (value instanceof Number || value instanceof Boolean) {
            return String.valueOf(value);
        }
        if (value instanceof Map<?, ?> map) {
            StringBuilder builder = new StringBuilder("{");
            boolean first = true;
            for (Map.Entry<?, ?> entry : map.entrySet()) {
                if (!first) {
                    builder.append(",");
                }
                first = false;
                builder.append("\"").append(escapeJson(String.valueOf(entry.getKey()))).append("\":");
                builder.append(toJson(entry.getValue()));
            }
            return builder.append("}").toString();
        }
        if (value instanceof Collection<?> collection) {
            StringBuilder builder = new StringBuilder("[");
            boolean first = true;
            for (Object item : collection) {
                if (!first) {
                    builder.append(",");
                }
                first = false;
                builder.append(toJson(item));
            }
            return builder.append("]").toString();
        }
        return "\"" + escapeJson(String.valueOf(value)) + "\"";
    }

    private String escapeJson(String value) {
        return value.replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\r", "\\r")
                .replace("\n", "\\n")
                .replace("\t", "\\t");
    }

    private LocalDateTime parseCapturedAt(String capturedAt) {
        if (capturedAt == null || capturedAt.isBlank()) {
            return LocalDateTime.now();
        }
        try {
            return OffsetDateTime.parse(capturedAt).toLocalDateTime();
        } catch (Exception ignored) {
            return LocalDateTime.now();
        }
    }
}
