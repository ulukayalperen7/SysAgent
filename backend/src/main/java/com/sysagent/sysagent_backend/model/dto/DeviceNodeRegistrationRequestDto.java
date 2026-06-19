package com.sysagent.sysagent_backend.model.dto;

import com.sysagent.sysagent_backend.model.enums.DeviceType;

import lombok.Data;

@Data
public class DeviceNodeRegistrationRequestDto {

    private String token;
    private String name;
    private String ipAddress;
    private DeviceType type;
}
