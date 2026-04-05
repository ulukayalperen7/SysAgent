package com.sysagent.sysagent_backend.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import lombok.Data;

/**
 * AI Engine HTTP client settings (URL and timeouts). Bound from {@code ai.engine.*} in application.properties.
 */
@Data
@ConfigurationProperties(prefix = "ai.engine")
public class AiEngineProperties {

    /**
     * Base URL of the FastAPI service (no trailing slash).
     */
    private String url = "http://localhost:8001";

    /**
     * Milliseconds to wait when opening the TCP connection to the AI Engine.
     */
    private int connectTimeoutMs = 5_000;

    /**
     * Milliseconds to wait for the full HTTP response (Crew runs can be slow).
     */
    private int readTimeoutMs = 120_000;
}
