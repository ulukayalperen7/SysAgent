package com.sysagent.sysagent_backend.security;

import org.springframework.stereotype.Component;

@Component
public class CurrentUserProvider {

    private static final ThreadLocal<AuthenticatedUser> CURRENT_USER = new ThreadLocal<>();

    public String getCurrentUserId() {
        return getCurrentUser().id();
    }

    public AuthenticatedUser getCurrentUser() {
        AuthenticatedUser user = CURRENT_USER.get();
        if (user == null) {
            throw new IllegalStateException("No authenticated user is bound to the current request.");
        }
        return user;
    }

    public void setCurrentUser(AuthenticatedUser user) {
        CURRENT_USER.set(user);
    }

    public void clear() {
        CURRENT_USER.remove();
    }
}
