package com.sysagent.sysagent_backend.security;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.sysagent.sysagent_backend.service.AgentHubService;

@ExtendWith(MockitoExtension.class)
class ScriptPolicyValidatorTest {

    @Mock
    private AgentHubService agentHubService;

    @InjectMocks
    private ScriptPolicyValidator validator;

    @Test
    void blocksAgentHubPolicyMatchesBeforeExecution() {
        when(agentHubService.findCommandBlockReason("shutdown /s", "Windows 11"))
                .thenReturn("Blocks shutdown commands.");

        ScriptPolicyValidator.PolicyDecision decision = validator.validate("shutdown /s", "Windows 11");

        assertThat(decision.allowed()).isFalse();
        assertThat(decision.reason()).contains("Agent Hub policy blocked");
    }

    @Test
    void blocksStaticRedZoneEvenWhenDatabasePolicyIsUnavailable() {
        ScriptPolicyValidator.PolicyDecision decision = validator.validate(
                "Remove-Item -LiteralPath C:\\Windows\\temp.txt",
                "Windows 11");

        assertThat(decision.allowed()).isFalse();
        assertThat(decision.reason()).contains("protected Windows path");
    }

    @Test
    void allowsNormalUserScopedCommand() {
        ScriptPolicyValidator.PolicyDecision decision = validator.validate(
                "New-Item -ItemType File -Path \"$env:USERPROFILE\\Desktop\\note.txt\"",
                "Windows 11");

        assertThat(decision.allowed()).isTrue();
    }
}
