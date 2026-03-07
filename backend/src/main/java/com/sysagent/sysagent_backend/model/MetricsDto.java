package com.sysagent.sysagent_backend.model;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class MetricsDto {
    private double cpuLoadPercentage;
    private long totalRamBytes;
    private long availableRamBytes;
    private long usedRamBytes;
}
