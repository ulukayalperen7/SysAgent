package com.sysagent.sysagent_backend.security;

public record AuthenticatedUser(String id, String email, String displayName) {
}
