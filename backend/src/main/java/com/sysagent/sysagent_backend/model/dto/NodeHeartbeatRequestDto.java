package com.sysagent.sysagent_backend.model.dto;

import com.sysagent.sysagent_backend.model.enums.DeviceType;

import lombok.Data;

@Data
public class NodeHeartbeatRequestDto {
    private Long deviceId;
    private String nodeVersion;
    private String hostname;
    private String ipAddress;
    private DeviceType type;
    private Integer cpuUsage;
    private Integer ramUsage;
}
