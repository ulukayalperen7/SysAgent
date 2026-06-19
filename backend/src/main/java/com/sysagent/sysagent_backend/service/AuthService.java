package com.sysagent.sysagent_backend.service;

import java.time.LocalDateTime;
import java.util.Locale;
import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.sysagent.sysagent_backend.model.dto.AuthLoginRequestDto;
import com.sysagent.sysagent_backend.model.dto.AuthRegisterRequestDto;
import com.sysagent.sysagent_backend.model.dto.AuthResponseDto;
import com.sysagent.sysagent_backend.model.dto.AuthUserDto;
import com.sysagent.sysagent_backend.model.entity.AppUserEntity;
import com.sysagent.sysagent_backend.repository.AppUserRepository;
import com.sysagent.sysagent_backend.security.AuthenticatedUser;
import com.sysagent.sysagent_backend.security.JwtTokenService;
import com.sysagent.sysagent_backend.security.PasswordHasher;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final AppUserRepository appUserRepository;
    private final PasswordHasher passwordHasher;
    private final JwtTokenService jwtTokenService;

    @Transactional
    public AuthResponseDto register(AuthRegisterRequestDto request) {
        String email = normalizeEmail(request.getEmail());
        validateEmail(email);
        validatePassword(request.getPassword());
        if (appUserRepository.existsByEmail(email)) {
            throw new IllegalArgumentException("Email is already registered.");
        }

        LocalDateTime now = LocalDateTime.now();
        AppUserEntity user = AppUserEntity.builder()
                .id(UUID.randomUUID().toString())
                .email(email)
                .passwordHash(passwordHasher.hash(request.getPassword()))
                .displayName(cleanDisplayName(request.getDisplayName(), email))
                .status("active")
                .createdAt(now)
                .updatedAt(now)
                .lastLoginAt(now)
                .build();
        AppUserEntity saved = appUserRepository.save(user);
        return buildResponse(saved);
    }

    @Transactional
    public AuthResponseDto login(AuthLoginRequestDto request) {
        String email = normalizeEmail(request.getEmail());
        AppUserEntity user = appUserRepository.findByEmail(email)
                .orElseThrow(() -> new IllegalArgumentException("Invalid email or password."));
        if (!"active".equals(user.getStatus()) || !passwordHasher.verify(request.getPassword(), user.getPasswordHash())) {
            throw new IllegalArgumentException("Invalid email or password.");
        }
        user.setLastLoginAt(LocalDateTime.now());
        user.setUpdatedAt(LocalDateTime.now());
        return buildResponse(appUserRepository.save(user));
    }

    @Transactional(readOnly = true)
    public AuthUserDto getUser(String userId) {
        return appUserRepository.findById(userId)
                .map(AuthUserDto::fromEntity)
                .orElseThrow(() -> new IllegalArgumentException("User not found."));
    }

    private AuthResponseDto buildResponse(AppUserEntity user) {
        AuthenticatedUser principal = new AuthenticatedUser(user.getId(), user.getEmail(), user.getDisplayName());
        return AuthResponseDto.builder()
                .token(jwtTokenService.createToken(principal))
                .tokenType("Bearer")
                .expiresInSeconds(jwtTokenService.getExpirationSeconds())
                .user(AuthUserDto.fromEntity(user))
                .build();
    }

    private String normalizeEmail(String email) {
        return email == null ? "" : email.trim().toLowerCase(Locale.ROOT);
    }

    private void validateEmail(String email) {
        if (!email.matches("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$")) {
            throw new IllegalArgumentException("A valid email is required.");
        }
    }

    private void validatePassword(String password) {
        if (password == null || password.length() < 8 || password.length() > 128) {
            throw new IllegalArgumentException("Password must be between 8 and 128 characters.");
        }
    }

    private String cleanDisplayName(String displayName, String email) {
        String cleaned = displayName == null ? "" : displayName.trim();
        if (cleaned.isBlank()) {
            return email.substring(0, email.indexOf('@'));
        }
        return cleaned.length() > 80 ? cleaned.substring(0, 80) : cleaned;
    }
}
