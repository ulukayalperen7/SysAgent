package com.sysagent.sysagent_backend.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

/**
 * Global application configuration.
 * Defines shared beans like RestTemplate for HTTP calls to the AI Engine.
 */
@Configuration
@EnableConfigurationProperties(AiEngineProperties.class)
public class AppConfig {

    @Bean
    public RestTemplate restTemplate(AiEngineProperties aiEngine) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(aiEngine.getConnectTimeoutMs());
        factory.setReadTimeout(aiEngine.getReadTimeoutMs());
        return new RestTemplate(factory);
    }
}
