package com.sysagent.sysagent_backend.service;

import com.sysagent.sysagent_backend.model.MetricsDto;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.lang.management.ManagementFactory;
import com.sun.management.OperatingSystemMXBean;

@Slf4j
@Service
public class MetricsService {

    public MetricsDto getSystemMetrics() {
        OperatingSystemMXBean osBean = ManagementFactory.getPlatformMXBean(OperatingSystemMXBean.class);
        
        // Return percentage (0.0 to 100.0)
        double cpuLoad = osBean.getCpuLoad() * 100;
        
        long totalMemory = osBean.getTotalMemorySize();
        long freeMemory = osBean.getFreeMemorySize();
        long usedMemory = totalMemory - freeMemory;
        
        log.debug("Fetched system metrics: CPU Load: {}%, Used RAM: {}/{}", cpuLoad, usedMemory, totalMemory);
        
        return MetricsDto.builder()
                .cpuLoadPercentage(cpuLoad)
                .totalRamBytes(totalMemory)
                .availableRamBytes(freeMemory)
                .usedRamBytes(usedMemory)
                .build();
    }
}
