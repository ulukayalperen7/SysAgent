package com.sysagent.sysagent_backend.config;

import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;

import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class StartupSecurityValidator implements ApplicationRunner {

    private final AuthProperties authProperties;
    private final SecurityProperties securityProperties;

    @Override
    public void run(ApplicationArguments args) {
        if (!securityProperties.isProduction()) {
            return;
        }
        if (authProperties.getJwtSecret() == null || authProperties.getJwtSecret().length() < 32) {
            throw new IllegalStateException("SYSAGENT_AUTH_JWT_SECRET must be at least 32 characters in production.");
        }
        if (securityProperties.getCors().getAllowedOrigins().stream().anyMatch("*"::equals)) {
            throw new IllegalStateException("Wildcard CORS origins are not allowed in production.");
        }
    }
}
