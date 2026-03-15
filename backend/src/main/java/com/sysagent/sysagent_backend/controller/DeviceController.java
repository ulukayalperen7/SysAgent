package com.sysagent.sysagent_backend.controller;

import com.sysagent.sysagent_backend.model.dto.DeviceDto;
import com.sysagent.sysagent_backend.model.response.ApiResponse;
import com.sysagent.sysagent_backend.service.DeviceService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

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

    @GetMapping
    public ResponseEntity<ApiResponse<List<DeviceDto>>> getConnectedDevices() {
        List<DeviceDto> devices = deviceService.getAllDevices();

        return ResponseEntity.ok(ApiResponse.<List<DeviceDto>>builder()
                .status("SUCCESS")
                .message("Devices fetched successfully")
                .data(devices)
                .build());
    }
}
