package com.sysagent.sysagent_backend.security;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

import com.sysagent.sysagent_backend.config.SecurityProperties;

class AuthRateLimiterTest {

    @Test
    void limitsLoginAttemptsPerIpAndEmail() {
        SecurityProperties properties = new SecurityProperties();
        properties.getAuthRateLimit().setLoginMaxAttempts(2);
        properties.getAuthRateLimit().setLoginWindowSeconds(600);
        AuthRateLimiter limiter = new AuthRateLimiter(properties);

        assertThat(limiter.allowLogin("127.0.0.1", "USER@example.com")).isTrue();
        assertThat(limiter.allowLogin("127.0.0.1", "user@example.com")).isTrue();
        assertThat(limiter.allowLogin("127.0.0.1", "user@example.com")).isFalse();
    }

    @Test
    void limitsRegistrationAttemptsPerIpAndEmail() {
        SecurityProperties properties = new SecurityProperties();
        properties.getAuthRateLimit().setRegisterMaxAttempts(1);
        properties.getAuthRateLimit().setRegisterWindowSeconds(600);
        AuthRateLimiter limiter = new AuthRateLimiter(properties);

        assertThat(limiter.allowRegister("127.0.0.1", "a@example.com")).isTrue();
        assertThat(limiter.allowRegister("127.0.0.1", "a@example.com")).isFalse();
        assertThat(limiter.allowRegister("127.0.0.2", "a@example.com")).isTrue();
    }
}
