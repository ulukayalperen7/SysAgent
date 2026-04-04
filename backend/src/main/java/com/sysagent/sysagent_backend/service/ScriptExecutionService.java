package com.sysagent.sysagent_backend.service;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Base64;

import org.springframework.stereotype.Service;

import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
public class ScriptExecutionService {

    /**
     * Executes a PowerShell script securely by Base64 encoding it
     * and passing it to the powershell.exe binary. This avoids all
     * quote escaping and injection issues.
     */
    public String executePowerShell(String script) {
        log.info("Starting execution of PowerShell script...");
        StringBuilder output = new StringBuilder();
        try {
            // Encode the script in UTF-16LE as required by PowerShell -EncodedCommand
            String encodedCommand = Base64.getEncoder().encodeToString(script.getBytes(StandardCharsets.UTF_16LE));
            
            ProcessBuilder pb = new ProcessBuilder("powershell.exe", "-ExecutionPolicy", "Bypass", "-NoProfile", "-EncodedCommand", encodedCommand);
            pb.redirectErrorStream(true);
            Process process = pb.start();

            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append(System.lineSeparator());
            }

            int exitCode = process.waitFor();
            log.info("Script executed with exit code {}", exitCode);
            
            String result = output.toString();
            if (result.contains("#< CLIXML")) {
                result = cleanPowerShellOutput(result);
            }

            if (exitCode != 0) {
                log.warn("Script execution returned non-zero code. Output: \n{}", result);
                return "Execution Finished with Errors (Code " + exitCode + "):\n" + result;
            }
            return result;
            
        } catch (Exception e) {
            log.error("Failed to execute script", e);
            throw new RuntimeException("Execution failed: " + e.getMessage());
        }
    }

    /**
     * Strips PowerShell's ugly CLIXML tags from the output string.
     */
    private String cleanPowerShellOutput(String rawOutput) {
        // Remove XML tags like <Objs...>, <S S="Error">, etc.
        // This is a naive but effective way for the terminal UI.
        return rawOutput.replaceAll("<[^>]*>", "")
                        .replaceAll("_x000D__x000A_", "\n")
                        .replaceAll("&lt;", "<")
                        .replaceAll("&gt;", ">")
                        .trim();
    }
}
