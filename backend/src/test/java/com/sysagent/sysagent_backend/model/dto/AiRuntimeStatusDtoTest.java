package com.sysagent.sysagent_backend.model.dto;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;

class AiRuntimeStatusDtoTest {

    @Test
    void convertsPythonRuntimePayloadToTypedContract() {
        Map<String, Object> payload = Map.of(
                "runtime", Map.of(
                        "status", "ready",
                        "required_missing", List.of(),
                        "optional_missing", List.of("langgraph_checkpoint_postgres"),
                        "dependencies", Map.of(
                                "langgraph", Map.of(
                                        "module", "langgraph",
                                        "required", true,
                                        "available", true,
                                        "purpose", "agent workflow orchestration"))),
                "agent_hub", Map.of(
                        "source", "database",
                        "route_count", 7,
                        "prompt_agents", List.of("terminal_router")),
                "checkpoint", Map.of(
                        "configured_backend", "postgres",
                        "active_backend", "memory",
                        "database_url_configured", "false"),
                "mcp", Map.of(
                        "available", true,
                        "mode", "mcp_streamable_http",
                        "detail", "connected",
                        "tools", List.of("system_get_metrics_snapshot")));

        AiRuntimeStatusDto status = AiRuntimeStatusDto.fromPayload(payload);

        assertThat(status.getRuntime().getStatus()).isEqualTo("ready");
        assertThat(status.getRuntime().getOptionalMissing()).containsExactly("langgraph_checkpoint_postgres");
        assertThat(status.getRuntime().getDependencies().get("langgraph").isRequired()).isTrue();
        assertThat(status.getAgentHub().getSource()).isEqualTo("database");
        assertThat(status.getAgentHub().getRouteCount()).isEqualTo(7);
        assertThat(status.getCheckpoint().isDatabaseUrlConfigured()).isFalse();
        assertThat(status.getMcp().getTools()).containsExactly("system_get_metrics_snapshot");
    }
}
