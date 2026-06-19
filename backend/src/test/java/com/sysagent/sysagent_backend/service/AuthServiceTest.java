package com.sysagent.sysagent_backend.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import java.time.LocalDateTime;
import java.util.Optional;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.sysagent.sysagent_backend.config.AuthProperties;
import com.sysagent.sysagent_backend.model.dto.AuthLoginRequestDto;
import com.sysagent.sysagent_backend.model.dto.AuthRegisterRequestDto;
import com.sysagent.sysagent_backend.model.dto.AuthResponseDto;
import com.sysagent.sysagent_backend.model.entity.AppUserEntity;
import com.sysagent.sysagent_backend.repository.AppUserRepository;
import com.sysagent.sysagent_backend.security.JwtTokenService;
import com.sysagent.sysagent_backend.security.PasswordHasher;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

    @Mock
    private AppUserRepository appUserRepository;

    private final PasswordHasher passwordHasher = new PasswordHasher();
    private final JwtTokenService jwtTokenService = new JwtTokenService(testAuthProperties());

    @InjectMocks
    private AuthService authService;

    @Test
    void registersUserWithNormalizedEmailAndToken() {
        AuthRegisterRequestDto request = new AuthRegisterRequestDto();
        request.setEmail("USER@Example.COM");
        request.setPassword("strong-password");
        request.setDisplayName("Test User");

        when(appUserRepository.existsByEmail("user@example.com")).thenReturn(false);
        when(appUserRepository.save(any(AppUserEntity.class))).thenAnswer(invocation -> invocation.getArgument(0));
        authService = new AuthService(appUserRepository, passwordHasher, jwtTokenService);

        AuthResponseDto response = authService.register(request);

        assertThat(response.getToken()).isNotBlank();
        assertThat(response.getUser().getEmail()).isEqualTo("user@example.com");
    }

    @Test
    void logsInWithStoredPasswordHash() {
        String hash = passwordHasher.hash("strong-password");
        AppUserEntity user = AppUserEntity.builder()
                .id("user-1")
                .email("user@example.com")
                .passwordHash(hash)
                .displayName("Test User")
                .status("active")
                .createdAt(LocalDateTime.now())
                .updatedAt(LocalDateTime.now())
                .build();
        AuthLoginRequestDto request = new AuthLoginRequestDto();
        request.setEmail("user@example.com");
        request.setPassword("strong-password");

        when(appUserRepository.findByEmail("user@example.com")).thenReturn(Optional.of(user));
        when(appUserRepository.save(any(AppUserEntity.class))).thenAnswer(invocation -> invocation.getArgument(0));
        authService = new AuthService(appUserRepository, passwordHasher, jwtTokenService);

        AuthResponseDto response = authService.login(request);

        assertThat(response.getToken()).isNotBlank();
        assertThat(response.getUser().getId()).isEqualTo("user-1");
    }

    private static AuthProperties testAuthProperties() {
        AuthProperties properties = new AuthProperties();
        properties.setJwtSecret("test-secret-that-is-long-enough-for-hmac");
        properties.setJwtExpirationSeconds(3600);
        return properties;
    }
}
