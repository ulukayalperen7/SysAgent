package com.sysagent.sysagent_backend.security;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

import com.sysagent.sysagent_backend.config.AuthProperties;

class JwtTokenServiceTest {

    @Test
    void createsAndValidatesSignedToken() {
        AuthProperties properties = new AuthProperties();
        properties.setJwtSecret("test-secret-that-is-long-enough-for-hmac");
        properties.setJwtExpirationSeconds(3600);
        JwtTokenService tokenService = new JwtTokenService(properties);

        String token = tokenService.createToken(new AuthenticatedUser("user-1", "user@example.com", "User"));
        AuthenticatedUser user = tokenService.validateToken(token);

        assertThat(user.id()).isEqualTo("user-1");
        assertThat(user.email()).isEqualTo("user@example.com");
    }
}
