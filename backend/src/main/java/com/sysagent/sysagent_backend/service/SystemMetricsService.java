package com.sysagent.sysagent_backend.service;

import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import com.sysagent.sysagent_backend.model.dto.SystemMetricsDto;

import lombok.RequiredArgsConstructor;
import oshi.SystemInfo;
import oshi.hardware.GlobalMemory;
import oshi.hardware.HardwareAbstractionLayer;
import oshi.hardware.NetworkIF;
import oshi.software.os.OperatingSystem;

import java.net.InetAddress;
import java.net.UnknownHostException;

/**
 * Service: Reads OS metrics every 2 seconds in the background and broadcasts them via WebSocket.
 */
@Service
@EnableScheduling // To enable Scheduled annotations
@RequiredArgsConstructor
public class SystemMetricsService {

    private final SimpMessagingTemplate messagingTemplate;

    private final SystemInfo systemInfo = new SystemInfo();
    private final HardwareAbstractionLayer hardware = systemInfo.getHardware();
    private final OperatingSystem os = systemInfo.getOperatingSystem();

    // Requires previous ticks to accurately calculate CPU usage percentage (OSHI method)
    private long[] prevTicks = hardware.getProcessor().getSystemCpuLoadTicks();

    /**
     * Runs every 2000 milliseconds. Reads CPU/RAM and sends to Frontend (Angular).
     */
    @Scheduled(fixedRate = 2000)
    public void readAndBroadcastMetrics() {
        SystemMetricsDto metrics = collectMetrics();
        
        // For development logging (can be removed later)
        // System.out.println("Live CPU: " + metrics.getCpuUsage() + "% - RAM: " + metrics.getRamUsage() + "%");

        // Send the data to the WebSocket `/topic/system-metrics` channel
        messagingTemplate.convertAndSend("/topic/system-metrics", metrics);
    }

    public SystemMetricsDto collectMetrics() {
        // Read RAM
        GlobalMemory memory = hardware.getMemory();
        long totalRam = memory.getTotal();
        long availableRam = memory.getAvailable();
        long usedRam = totalRam - availableRam;

        // Calculate RAM percentage
        int ramPercent = (int) Math.round(((double) usedRam / totalRam) * 100);

        // Read CPU
        // Method to read instantaneous system load between ticks as percentage:
        double cpuLoad = hardware.getProcessor().getSystemCpuLoadBetweenTicks(prevTicks);
        prevTicks = hardware.getProcessor().getSystemCpuLoadTicks(); // Store for next iteration

        int cpuPercent = (int) Math.round(cpuLoad * 100);

        // Uptime & OS
        long uptime = os.getSystemUptime();
        String osName = os.getFamily();
        String osVersion = os.getVersionInfo().getVersion();
        int logicalCores = hardware.getProcessor().getLogicalProcessorCount();
        
        // Basic Networking (Hostname, IP, MAC) - Fast retrieval for local machine
        String hostname = "Unknown";
        String ipAddress = "Unknown";
        String macAddress = "Unknown";
        try {
            InetAddress localHost = InetAddress.getLocalHost();
            hostname = localHost.getHostName();
            ipAddress = localHost.getHostAddress();
            
            // Getting MAC via OSHI (First active interface with a MAC)
            for (NetworkIF net : hardware.getNetworkIFs()) {
                if (net.getMacaddr() != null && !net.getMacaddr().isEmpty() && !net.getMacaddr().startsWith("00:00:00")) {
                    macAddress = net.getMacaddr();
                    break;
                }
            }
        } catch (UnknownHostException e) {
            // Ignore if networking info is unavailable
        }

        return SystemMetricsDto.builder()
                .cpuUsage(cpuPercent)
                .ramUsage(ramPercent)
                .totalRam(totalRam)
                .usedRam(usedRam)
                .cpuCores(logicalCores)
                .osName(osName)
                .osVersion(osVersion)
                .systemUptimeSeconds(uptime)
                .hostname(hostname)
                .ipAddress(ipAddress)
                .macAddress(macAddress)
                .build();
    }

}
