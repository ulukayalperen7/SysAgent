package com.sysagent.sysagent_backend.service;

import com.sysagent.sysagent_backend.model.dto.DeviceDto;
import com.sysagent.sysagent_backend.model.entity.DeviceEntity;
import com.sysagent.sysagent_backend.repository.DeviceRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class DeviceService {

    private final DeviceRepository deviceRepository;

    public List<DeviceDto> getAllDevices() {
        return deviceRepository.findAll().stream()
                .map(this::mapToDto)
                .collect(Collectors.toList());
    }

    private DeviceDto mapToDto(DeviceEntity entity) {
        return DeviceDto.builder()
                .id(entity.getId())
                .name(entity.getName())
                .status(entity.getStatus())
                // In a real scenario, CPU/RAM usage might come from a separate metrics table or real-time query
                .cpuUsage(0) 
                .ramUsage(0) 
                .type(entity.getType()) 
                .build();
    }
}