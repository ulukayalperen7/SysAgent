package com.sysagent.sysagent_backend.service;

import java.time.LocalDateTime;
import java.util.UUID;
import java.util.List;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;

import com.sysagent.sysagent_backend.model.dto.DeviceNodeRegistrationRequestDto;
import com.sysagent.sysagent_backend.model.dto.DeviceRegistrationTokenResponseDto;
import com.sysagent.sysagent_backend.model.dto.DeviceDto;
import com.sysagent.sysagent_backend.model.dto.NodeRegistrationResponseDto;
import com.sysagent.sysagent_backend.model.entity.DeviceEntity;
import com.sysagent.sysagent_backend.model.entity.DeviceRegistrationTokenEntity;
import com.sysagent.sysagent_backend.model.enums.DeviceType;
import com.sysagent.sysagent_backend.repository.DeviceRegistrationTokenRepository;
import com.sysagent.sysagent_backend.repository.DeviceRepository;
import com.sysagent.sysagent_backend.security.TokenHashingService;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class DeviceService {

    private final DeviceRepository deviceRepository;
    private final DeviceRegistrationTokenRepository registrationTokenRepository;
    private final TokenHashingService tokenHashingService;

    /**
     * Replaced getAllDevices with a tenant-aware method.
     * 
     * @param ownerId The ID of the currently authenticated user.
     * @return List of DeviceDto belonging only to this user.
     */
    public List<DeviceDto> getDevicesByOwner(String ownerId) {
        return deviceRepository.findByOwnerId(ownerId).stream()
                .map(this::mapToDto)
                .collect(Collectors.toList());
    }

    public DeviceDto getOwnedDevice(Long deviceId, String ownerId) {
        return deviceRepository.findByIdAndOwnerId(deviceId, ownerId)
                .map(this::mapToDto)
                .orElseThrow(() -> new IllegalArgumentException("Target device does not belong to the current user."));
    }

    public DeviceRegistrationTokenResponseDto createRegistrationToken(String ownerId, String label) {
        String token = tokenHashingService.newPlainToken();
        LocalDateTime expiresAt = LocalDateTime.now().plusMinutes(30);
        registrationTokenRepository.save(DeviceRegistrationTokenEntity.builder()
                .id(UUID.randomUUID())
                .ownerId(ownerId)
                .tokenHash(tokenHashingService.hash(token))
                .label(cleanLabel(label))
                .expiresAt(expiresAt)
                .createdAt(LocalDateTime.now())
                .build());

        return DeviceRegistrationTokenResponseDto.builder()
                .token(token)
                .expiresAt(expiresAt)
                .bootstrapCommand("sysagent-node register --server http://localhost:8080 --token " + token)
                .build();
    }

    public NodeRegistrationResponseDto registerNode(DeviceNodeRegistrationRequestDto request, String fallbackIpAddress) {
        if (request.getToken() == null || request.getToken().isBlank()) {
            throw new IllegalArgumentException("Registration token is required.");
        }
        DeviceRegistrationTokenEntity token = registrationTokenRepository
                .findByTokenHash(tokenHashingService.hash(request.getToken()))
                .orElseThrow(() -> new IllegalArgumentException("Invalid registration token."));
        if (token.getUsedAt() != null) {
            throw new IllegalArgumentException("Registration token has already been used.");
        }
        if (token.getExpiresAt().isBefore(LocalDateTime.now())) {
            throw new IllegalArgumentException("Registration token has expired.");
        }

        String name = cleanDeviceName(request.getName());
        DeviceType type = request.getType() == null ? DeviceType.WINDOWS : request.getType();
        String ipAddress = cleanIp(request.getIpAddress(), fallbackIpAddress);
        String nodeToken = tokenHashingService.newPlainToken();
        DeviceEntity device = deviceRepository.findByOwnerIdAndName(token.getOwnerId(), name)
                .orElse(DeviceEntity.builder()
                        .ownerId(token.getOwnerId())
                        .name(name)
                        .type(type)
                        .build());

        device.setIpAddress(ipAddress);
        device.setType(type);
        device.setStatus("online");
        device.setLastSeen(LocalDateTime.now());
        device.setNodeTokenHash(tokenHashingService.hash(nodeToken));
        DeviceEntity saved = deviceRepository.save(device);

        token.setUsedAt(LocalDateTime.now());
        registrationTokenRepository.save(token);
        return NodeRegistrationResponseDto.builder()
                .device(mapToDto(saved))
                .nodeToken(nodeToken)
                .heartbeatIntervalSeconds(30)
                .build();
    }

    private DeviceDto mapToDto(DeviceEntity entity) {
        return DeviceDto.builder()
                .id(entity.getId())
                .name(entity.getName())
                .status(entity.getStatus())
                .ipAddress(entity.getIpAddress())
                .lastSeen(entity.getLastSeen())
                .ownerId(entity.getOwnerId())
                .cpuUsage(null)
                .ramUsage(null)
                .type(entity.getType()) 
                .build();
    }

    private String cleanLabel(String label) {
        if (label == null || label.isBlank()) {
            return "Device registration";
        }
        String cleaned = label.trim();
        return cleaned.length() > 80 ? cleaned.substring(0, 80) : cleaned;
    }

    private String cleanDeviceName(String name) {
        if (name == null || name.isBlank()) {
            return "Unnamed device";
        }
        String cleaned = name.trim();
        return cleaned.length() > 120 ? cleaned.substring(0, 120) : cleaned;
    }

    private String cleanIp(String provided, String fallback) {
        String value = provided == null || provided.isBlank() ? fallback : provided.trim();
        if (value == null || value.isBlank()) {
            return "unknown";
        }
        return value.length() > 120 ? value.substring(0, 120) : value;
    }
}
