package com.sysagent.sysagent_backend.security;

import org.springframework.stereotype.Service;

import com.sysagent.sysagent_backend.model.entity.DeviceEntity;
import com.sysagent.sysagent_backend.repository.DeviceRepository;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class NodeDeviceAuthService {

    private final DeviceRepository deviceRepository;
    private final TokenHashingService tokenHashingService;

    public DeviceEntity authenticateDevice(Long deviceId, String nodeToken) {
        DeviceEntity device = requireDevice(deviceId);
        String expectedHash = device.getNodeTokenHash();
        if (expectedHash == null || expectedHash.isBlank() || nodeToken == null || nodeToken.isBlank()) {
            throw new IllegalArgumentException("Invalid node token.");
        }
        if (!expectedHash.equals(tokenHashingService.hash(nodeToken))) {
            throw new IllegalArgumentException("Invalid node token.");
        }
        return device;
    }

    public DeviceEntity requireDevice(Long deviceId) {
        if (deviceId == null) {
            throw new IllegalArgumentException("Device id is required.");
        }
        return deviceRepository.findById(deviceId)
                .orElseThrow(() -> new IllegalArgumentException("Device not found."));
    }
}
