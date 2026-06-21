package com.sysagent.sysagent_backend.adapter;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;

import java.util.Map;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpEntity;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestTemplate;

import com.sysagent.sysagent_backend.config.AiEngineProperties;
import com.sysagent.sysagent_backend.model.dto.AgentIntentResponseDto;
import com.sysagent.sysagent_backend.model.dto.DeviceContextSnapshotDto;
import com.sysagent.sysagent_backend.model.dto.DeviceDto;
import com.sysagent.sysagent_backend.model.dto.SystemMetricsDto;
import com.sysagent.sysagent_backend.model.enums.DeviceType;

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
                "thread-1",
                "user-1",
                DeviceDto.builder().id(7L).name("Office PC").type(DeviceType.WINDOWS).status("online").build(),
                DeviceContextSnapshotDto.builder()
                        .activeWindowTitle("Postman")
                        .activeProcessName("Postman.exe")
                        .screenWidth(1920)
                        .screenHeight(1080)
                        .screenshotBase64("abc")
                        .build());

        assertThat(response.getTaskId()).isEqualTo("task-1");
        assertThat(response.getActiveStep()).isEqualTo("create note.txt on desktop");
        assertThat(response.getPendingCount()).isEqualTo(2);
        assertThat(response.getScript()).contains("New-Item");

        ArgumentCaptor<HttpEntity<Map<String, Object>>> captor = ArgumentCaptor.forClass(HttpEntity.class);
        org.mockito.Mockito.verify(restTemplate).postForEntity(eq("http://localhost:8001/analyze"), captor.capture(), eq(Map.class));
        Map<String, Object> payload = captor.getValue().getBody();
        assertThat(payload).containsEntry("owner_id", "user-1");
        assertThat(payload).containsEntry("target_device_id", 7L);
        Map<String, Object> deviceContext = (Map<String, Object>) payload.get("device_context");
        assertThat(deviceContext).containsEntry("execution_mode", "remote_device");
        assertThat((Map<String, Object>) deviceContext.get("screen_context"))
                .containsEntry("active_process_name", "Postman.exe")
                .containsEntry("has_screenshot", true);
        assertThat((Map<String, Object>) deviceContext.get("screen_context"))
                .doesNotContainKey("screen_image_base64");
    }

    @Test
    void includesScreenImageOnlyForScreenContextRequests() {
        when(aiEngineProperties.getUrl()).thenReturn("http://localhost:8001");
        when(restTemplate.postForEntity(eq("http://localhost:8001/analyze"), any(), eq(Map.class)))
                .thenReturn(ResponseEntity.ok(Map.of(
                        "explanation", "Understanding:\nClose active app.",
                        "script", "Stop-Process -Name \"Code\"",
                        "active_step", "close this app",
                        "pending_count", 0)));

        adapter.analyzeIntent(
                "task-2",
                "close this app",
                SystemMetricsDto.builder().osName("Windows 11").build(),
                "thread-1",
                "user-1",
                DeviceDto.builder().id(7L).name("Office PC").type(DeviceType.WINDOWS).status("online").build(),
                DeviceContextSnapshotDto.builder()
                        .activeWindowTitle("Visual Studio Code")
                        .activeProcessName("Code.exe")
                        .screenshotMimeType("image/jpeg")
                        .screenshotBase64("abc")
                        .build());

        ArgumentCaptor<HttpEntity<Map<String, Object>>> captor = ArgumentCaptor.forClass(HttpEntity.class);
        org.mockito.Mockito.verify(restTemplate).postForEntity(eq("http://localhost:8001/analyze"), captor.capture(), eq(Map.class));
        Map<String, Object> deviceContext = (Map<String, Object>) captor.getValue().getBody().get("device_context");
        assertThat((Map<String, Object>) deviceContext.get("screen_context"))
                .containsEntry("screen_image_base64", "abc")
                .containsEntry("screen_image_mime_type", "image/jpeg");
    }

    @Test
    void includesScreenImageForTurkishGuiTargetingRequests() {
        when(aiEngineProperties.getUrl()).thenReturn("http://localhost:8001");
        when(restTemplate.postForEntity(eq("http://localhost:8001/analyze"), any(), eq(Map.class)))
                .thenReturn(ResponseEntity.ok(Map.of(
                        "explanation", "Understanding:\nClick visible target.",
                        "script", "NONE",
                        "active_step", "şunu tıkla",
                        "pending_count", 0)));

        adapter.analyzeIntent(
                "task-3",
                "şunu tıkla",
                SystemMetricsDto.builder().osName("Windows 11").build(),
                "thread-1",
                "user-1",
                DeviceDto.builder().id(7L).name("Office PC").type(DeviceType.WINDOWS).status("online").build(),
                DeviceContextSnapshotDto.builder()
                        .screenshotMimeType("image/jpeg")
                        .screenshotBase64("abc")
                        .build());

        ArgumentCaptor<HttpEntity<Map<String, Object>>> captor = ArgumentCaptor.forClass(HttpEntity.class);
        org.mockito.Mockito.verify(restTemplate).postForEntity(eq("http://localhost:8001/analyze"), captor.capture(), eq(Map.class));
        Map<String, Object> deviceContext = (Map<String, Object>) captor.getValue().getBody().get("device_context");
        assertThat((Map<String, Object>) deviceContext.get("screen_context"))
                .containsEntry("screen_image_base64", "abc");
    }

    @Test
    void includesScreenImageForQueueResumeRequests() {
        when(aiEngineProperties.getUrl()).thenReturn("http://localhost:8001");
        when(restTemplate.postForEntity(eq("http://localhost:8001/analyze"), any(), eq(Map.class)))
                .thenReturn(ResponseEntity.ok(Map.of(
                        "explanation", "Understanding:\nContinue next step.",
                        "script", "NONE",
                        "active_step", "continue",
                        "pending_count", 0)));

        adapter.analyzeIntent(
                "task-4",
                "devam",
                SystemMetricsDto.builder().osName("Windows 11").build(),
                "thread-1",
                "user-1",
                DeviceDto.builder().id(7L).name("Office PC").type(DeviceType.WINDOWS).status("online").build(),
                DeviceContextSnapshotDto.builder()
                        .screenshotMimeType("image/jpeg")
                        .screenshotBase64("abc")
                        .build());

        ArgumentCaptor<HttpEntity<Map<String, Object>>> captor = ArgumentCaptor.forClass(HttpEntity.class);
        org.mockito.Mockito.verify(restTemplate).postForEntity(eq("http://localhost:8001/analyze"), captor.capture(), eq(Map.class));
        Map<String, Object> deviceContext = (Map<String, Object>) captor.getValue().getBody().get("device_context");
        assertThat((Map<String, Object>) deviceContext.get("screen_context"))
                .containsEntry("screen_image_base64", "abc");
    }

    @Test
    void includesScreenImageForVerificationRepairRequests() {
        when(aiEngineProperties.getUrl()).thenReturn("http://localhost:8001");
        when(restTemplate.postForEntity(eq("http://localhost:8001/analyze"), any(), eq(Map.class)))
                .thenReturn(ResponseEntity.ok(Map.of(
                        "explanation", "Understanding:\nRepair the current step.",
                        "script", "NONE",
                        "active_step", "VERIFICATION_FAILED",
                        "pending_count", 0)));

        adapter.analyzeIntent(
                "task-5",
                "VERIFICATION_FAILED: The previous approved desktop action did not verify cleanly.",
                SystemMetricsDto.builder().osName("Windows 11").build(),
                "thread-1",
                "user-1",
                DeviceDto.builder().id(7L).name("Office PC").type(DeviceType.WINDOWS).status("online").build(),
                DeviceContextSnapshotDto.builder()
                        .screenshotMimeType("image/jpeg")
                        .screenshotBase64("abc")
                        .build());

        ArgumentCaptor<HttpEntity<Map<String, Object>>> captor = ArgumentCaptor.forClass(HttpEntity.class);
        org.mockito.Mockito.verify(restTemplate).postForEntity(eq("http://localhost:8001/analyze"), captor.capture(), eq(Map.class));
        Map<String, Object> deviceContext = (Map<String, Object>) captor.getValue().getBody().get("device_context");
        assertThat((Map<String, Object>) deviceContext.get("screen_context"))
                .containsEntry("screen_image_base64", "abc");
    }

    @Test
    void mapsPostCommandVerificationResponse() {
        when(aiEngineProperties.getUrl()).thenReturn("http://localhost:8001");
        when(restTemplate.postForEntity(eq("http://localhost:8001/verify-action"), any(), eq(Map.class)))
                .thenReturn(ResponseEntity.ok(Map.of(
                        "status", "verified",
                        "reason", "The app is visible.",
                        "screen_summary", "The application opened and is visible.")));

        var response = adapter.verifyPostCommand(
                "task-5",
                "open app",
                "ok",
                null,
                DeviceDto.builder().id(7L).name("Office PC").type(DeviceType.WINDOWS).status("online").build(),
                DeviceContextSnapshotDto.builder()
                        .screenshotMimeType("image/jpeg")
                        .screenshotBase64("abc")
                        .build());

        assertThat(response.getStatus()).isEqualTo("verified");
        assertThat(response.getReason()).contains("visible");

        ArgumentCaptor<HttpEntity<Map<String, Object>>> captor = ArgumentCaptor.forClass(HttpEntity.class);
        org.mockito.Mockito.verify(restTemplate).postForEntity(eq("http://localhost:8001/verify-action"), captor.capture(), eq(Map.class));
        Map<String, Object> payload = captor.getValue().getBody();
        assertThat(payload).containsEntry("expected_action", "open app");
        Map<String, Object> deviceContext = (Map<String, Object>) payload.get("device_context");
        assertThat((Map<String, Object>) deviceContext.get("screen_context"))
                .containsEntry("screen_image_base64", "abc");
    }
}
