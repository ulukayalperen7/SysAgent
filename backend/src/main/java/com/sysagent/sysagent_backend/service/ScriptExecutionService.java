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
     * Entry point for script execution. Detects OS and chooses the right runner.
     */
    public String executeScript(String script) {
        // Decode HTML entities (AI sometimes sends &amp;&amp; for chained commands)
        String decodedScript = script.replace("&amp;&amp;", "&&")
                                     .replace("&amp;", "&")
                                     .replace("&lt;", "<")
                                     .replace("&gt;", ">")
                                     .replace("&quot;", "\"")
                                     .replace("&#39;", "'");
        
        String os = System.getProperty("os.name").toLowerCase();
        if (os.contains("win")) {
            return executePowerShell(decodedScript);
        } else {
            return executeBash(decodedScript);
        }
    }

    /**
     * Executes a PowerShell script securely by Base64 encoding it.
     */
    private String executePowerShell(String script) {
        log.info("Executing PowerShell script on Windows...");
        try {
            String encodedCommand = Base64.getEncoder().encodeToString(script.getBytes(StandardCharsets.UTF_16LE));
            ProcessBuilder pb = new ProcessBuilder("powershell.exe", "-ExecutionPolicy", "Bypass", "-NoProfile", "-EncodedCommand", encodedCommand);
            return runProcess(pb);
        } catch (Exception e) {
            log.error("PowerShell execution failed", e);
            return "Error: " + e.getMessage();
        }
    }

    /**
     * Executes a Bash script on Linux/macOS.
     */
    private String executeBash(String script) {
        log.info("Executing Bash script on Unix-like system...");
        try {
            // We use 'bash -c' for direct execution. 
            // Note: For absolute security, we could write to a temp file, but 'bash -c' is standard for quick tasks.
            ProcessBuilder pb = new ProcessBuilder("bash", "-c", script);
            return runProcess(pb);
        } catch (Exception e) {
            log.error("Bash execution failed", e);
            return "Error: " + e.getMessage();
        }
    }

    private String runProcess(ProcessBuilder pb) throws Exception {
        StringBuilder output = new StringBuilder();
        pb.redirectErrorStream(true);
        Process process = pb.start();

        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append(System.lineSeparator());
            }
        }

        int exitCode = process.waitFor();
        String result = output.toString();

        if (result.contains("#< CLIXML")) {
            result = cleanPowerShellOutput(result);
        }

        if (exitCode != 0) {
            return "Finished with Errors (Code " + exitCode + "):\n" + result;
        }
        return result;
    }

    private String cleanPowerShellOutput(String rawOutput) {
        return rawOutput.replaceAll("<[^>]*>", "")
                        .replaceAll("_x000D__x000A_", "\n")
                        .replaceAll("&lt;", "<")
                        .replaceAll("&gt;", ">")
                        .trim();
    }
}
