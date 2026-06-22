package com.sysagent.sysagent_backend.config;

import java.net.URI;

import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;

import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class StartupSecurityValidator implements ApplicationRunner {

    private final AuthProperties authProperties;
    private final SecurityProperties securityProperties;
    private final AiEngineProperties aiEngineProperties;

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
        if (!isLocalAiEngine(aiEngineProperties.getUrl())
                && (aiEngineProperties.getApiKey() == null || aiEngineProperties.getApiKey().isBlank())) {
            throw new IllegalStateException("SYSAGENT_AI_ENGINE_API_KEY is required when AI Engine is remote in production.");
        }
    }

    private boolean isLocalAiEngine(String url) {
        try {
            String host = URI.create(url).getHost();
            return host == null
                    || "localhost".equalsIgnoreCase(host)
                    || "127.0.0.1".equals(host)
                    || "::1".equals(host);
        } catch (Exception e) {
            return false;
        }
    }
}
