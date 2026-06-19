package com.sysagent.sysagent_backend.config;

import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;

class StartupSecurityValidatorTest {

    @Test
    void allowsDevelopmentWithoutJwtSecret() {
        AuthProperties auth = new AuthProperties();
        SecurityProperties security = new SecurityProperties();
        security.setProduction(false);

        assertThatCode(() -> new StartupSecurityValidator(auth, security).run(null))
                .doesNotThrowAnyException();
    }

    @Test
    void requiresStrongJwtSecretInProduction() {
        AuthProperties auth = new AuthProperties();
        auth.setJwtSecret("short");
        SecurityProperties security = new SecurityProperties();
        security.setProduction(true);

        assertThatThrownBy(() -> new StartupSecurityValidator(auth, security).run(null))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("SYSAGENT_AUTH_JWT_SECRET");
    }

    @Test
    void rejectsWildcardCorsInProduction() {
        AuthProperties auth = new AuthProperties();
        auth.setJwtSecret("this-secret-is-long-enough-for-production");
        SecurityProperties security = new SecurityProperties();
        security.setProduction(true);
        security.getCors().setAllowedOrigins(java.util.List.of("*"));

        assertThatThrownBy(() -> new StartupSecurityValidator(auth, security).run(null))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("Wildcard CORS");
    }
}
