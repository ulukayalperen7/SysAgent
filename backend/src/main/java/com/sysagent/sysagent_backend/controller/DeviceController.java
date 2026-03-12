package com.sysagent.sysagent_backend.controller;

import com.sysagent.sysagent_backend.model.DeviceDto;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/devices")
@CrossOrigin(origins = "*") // Allow Angular frontend to call this
public class DeviceController {

    @GetMapping
    public ResponseEntity<List<DeviceDto>> getConnectedDevices() {
        // Mock data moved from Frontend to Backend to test API connection
        return ResponseEntity.ok(List.of(
            DeviceDto.builder().id(1L).name("Main Rig (Windows 11)").status("online").cpu(34).ram(45).type("windows").build(),
            DeviceDto.builder().id(2L).name("Work MacBook (macOS Sonoma)").status("offline").cpu(0).ram(0).type("macos").build()
        ));
    }
}
