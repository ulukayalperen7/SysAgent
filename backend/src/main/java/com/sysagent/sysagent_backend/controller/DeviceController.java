package com.sysagent.sysagent_backend.controller;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.sysagent.sysagent_backend.model.dto.DeviceDto;
import com.sysagent.sysagent_backend.model.response.ApiResponse;
import com.sysagent.sysagent_backend.service.DeviceService;

import lombok.RequiredArgsConstructor;

/**
 * Controller for managing connected devices.
 * Provides endpoints to list devices and get their status.
 */
@RestController
@RequestMapping("/api/devices")
@CrossOrigin(origins = "*") // Allow Angular frontend to call this
@RequiredArgsConstructor
public class DeviceController {

    private final DeviceService deviceService; // added

    // TODO: When authentication is implemented, extract ownerId from the security context (e.g., JWT token).
    // For now, we simulate a logged-in user with a hardcoded ID for testing.
    private static final String CURRENT_LOGGED_IN_USER_ID = "test-user-1";

    @GetMapping
    public ResponseEntity<ApiResponse<List<DeviceDto>>> getConnectedDevices() {
        // Pass the simulated logged-in user's ID to the service
        List<DeviceDto> devices = deviceService.getDevicesByOwner(CURRENT_LOGGED_IN_USER_ID);

        return ResponseEntity.ok(ApiResponse.<List<DeviceDto>>builder()
                .status("SUCCESS")
                .message("Devices fetched successfully")
                .data(devices)
                .build());
    }
}
