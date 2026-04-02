package com.sysagent.sysagent_backend.model.dto;

import lombok.Builder;
import lombok.Data;

/**
 * Data Transfer Object for carrying real-time OS metrics.
 */
@Data
@Builder
public class SystemMetricsDto {
    private int cpuUsage; // Percentage CPU usage
    private int ramUsage; // Percentage RAM usage
    private long totalRam; // Total RAM in bytes
    private long usedRam; // Used RAM in bytes
}
