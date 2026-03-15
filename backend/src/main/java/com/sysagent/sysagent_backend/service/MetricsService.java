package com.sysagent.sysagent_backend.service;

import com.sysagent.sysagent_backend.model.dto.MetricsDto;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.File;
import java.lang.management.ManagementFactory;
import java.lang.management.RuntimeMXBean;
import com.sun.management.OperatingSystemMXBean;

@Slf4j
@Service
public class MetricsService {

    public MetricsDto getSystemMetrics() {
        OperatingSystemMXBean osBean = ManagementFactory.getPlatformMXBean(OperatingSystemMXBean.class);
        RuntimeMXBean runtimeBean = ManagementFactory.getRuntimeMXBean();
        
        // --- 1. CPU & OS INFO ---
        String osName = osBean.getName();
        String osVersion = osBean.getVersion();
        int cores = osBean.getAvailableProcessors();
        double cpuLoad = osBean.getCpuLoad() * 100; // Returns 0.0 to 100.0
        long uptimeSeconds = runtimeBean.getUptime() / 1000;
        
        // --- 2. RAM INFO ---
        long totalMemory = osBean.getTotalMemorySize();
        long freeMemory = osBean.getFreeMemorySize();
        long usedMemory = totalMemory - freeMemory;
        
        // --- 3. DISK INFO (C:\ Drive) --- 
        File cDrive = new File("C:\\");
        long totalDisk = cDrive.getTotalSpace();
        long freeDisk = cDrive.getFreeSpace();
        long usedDisk = totalDisk - freeDisk;
        
        log.debug("Fetched extended OS metrics. CPU: {}%, RAM: {}/{}", cpuLoad, usedMemory, totalMemory);
        
        return MetricsDto.builder()
                .osName(osName)
                .osVersion(osVersion)
                .cpuCores(cores)
                .cpuLoadPercentage(cpuLoad)
                .systemUptimeSeconds(uptimeSeconds)
                .totalRamBytes(totalMemory)
                .availableRamBytes(freeMemory)
                .usedRamBytes(usedMemory)
                .totalDiskBytes(totalDisk)
                .freeDiskBytes(freeDisk)
                .usedDiskBytes(usedDisk)
                .build();
    }
}
