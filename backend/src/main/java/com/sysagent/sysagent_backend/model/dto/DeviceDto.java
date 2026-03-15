package com.sysagent.sysagent_backend.model.dto;

import java.time.LocalDateTime;

import com.sysagent.sysagent_backend.model.enums.DeviceType;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Data Transfer Object for transferring device information between frontend and backend.
 * Avoids exposing the raw entity structure directly to the API consumers.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DeviceDto {
    
    private Long id;
    
    /**
     * Friendly name of the device.
     */
    private String name;
    
    /**
     * Connection status (e.g., "ONLINE", "OFFLINE").
     */
    private String status;
    
    /**
     * Type of operating system (WINDOWS, LINUX, MACOS).
     */
    private DeviceType type;
    
    /**
     * IP address used for connection (might be masked in future for security).
     */
    private String ipAddress;
    
    /**
     * Last time the device was successfully pinged or sent metrics.
     */
    private LocalDateTime lastSeen;

    // These fields might be moved to a separate MetricsDto linked to the device 
    // to keep this DTO lightweight for list views.
    private Integer cpuUsage;
    private Integer ramUsage;
}
