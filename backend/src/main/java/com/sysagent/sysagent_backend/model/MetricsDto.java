package com.sysagent.sysagent_backend.model;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class MetricsDto {
    // OS and CPU
    private String osName;
    private String osVersion;
    private int cpuCores;
    private double cpuLoadPercentage;
    private long systemUptimeSeconds;

    // RAM
    private long totalRamBytes;
    private long availableRamBytes;
    private long usedRamBytes;

    // Disk (C:\ Drive)
    private long totalDiskBytes;
    private long freeDiskBytes;
    private long usedDiskBytes;
}
