package com.sysagent.sysagent_backend.service;

import java.util.List;
import java.util.Random;
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
    private final Random random = new Random();

    public List<DeviceDto> getAllDevices() {
        return deviceRepository.findAll().stream()
                .map(this::mapToDto)
                .collect(Collectors.toList());
    }

    private DeviceDto mapToDto(DeviceEntity entity) {
        // Mock live metrics for demo purposes
        int simulatedCpu = random.nextInt(30) + 10; 
        int simulatedRam = random.nextInt(40) + 20;

        return DeviceDto.builder()
                .id(entity.getId())
                .name(entity.getName())
                .status(entity.getStatus())
                .ipAddress(entity.getIpAddress())
                .lastSeen(entity.getLastSeen())
                .cpuUsage(simulatedCpu) 
                .ramUsage(simulatedRam) 
                .type(entity.getType()) 
                .build();
    }
}