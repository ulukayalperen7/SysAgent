package com.sysagent.sysagent_backend.model.entity;

import java.time.LocalDateTime;

import com.sysagent.sysagent_backend.model.enums.DeviceType;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Represents a physical or virtual machine managed by SysAgent.
 * Stores core details like hostname, IP, OS type, and last known status.
 */
@Entity
@Table(name = "devices")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DeviceEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * The human-readable name of the device (e.g., "Web Server 01").
     */
    @Column(nullable = false)
    private String name;

    /**
     * IP address or hostname to connect to.
     */
    @Column(nullable = false)
    private String ipAddress;

    /**
     * Current status (e.g., "ONLINE", "OFFLINE").
     * Consider using an Enum for status in the future.
     */
    private String status;

    /**
     * Operating System type (WINDOWS, LINUX, MACOS).
     * Critical for determining compatible scripts.
     */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private DeviceType type;

    /**
     * Last time the device metrics were updated.
     */
    private LocalDateTime lastSeen;

    // Additional fields for hardware specs can be added here or in a separate Specs entity
    // private Integer cpuCores;
    // private Long totalRam;
}
