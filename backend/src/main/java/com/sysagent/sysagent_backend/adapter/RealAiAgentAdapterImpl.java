package com.sysagent.sysagent_backend.adapter;

import java.util.HashMap;
import java.util.Map;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Primary;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

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

    @Value("${ai.engine.url:http://localhost:8001}")
    private String aiEngineUrl;

    @Override
    public AgentIntentResponseDto analyzeIntent(String taskId, String intent, SystemMetricsDto metrics) {
        log.info("Sending natural language intent to REAL Python AI Engine via FastAPI. Task ID: {}", taskId);

        String analyzeEndpoint = aiEngineUrl + "/analyze";

        // Prepare the payload (mapping to FastAPI AnalyzeRequest)
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
                String reply = (String) responseBody.getOrDefault("reply", "");
                
                // The AI replies in a combined format. We need to parse explanation and script.
                // Since our tasks.yaml guarantees "Explanation:" and "Script:" format, we can parse it.
                String explanation = "Detailed analysis completed by SysAgent AI.";
                String script = reply;

                if (reply.contains("Explanation:") && reply.contains("Script:")) {
                    try {
                        String[] parts = reply.split("Script:", 2);
                        explanation = parts[0].replace("Explanation:", "").trim();
                        script = parts[1].replace("```bash", "").replace("```powershell", "").replace("```", "").trim();
                    } catch (Exception e) {
                        log.warn("Failed to nicely parse AI output format. Proceeding with raw output.");
                    }
                }

                return AgentIntentResponseDto.builder()
                        .taskId(taskId)
                        .explanation(explanation)
                        .script(script)
                        .confidenceScore(0.95)
                        .build();
            } else {
                log.error("AI Engine returned unhappy status: {}", response.getStatusCode());
                return fallbackResponse(taskId, "AI Engine returned an error status.");
            }
        } catch (Exception e) {
            log.error("Failed to connect to Python AI Engine at {}. Error: {}", analyzeEndpoint, e.getMessage());
            return fallbackResponse(taskId, "Could not reach Python AI Engine. Ensure FastAPI is running on port 8001.");
        }
    }

    private AgentIntentResponseDto fallbackResponse(String taskId, String errorReason) {
        return AgentIntentResponseDto.builder()
                .taskId(taskId)
                .explanation("System Error: " + errorReason)
                .script("# Execution Blocked")
                .confidenceScore(0.0)
                .build();
    }
}
