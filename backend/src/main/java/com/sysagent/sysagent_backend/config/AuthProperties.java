package com.sysagent.sysagent_backend.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import lombok.Data;

@Data
@ConfigurationProperties(prefix = "sysagent.auth")
public class AuthProperties {

    private String jwtSecret = "";
    private long jwtExpirationSeconds = 86400;
}
