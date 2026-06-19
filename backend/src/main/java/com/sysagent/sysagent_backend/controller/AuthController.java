package com.sysagent.sysagent_backend.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.sysagent.sysagent_backend.model.dto.AuthLoginRequestDto;
import com.sysagent.sysagent_backend.model.dto.AuthRegisterRequestDto;
import com.sysagent.sysagent_backend.model.dto.AuthResponseDto;
import com.sysagent.sysagent_backend.model.dto.AuthUserDto;
import com.sysagent.sysagent_backend.model.response.ApiResponse;
import com.sysagent.sysagent_backend.security.CurrentUserProvider;
import com.sysagent.sysagent_backend.service.AuthService;

import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class AuthController {

    private final AuthService authService;
    private final CurrentUserProvider currentUserProvider;

    @PostMapping("/register")
    public ResponseEntity<ApiResponse<AuthResponseDto>> register(@RequestBody AuthRegisterRequestDto request) {
        try {
            return ResponseEntity.ok(ApiResponse.success(authService.register(request), "Registered successfully"));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(ApiResponse.error(e.getMessage()));
        }
    }

    @PostMapping("/login")
    public ResponseEntity<ApiResponse<AuthResponseDto>> login(@RequestBody AuthLoginRequestDto request) {
        try {
            return ResponseEntity.ok(ApiResponse.success(authService.login(request), "Logged in successfully"));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(ApiResponse.error(e.getMessage()));
        }
    }

    @GetMapping("/me")
    public ResponseEntity<ApiResponse<AuthUserDto>> me() {
        return ResponseEntity.ok(ApiResponse.success(
                authService.getUser(currentUserProvider.getCurrentUserId()),
                "Current user loaded"));
    }
}
