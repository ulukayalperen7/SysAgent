package com.sysagent.sysagent_backend.security;

import org.springframework.stereotype.Component;

import com.sysagent.sysagent_backend.service.AgentHubService;

import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class ScriptPolicyValidator {

    private static final String[] BLACKLISTED_COMMANDS = {
            "rm -rf /", "mkfs", "dd if=", "shutdown", "reboot", "del /s /q c:\\"
    };

    private static final String[] WINDOWS_RED_ZONES = {
            "c:\\windows", "c:\\program files", "c:\\programdata", "c:\\users\\all users"
    };

    private static final String[] UNIX_RED_ZONES = {
            "/etc", "/bin", "/sbin", "/usr/bin", "/usr/sbin", "/root", "/var/lib", "/boot", "/sys", "/dev"
    };

    private final AgentHubService agentHubService;

    public PolicyDecision validate(String script, String osName) {
        if (script == null || script.isBlank()) {
            return PolicyDecision.allow();
        }

        String lowerScript = script.toLowerCase();
        String policyReason = agentHubService.findCommandBlockReason(script, osName);
        if (policyReason != null && !policyReason.isBlank()) {
            return PolicyDecision.block("Agent Hub policy blocked this command: " + policyReason);
        }

        for (String command : BLACKLISTED_COMMANDS) {
            if (lowerScript.contains(command)) {
                return PolicyDecision.block("Blocked critical command pattern: " + command);
            }
        }

        if (osName.toLowerCase().contains("win")) {
            for (String zone : WINDOWS_RED_ZONES) {
                if (lowerScript.contains(zone)) {
                    return PolicyDecision.block("Blocked mutation against protected Windows path: " + zone);
                }
            }
        } else {
            for (String zone : UNIX_RED_ZONES) {
                if (lowerScript.startsWith(zone) || lowerScript.contains(" " + zone)) {
                    return PolicyDecision.block("Blocked mutation against protected system path: " + zone);
                }
            }
        }

        return PolicyDecision.allow();
    }

    public record PolicyDecision(boolean allowed, String reason) {

        public static PolicyDecision allow() {
            return new PolicyDecision(true, "Allowed");
        }

        public static PolicyDecision block(String reason) {
            return new PolicyDecision(false, reason);
        }
    }
}
