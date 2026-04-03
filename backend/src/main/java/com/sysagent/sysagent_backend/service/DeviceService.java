package com.sysagent.sysagent_backend.service;

import java.util.List;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;

import com.sysagent.sysagent_backend.model.dto.DeviceDto;
import com.sysagent.sysagent_backend.model.entity.DeviceEntity;
import com.sysagent.sysagent_backend.repository.DeviceRepository;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class DeviceService {

    private final DeviceRepository deviceRepository;

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

    private DeviceDto mapToDto(DeviceEntity entity) {
        // Remove mock CPU/RAM logic as we will eventually wire up real per-device stats.
        // For now, if it's the current device and online, we can just leave it as 0 or null 
        // to avoid fake "16%" values showing up on the Devices page.
        return DeviceDto.builder()
                .id(entity.getId())
                .name(entity.getName())
                .status(entity.getStatus())
                .ipAddress(entity.getIpAddress())
                .lastSeen(entity.getLastSeen())
                .ownerId(entity.getOwnerId())
                .cpuUsage(null) // Set to null instead of random mock
                .ramUsage(null) // Set to null instead of random mock
                .type(entity.getType()) 
                .build();
    }
}