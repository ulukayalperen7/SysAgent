package com.sysagent.sysagent_backend.security;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class PasswordHasherTest {

    private final PasswordHasher passwordHasher = new PasswordHasher();

    @Test
    void hashesAndVerifiesPasswordWithoutStoringPlainText() {
        String hash = passwordHasher.hash("strong-password");

        assertThat(hash).doesNotContain("strong-password");
        assertThat(passwordHasher.verify("strong-password", hash)).isTrue();
        assertThat(passwordHasher.verify("wrong-password", hash)).isFalse();
    }
}
