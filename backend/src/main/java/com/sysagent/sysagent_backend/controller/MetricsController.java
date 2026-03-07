package com.sysagent.sysagent_backend.controller;

import com.sysagent.sysagent_backend.model.MetricsDto;
import com.sysagent.sysagent_backend.service.MetricsService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/metrics")
@RequiredArgsConstructor
@CrossOrigin(origins = "*") // Allow Angular frontend to call this
public class MetricsController {

    private final MetricsService metricsService;

    @GetMapping
    public ResponseEntity<MetricsDto> getSystemMetrics() {
        return ResponseEntity.ok(metricsService.getSystemMetrics());
    }
}
