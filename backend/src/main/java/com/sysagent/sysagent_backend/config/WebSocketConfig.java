package com.sysagent.sysagent_backend.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;

/**
 * Configuration for WebSocket to stream real-time metrics to the frontend.
 */
@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    @Override
    public void configureMessageBroker(MessageBrokerRegistry config) {
        // Messages whose destination starts with /topic will be routed to the message broker
        config.enableSimpleBroker("/topic");
        // Messages whose destination starts with /app are routed to @MessageMapping methods
        config.setApplicationDestinationPrefixes("/app");
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        // The endpoint /ws-metrics is what Angular will connect to
        registry.addEndpoint("/ws-metrics")
                .setAllowedOriginPatterns("*") // Allow all origins for development
                .withSockJS(); // Fallback option if WebSocket is not supported
    }
}
