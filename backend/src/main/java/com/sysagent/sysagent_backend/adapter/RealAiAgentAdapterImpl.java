package com.sysagent.sysagent_backend.adapter;

import java.util.HashMap;
import java.util.Map;

import org.springframework.context.annotation.Primary;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import com.sysagent.sysagent_backend.config.AiEngineProperties;
import com.sysagent.sysagent_backend.model.dto.AgentIntentResponseDto;
import com.sysagent.sysagent_backend.model.dto.SystemMetricsDto;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Component
@Primary // Use this real implementation instead of the mock
@RequiredArgsConstructor
public class RealAiAgentAdapterImpl implements AiAgentAdapter {

    private final RestTemplate restTemplate;
    private final AiEngineProperties aiEngine;

    @Override
    public AgentIntentResponseDto analyzeIntent(String taskId, String intent, SystemMetricsDto metrics) {
        log.info("Analyzing intent for task: {}", taskId);

        // --- Defense-in-depth: Java-side Security Checks ---
        if (intent == null || intent.isBlank()) {
            return fallbackResponse(taskId, "Empty prompt.");
        }
        if (intent.length() > 4000) {
            return fallbackResponse(taskId, "Prompt is too long (max 4000 chars).");
        }
        String lowerIntent = intent.toLowerCase();
        if (lowerIntent.contains("system.exit") || lowerIntent.contains("runtime.exec")) {
            return fallbackResponse(taskId, "Potential Java-level code injection detected.");
        }

        String analyzeEndpoint = aiEngine.getUrl().replaceAll("/$", "") + "/analyze";

        // Prepare the payload
        Map<String, Object> requestPayload = new HashMap<>();
        requestPayload.put("user_prompt", intent);
        requestPayload.put("metrics", metrics);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<Map<String, Object>> requestEntity = new HttpEntity<>(requestPayload, headers);

        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(analyzeEndpoint, requestEntity, Map.class);
            
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Map<String, Object> responseBody = response.getBody();
                
                // --- STRUCTURED JSON PATTERN (Preferred) ---
                String explanation = (String) responseBody.get("explanation");
                String script = normalizeScript(responseBody.get("script"));

                // --- LEGACY STRING-SPLIT PATTERN (Fallback) ---
                if (explanation == null || explanation.isBlank()) {
                    String reply = String.valueOf(responseBody.getOrDefault("reply", ""));
                    if (reply.contains("Explanation:") && reply.contains("Script:")) {
                        String[] parts = reply.split("Script:", 2);
                        explanation = parts[0].replace("Explanation:", "").trim();
                        script = normalizeScript(parts[1].trim());
                    } else {
                        explanation = reply;
                        script = null;
                    }
                }

                int pendingCount = 0;
                Object pendingObj = responseBody.get("pending_count");
                if (pendingObj instanceof Number) {
                    pendingCount = ((Number) pendingObj).intValue();
                }

                log.info("AI response received: explanation={}, script={}, pendingCount={}", explanation, script, pendingCount);

                return AgentIntentResponseDto.builder()
                        .taskId(taskId)
                        .explanation(explanation)
                        .script(script)
                        .confidenceScore(0.95)
                        .pendingCount(pendingCount)
                        .build();
            } else {
                return fallbackResponse(taskId, "AI Engine error: " + response.getStatusCode());
            }
        } catch (Exception e) {
            log.error("AI Engine connection failed: {}", e.getMessage());
            return fallbackResponse(taskId, "AI Engine unreachable on " + aiEngine.getUrl());
        }
    }

    /**
     * Accepts JSON null or NONE; strips markdown fences from script text.
     */
    private static String normalizeScript(Object scriptObj) {
        if (scriptObj == null) {
            return null;
        }
        if (!(scriptObj instanceof String)) {
            return null;
        }
        String raw = ((String) scriptObj).trim();
        if (raw.isEmpty() || "NONE".equalsIgnoreCase(raw)) {
            return null;
        }
        return stripCodeFences(raw);
    }

    private static String stripCodeFences(String raw) {
        return raw.replace("```bash", "")
                .replace("```powershell", "")
                .replace("```", "")
                .trim();
    }

    private AgentIntentResponseDto fallbackResponse(String taskId, String errorReason) {
        // script must be null — NOT a string — so the frontend hides the Approve button
        return AgentIntentResponseDto.builder()
                .taskId(taskId)
                .explanation("⚠ SysAgent Error: " + errorReason)
                .script(null)
                .confidenceScore(0.0)
                .build();
    }
}
