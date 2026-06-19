package com.sysagent.sysagent_backend.security;

import java.time.Clock;
import java.time.Instant;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.springframework.stereotype.Component;

import com.sysagent.sysagent_backend.config.SecurityProperties;

import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class AuthRateLimiter {

    private final SecurityProperties securityProperties;
    private final Clock clock = Clock.systemUTC();
    private final Map<String, Window> attempts = new ConcurrentHashMap<>();

    public boolean allowLogin(String clientIp, String email) {
        SecurityProperties.AuthRateLimit limits = securityProperties.getAuthRateLimit();
        return allow("login", clientIp, normalize(email), limits.getLoginMaxAttempts(), limits.getLoginWindowSeconds());
    }

    public boolean allowRegister(String clientIp, String email) {
        SecurityProperties.AuthRateLimit limits = securityProperties.getAuthRateLimit();
        return allow("register", clientIp, normalize(email), limits.getRegisterMaxAttempts(), limits.getRegisterWindowSeconds());
    }

    private boolean allow(String scope, String clientIp, String email, int maxAttempts, long windowSeconds) {
        if (maxAttempts <= 0 || windowSeconds <= 0) {
            return true;
        }
        String key = scope + "|" + safe(clientIp) + "|" + email;
        Instant now = Instant.now(clock);
        Window updated = attempts.compute(key, (ignored, current) -> {
            if (current == null || !now.isBefore(current.expiresAt())) {
                return new Window(1, now.plusSeconds(windowSeconds));
            }
            return new Window(current.count() + 1, current.expiresAt());
        });
        return updated.count() <= maxAttempts;
    }

    private String normalize(String email) {
        return email == null ? "" : email.trim().toLowerCase(Locale.ROOT);
    }

    private String safe(String value) {
        return value == null || value.isBlank() ? "unknown" : value.trim();
    }

    private record Window(int count, Instant expiresAt) {
    }
}
