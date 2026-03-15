package com.sysagent.sysagent_backend.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.sysagent.sysagent_backend.model.dto.MetricsDto;
import com.sysagent.sysagent_backend.model.response.ApiResponse;
import com.sysagent.sysagent_backend.service.MetricsService;

import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/api/metrics")
@RequiredArgsConstructor
@CrossOrigin(origins = "*") // Allow Angular frontend to call this
public class MetricsController {

    private final MetricsService metricsService;

    @GetMapping
    public ResponseEntity<ApiResponse<MetricsDto>> getSystemMetrics() {
        MetricsDto metrics = metricsService.getSystemMetrics();
        return ResponseEntity.ok(ApiResponse.<MetricsDto>builder()
                .status("SUCCESS")
                .message("Metrics fetched successfully")
                .data(metrics)
                .build());
    }
}
