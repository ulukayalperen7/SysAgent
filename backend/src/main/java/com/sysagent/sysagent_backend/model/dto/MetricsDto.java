package com.sysagent.sysagent_backend.model.dto;

import lombok.Builder;
import lombok.Data;

/**
 * Encapsulates system performance metrics (CPU, RAM, Disk) sent from a device.
 * Used for real-time monitoring and dashboard visualization.
 */
@Data
@Builder
public class MetricsDto {
    // OS and CPU Information
    /**
     * Operating System name (e.g., "Windows 11", "Ubuntu 22.04").
     */
    private String osName;
    
    /**
     * Kernel or OS version string.
     */
    private String osVersion;
    
    /**
     * Number of logical CPU cores available.
     */
    private int cpuCores;
    
    /**
     * Current CPU load as a percentage (0.0 to 100.0).
     */
    private double cpuLoadPercentage;
    
    /**
     * System uptime in seconds since last boot.
     */
    private long systemUptimeSeconds;

    // RAM Information
    /**
     * Total physical memory in bytes.
     */
    private long totalRamBytes;
    
    /**
     * Available physical memory in bytes.
     */
    private long availableRamBytes;
    
    /**
     * Memory currently in use in bytes.
     */
    private long usedRamBytes;

    // Disk Information (Focuses on primary drive usually)
    /**
     * Total storage capacity of the primary disk in bytes.
     */
    private long totalDiskBytes;
    
    /**
     * Free storage space on the primary disk in bytes.
     */
    private long freeDiskBytes;
    
    /**
     * Used storage space on the primary disk in bytes.
     */
    private long usedDiskBytes;
}
