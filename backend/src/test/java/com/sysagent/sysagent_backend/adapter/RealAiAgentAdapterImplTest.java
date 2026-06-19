package com.sysagent.sysagent_backend.adapter;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;

import java.util.Map;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestTemplate;

import com.sysagent.sysagent_backend.config.AiEngineProperties;
import com.sysagent.sysagent_backend.model.dto.AgentIntentResponseDto;
import com.sysagent.sysagent_backend.model.dto.SystemMetricsDto;

@ExtendWith(MockitoExtension.class)
class RealAiAgentAdapterImplTest {

    @Mock
    private RestTemplate restTemplate;

    @Mock
    private AiEngineProperties aiEngineProperties;

    @InjectMocks
    private RealAiAgentAdapterImpl adapter;

    @Test
    void mapsStructuredQueueFieldsFromAiEngineResponse() {
        when(aiEngineProperties.getUrl()).thenReturn("http://localhost:8001");
        when(restTemplate.postForEntity(eq("http://localhost:8001/analyze"), any(), eq(Map.class)))
                .thenReturn(ResponseEntity.ok(Map.of(
                        "explanation", "Understanding:\nCreate the file.",
                        "script", "New-Item -ItemType File -Path note.txt",
                        "active_step", "create note.txt on desktop",
                        "pending_count", 2)));

        AgentIntentResponseDto response = adapter.analyzeIntent(
                "task-1",
                "create note.txt then open it",
                SystemMetricsDto.builder().osName("Windows 11").build(),
                "thread-1");

        assertThat(response.getTaskId()).isEqualTo("task-1");
        assertThat(response.getActiveStep()).isEqualTo("create note.txt on desktop");
        assertThat(response.getPendingCount()).isEqualTo(2);
        assertThat(response.getScript()).contains("New-Item");
    }
}
