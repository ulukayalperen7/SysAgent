package com.sysagent.sysagent_backend.model.dto;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Typed status contract for the AI Engine runtime.
 *
 * The Python AI Engine reports health with snake_case fields. This DTO converts
 * that payload into a stable camelCase API contract for the frontend.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AiRuntimeStatusDto {

    private RuntimeSummaryDto runtime;
    private AgentHubSummaryDto agentHub;
    private CheckpointSummaryDto checkpoint;
    private McpSummaryDto mcp;

    public static AiRuntimeStatusDto fromPayload(Map<String, Object> payload) {
        return AiRuntimeStatusDto.builder()
                .runtime(runtimeFrom(section(payload, "runtime")))
                .agentHub(agentHubFrom(section(payload, "agent_hub")))
                .checkpoint(checkpointFrom(section(payload, "checkpoint")))
                .mcp(mcpFrom(section(payload, "mcp")))
                .build();
    }

    public static AiRuntimeStatusDto unavailable(String status, String detail) {
        return AiRuntimeStatusDto.builder()
                .runtime(RuntimeSummaryDto.builder()
                        .status(status)
                        .detail(detail)
                        .requiredMissing(List.of())
                        .optionalMissing(List.of())
                        .dependencies(Map.of())
                        .build())
                .agentHub(AgentHubSummaryDto.builder()
                        .source("unavailable")
                        .routeCount(0)
                        .promptAgents(List.of())
                        .build())
                .checkpoint(CheckpointSummaryDto.builder()
                        .configuredBackend("unknown")
                        .activeBackend("unknown")
                        .databaseUrlConfigured(false)
                        .build())
                .mcp(McpSummaryDto.builder()
                        .available(false)
                        .mode("unavailable")
                        .detail(detail)
                        .tools(List.of())
                        .build())
                .build();
    }

    private static RuntimeSummaryDto runtimeFrom(Map<String, Object> data) {
        return RuntimeSummaryDto.builder()
                .status(stringValue(data.get("status"), "unknown"))
                .detail(stringValue(data.get("detail"), null))
                .requiredMissing(stringList(data.get("required_missing")))
                .optionalMissing(stringList(data.get("optional_missing")))
                .dependencies(dependencies(data.get("dependencies")))
                .build();
    }

    private static AgentHubSummaryDto agentHubFrom(Map<String, Object> data) {
        return AgentHubSummaryDto.builder()
                .source(stringValue(data.get("source"), "unknown"))
                .routeCount(intValue(data.get("route_count")))
                .promptAgents(stringList(data.get("prompt_agents")))
                .build();
    }

    private static CheckpointSummaryDto checkpointFrom(Map<String, Object> data) {
        return CheckpointSummaryDto.builder()
                .configuredBackend(stringValue(data.get("configured_backend"), "unknown"))
                .activeBackend(stringValue(data.get("active_backend"), "unknown"))
                .databaseUrlConfigured(booleanValue(data.get("database_url_configured")))
                .detail(stringValue(data.get("detail"), null))
                .build();
    }

    private static McpSummaryDto mcpFrom(Map<String, Object> data) {
        return McpSummaryDto.builder()
                .available(booleanValue(data.get("available")))
                .mode(stringValue(data.get("mode"), "unknown"))
                .detail(stringValue(data.get("detail"), null))
                .tools(stringList(data.get("tools")))
                .build();
    }

    private static Map<String, DependencyStatusDto> dependencies(Object value) {
        if (!(value instanceof Map<?, ?> rawDependencies)) {
            return Map.of();
        }

        Map<String, DependencyStatusDto> dependencies = new LinkedHashMap<>();
        rawDependencies.forEach((name, rawDependency) -> {
            if (name == null || !(rawDependency instanceof Map<?, ?> dependencyData)) {
                return;
            }
            Map<String, Object> data = objectMap(dependencyData);
            dependencies.put(String.valueOf(name), DependencyStatusDto.builder()
                    .module(stringValue(data.get("module"), ""))
                    .required(booleanValue(data.get("required")))
                    .available(booleanValue(data.get("available")))
                    .purpose(stringValue(data.get("purpose"), ""))
                    .build());
        });
        return Collections.unmodifiableMap(dependencies);
    }

    private static Map<String, Object> section(Map<String, Object> payload, String key) {
        Object value = payload.get(key);
        if (value instanceof Map<?, ?> map) {
            return objectMap(map);
        }
        return Map.of();
    }

    private static Map<String, Object> objectMap(Map<?, ?> source) {
        Map<String, Object> result = new LinkedHashMap<>();
        source.forEach((key, value) -> {
            if (key != null) {
                result.put(String.valueOf(key), value);
            }
        });
        return result;
    }

    private static List<String> stringList(Object value) {
        if (!(value instanceof List<?> list)) {
            return List.of();
        }
        return list.stream()
                .map(String::valueOf)
                .toList();
    }

    private static String stringValue(Object value, String fallback) {
        if (value == null) {
            return fallback;
        }
        String text = String.valueOf(value);
        return text.isBlank() ? fallback : text;
    }

    private static int intValue(Object value) {
        if (value instanceof Number number) {
            return number.intValue();
        }
        try {
            return value == null ? 0 : Integer.parseInt(String.valueOf(value));
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    private static boolean booleanValue(Object value) {
        if (value instanceof Boolean bool) {
            return bool;
        }
        return Boolean.parseBoolean(String.valueOf(value));
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RuntimeSummaryDto {
        private String status;
        private String detail;
        private List<String> requiredMissing;
        private List<String> optionalMissing;
        private Map<String, DependencyStatusDto> dependencies;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class DependencyStatusDto {
        private String module;
        private boolean required;
        private boolean available;
        private String purpose;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class AgentHubSummaryDto {
        private String source;
        private int routeCount;
        private List<String> promptAgents;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class CheckpointSummaryDto {
        private String configuredBackend;
        private String activeBackend;
        private boolean databaseUrlConfigured;
        private String detail;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class McpSummaryDto {
        private boolean available;
        private String mode;
        private String detail;
        private List<String> tools;
    }
}
