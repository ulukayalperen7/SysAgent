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

        assertThatCode(() -> new StartupSecurityValidator(auth, security, new AiEngineProperties()).run(null))
                .doesNotThrowAnyException();
    }

    @Test
    void requiresStrongJwtSecretInProduction() {
        AuthProperties auth = new AuthProperties();
        auth.setJwtSecret("short");
        SecurityProperties security = new SecurityProperties();
        security.setProduction(true);

        assertThatThrownBy(() -> new StartupSecurityValidator(auth, security, new AiEngineProperties()).run(null))
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

        assertThatThrownBy(() -> new StartupSecurityValidator(auth, security, new AiEngineProperties()).run(null))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("Wildcard CORS");
    }

    @Test
    void requiresAiEngineApiKeyForRemoteProductionEngine() {
        AuthProperties auth = new AuthProperties();
        auth.setJwtSecret("this-secret-is-long-enough-for-production");
        SecurityProperties security = new SecurityProperties();
        security.setProduction(true);
        AiEngineProperties ai = new AiEngineProperties();
        ai.setUrl("https://ai.example.com");

        assertThatThrownBy(() -> new StartupSecurityValidator(auth, security, ai).run(null))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("SYSAGENT_AI_ENGINE_API_KEY");

        ai.setApiKey("shared-secret");
        assertThatCode(() -> new StartupSecurityValidator(auth, security, ai).run(null))
                .doesNotThrowAnyException();
    }
}
