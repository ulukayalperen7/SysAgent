package com.sysagent.sysagent_backend.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

/**
 * Global application configuration.
 * Defines shared beans like RestTemplate for HTTP calls to the AI Engine.
 */
@Configuration
public class AppConfig {

    @Bean
    public RestTemplate restTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();

        // Connection timeout: fail fast if the AI Engine isn't listening at all
        factory.setConnectTimeout(5_000);  // 5 seconds

        // Read timeout: the AI crew can take time to process (4 agents × ~15s avg)
        // 120 seconds gives enough headroom for slow LLM calls
        factory.setReadTimeout(120_000);   // 120 seconds

        return new RestTemplate(factory);
    }
}
