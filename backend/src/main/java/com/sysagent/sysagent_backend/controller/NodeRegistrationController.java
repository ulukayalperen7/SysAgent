package com.sysagent.sysagent_backend.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.sysagent.sysagent_backend.model.dto.DeviceDto;
import com.sysagent.sysagent_backend.model.dto.DeviceNodeRegistrationRequestDto;
import com.sysagent.sysagent_backend.model.response.ApiResponse;
import com.sysagent.sysagent_backend.service.DeviceService;

import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/api/node")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class NodeRegistrationController {

    private final DeviceService deviceService;

    @PostMapping("/register")
    public ResponseEntity<ApiResponse<DeviceDto>> registerNode(
            @RequestBody DeviceNodeRegistrationRequestDto request,
            HttpServletRequest servletRequest) {
        try {
            DeviceDto device = deviceService.registerNode(request, servletRequest.getRemoteAddr());
            return ResponseEntity.ok(ApiResponse.success(device, "Device registered successfully"));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(ApiResponse.error(e.getMessage()));
        }
    }
}
