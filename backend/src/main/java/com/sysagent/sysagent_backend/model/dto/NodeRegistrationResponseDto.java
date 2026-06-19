package com.sysagent.sysagent_backend.model.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class NodeRegistrationResponseDto {
    private DeviceDto device;
    private String nodeToken;
    private int heartbeatIntervalSeconds;
}
