package com.sysagent.sysagent_backend.config;

import java.util.ArrayList;
import java.util.List;

import org.springframework.boot.context.properties.ConfigurationProperties;

import lombok.Data;

@Data
@ConfigurationProperties(prefix = "sysagent.security")
public class SecurityProperties {

    private boolean production = false;
    private boolean trustForwardedFor = false;
    private Cors cors = new Cors();
    private AuthRateLimit authRateLimit = new AuthRateLimit();

    @Data
    public static class Cors {
        private List<String> allowedOrigins = new ArrayList<>(
                List.of("http://localhost:4200", "http://127.0.0.1:4200"));
    }

    @Data
    public static class AuthRateLimit {
        private int loginMaxAttempts = 10;
        private long loginWindowSeconds = 600;
        private int registerMaxAttempts = 5;
        private long registerWindowSeconds = 1800;
    }
}
