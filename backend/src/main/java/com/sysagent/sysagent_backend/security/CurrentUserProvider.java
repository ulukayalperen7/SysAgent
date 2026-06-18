package com.sysagent.sysagent_backend.security;

import org.springframework.stereotype.Component;

/**
 * Single pre-auth ownership boundary. Replace this implementation with the
 * authenticated principal once JWT/Supabase Auth is introduced.
 */
@Component
public class CurrentUserProvider {

    private static final String PRE_AUTH_USER_ID = "test-user-1";

    public String getCurrentUserId() {
        return PRE_AUTH_USER_ID;
    }
}
