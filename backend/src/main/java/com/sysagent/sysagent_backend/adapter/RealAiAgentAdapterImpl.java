package com.sysagent.sysagent_backend.adapter;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Locale;
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
import com.sysagent.sysagent_backend.model.dto.AiRuntimeStatusDto;
import com.sysagent.sysagent_backend.model.dto.DeviceContextSnapshotDto;
import com.sysagent.sysagent_backend.model.dto.DeviceDto;
import com.sysagent.sysagent_backend.model.dto.SystemMetricsDto;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Component
@Primary
@RequiredArgsConstructor
public class RealAiAgentAdapterImpl implements AiAgentAdapter {

    private final RestTemplate restTemplate;
    private final AiEngineProperties aiEngine;

    @Override
    public AgentIntentResponseDto analyzeIntent(
            String taskId,
            String intent,
            SystemMetricsDto metrics,
            String threadId,
            String ownerId,
            DeviceDto targetDevice,
            DeviceContextSnapshotDto targetContext) {
        log.info("Analyzing intent for task: {}", taskId);

        // --- Defense-in-depth: Java-side Security Checks ---
        if (intent == null || intent.isBlank()) {
            return fallbackResponse(taskId, "Empty prompt.");
        }
        if (intent.length() > 4000) {
            return fallbackResponse(taskId, "Prompt is too long (max 4000 chars).");
        }
        String lowerIntent = intent.toLowerCase(Locale.ROOT);
        if (lowerIntent.contains("system.exit") || lowerIntent.contains("runtime.exec")) {
            return fallbackResponse(taskId, "Potential Java-level code injection detected.");
        }

        String analyzeEndpoint = aiEngine.getUrl().replaceAll("/$", "") + "/analyze";

        // Prepare the payload
        Map<String, Object> requestPayload = new HashMap<>();
        requestPayload.put("task_id", taskId);
        requestPayload.put("user_prompt", intent);
        requestPayload.put("metrics", metrics);
        requestPayload.put("thread_id", threadId);
        requestPayload.put("owner_id", ownerId);
        requestPayload.put("target_device_id", targetDevice == null ? null : targetDevice.getId());
        requestPayload.put("device_context", buildDeviceContext(targetDevice, targetContext, shouldIncludeScreenImage(intent)));

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
                String activeStep = normalizeText(responseBody.get("active_step"));

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
                        .activeStep(activeStep)
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

    @Override
    public AiRuntimeStatusDto getRuntimeStatus() {
        String statusEndpoint = aiEngine.getUrl().replaceAll("/$", "") + "/runtime/status";

        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(statusEndpoint, Map.class);
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                return AiRuntimeStatusDto.fromPayload(response.getBody());
            }
            return AiRuntimeStatusDto.unavailable(
                    "unavailable",
                    "AI Engine status returned " + response.getStatusCode());
        } catch (Exception e) {
            log.error("AI Engine runtime status failed: {}", e.getMessage());
            return AiRuntimeStatusDto.unavailable(
                    "unreachable",
                    "AI Engine unreachable on " + aiEngine.getUrl());
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

    private static String normalizeText(Object textObj) {
        if (!(textObj instanceof String)) {
            return null;
        }
        String value = ((String) textObj).trim();
        return value.isEmpty() ? null : value;
    }

    private static Map<String, Object> buildDeviceContext(
            DeviceDto targetDevice,
            DeviceContextSnapshotDto targetContext,
            boolean includeScreenImage) {
        Map<String, Object> context = new LinkedHashMap<>();
        context.put("execution_mode", targetDevice == null ? "local_backend" : "remote_device");
        if (targetDevice == null) {
            return context;
        }
        context.put("id", targetDevice.getId());
        context.put("name", targetDevice.getName());
        context.put("type", targetDevice.getType() == null ? null : targetDevice.getType().name());
        context.put("status", targetDevice.getStatus());
        context.put("last_seen", targetDevice.getLastSeen() == null ? null : targetDevice.getLastSeen().toString());
        if (targetContext != null) {
            Map<String, Object> screenContext = new LinkedHashMap<>();
            screenContext.put("captured_at", targetContext.getCapturedAt() == null ? null : targetContext.getCapturedAt().toString());
            screenContext.put("active_window_title", targetContext.getActiveWindowTitle());
            screenContext.put("active_process_name", targetContext.getActiveProcessName());
            screenContext.put("screen_width", targetContext.getScreenWidth());
            screenContext.put("screen_height", targetContext.getScreenHeight());
            screenContext.put("has_screenshot", targetContext.getScreenshotBase64() != null && !targetContext.getScreenshotBase64().isBlank());
            if (includeScreenImage && targetContext.getScreenshotBase64() != null && !targetContext.getScreenshotBase64().isBlank()) {
                screenContext.put("screen_image_mime_type", targetContext.getScreenshotMimeType());
                screenContext.put("screen_image_base64", targetContext.getScreenshotBase64());
            }
            context.put("screen_context", screenContext);
        }
        return context;
    }

    private static boolean shouldIncludeScreenImage(String intent) {
        if (intent == null) {
            return false;
        }
        String lower = normalizeForMatching(intent);
        return lower.contains("screen")
                || lower.contains("screenshot")
                || lower.contains("ekran")
                || lower.contains("goru")
                || lower.contains("this")
                || lower.contains("that")
                || lower.contains("bunu")
                || lower.contains("sunu")
                || lower.contains("current")
                || lower.contains("active")
                || lower.contains("click")
                || lower.contains("tikla");
    }

    private static String normalizeForMatching(String value) {
        return value.toLowerCase(Locale.ROOT)
                .replace('ç', 'c')
                .replace('ğ', 'g')
                .replace('ı', 'i')
                .replace('ö', 'o')
                .replace('ş', 's')
                .replace('ü', 'u');
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
