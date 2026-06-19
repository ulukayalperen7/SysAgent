package com.sysagent.sysagent_backend.model.dto;

import java.time.LocalDateTime;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class DeviceRegistrationTokenResponseDto {

    private String token;
    private LocalDateTime expiresAt;
    private String bootstrapCommand;
}
