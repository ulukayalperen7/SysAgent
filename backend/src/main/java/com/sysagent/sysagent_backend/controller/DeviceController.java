package com.sysagent.sysagent_backend.controller;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.sysagent.sysagent_backend.model.dto.DeviceDto;
import com.sysagent.sysagent_backend.model.dto.DeviceRegistrationTokenRequestDto;
import com.sysagent.sysagent_backend.model.dto.DeviceRegistrationTokenResponseDto;
import com.sysagent.sysagent_backend.model.response.ApiResponse;
import com.sysagent.sysagent_backend.security.CurrentUserProvider;
import com.sysagent.sysagent_backend.service.DeviceService;

import lombok.RequiredArgsConstructor;

/**
 * Controller for managing connected devices.
 * Provides endpoints to list devices and get their status.
 */
@RestController
@RequestMapping("/api/devices")
@RequiredArgsConstructor
public class DeviceController {

    private final DeviceService deviceService;
    private final CurrentUserProvider currentUserProvider;

    @GetMapping
    public ResponseEntity<ApiResponse<List<DeviceDto>>> getConnectedDevices() {
        List<DeviceDto> devices = deviceService.getDevicesByOwner(currentUserProvider.getCurrentUserId());

        return ResponseEntity.ok(ApiResponse.<List<DeviceDto>>builder()
                .status("SUCCESS")
                .message("Devices fetched successfully")
                .data(devices)
                .build());
    }

    @PostMapping("/registration-token")
    public ResponseEntity<ApiResponse<DeviceRegistrationTokenResponseDto>> createRegistrationToken(
            @RequestBody(required = false) DeviceRegistrationTokenRequestDto request) {
        String label = request == null ? null : request.getLabel();
        DeviceRegistrationTokenResponseDto token = deviceService.createRegistrationToken(
                currentUserProvider.getCurrentUserId(),
                label);
        return ResponseEntity.ok(ApiResponse.success(token, "Device registration token created"));
    }
}
