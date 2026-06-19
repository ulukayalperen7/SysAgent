package com.sysagent.sysagent_backend.security;

import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.time.Instant;
import java.util.Base64;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

import org.springframework.stereotype.Component;

import com.sysagent.sysagent_backend.config.AuthProperties;

import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class JwtTokenService {

    private static final String HMAC_ALGORITHM = "HmacSHA256";
    private static final Base64.Encoder URL_ENCODER = Base64.getUrlEncoder().withoutPadding();
    private static final Base64.Decoder URL_DECODER = Base64.getUrlDecoder();
    private static final SecureRandom SECURE_RANDOM = new SecureRandom();

    private final AuthProperties authProperties;
    private final String processLocalSecret = createProcessLocalSecret();

    public String createToken(AuthenticatedUser user) {
        long now = Instant.now().getEpochSecond();
        String header = "{\"alg\":\"HS256\",\"typ\":\"JWT\"}";
        String payload = "{"
                + "\"sub\":\"" + escapeJson(user.id()) + "\","
                + "\"email\":\"" + escapeJson(user.email()) + "\","
                + "\"name\":\"" + escapeJson(user.displayName()) + "\","
                + "\"iat\":" + now + ","
                + "\"exp\":" + (now + authProperties.getJwtExpirationSeconds())
                + "}";

        String unsigned = encode(header) + "." + encode(payload);
        return unsigned + "." + sign(unsigned);
    }

    public AuthenticatedUser validateToken(String token) {
        try {
            String[] parts = token.split("\\.");
            if (parts.length != 3) {
                throw new IllegalArgumentException("Invalid JWT format.");
            }
            String unsigned = parts[0] + "." + parts[1];
            if (!constantTimeEquals(sign(unsigned), parts[2])) {
                throw new IllegalArgumentException("Invalid JWT signature.");
            }
            String payload = new String(URL_DECODER.decode(parts[1]), StandardCharsets.UTF_8);
            long exp = extractLong(payload, "exp");
            if (Instant.now().getEpochSecond() >= exp) {
                throw new IllegalArgumentException("JWT expired.");
            }
            return new AuthenticatedUser(
                    extractString(payload, "sub"),
                    extractString(payload, "email"),
                    extractString(payload, "name"));
        } catch (Exception e) {
            throw new IllegalArgumentException("Invalid authentication token.", e);
        }
    }

    public long getExpirationSeconds() {
        return authProperties.getJwtExpirationSeconds();
    }

    private String encode(String value) {
        return URL_ENCODER.encodeToString(value.getBytes(StandardCharsets.UTF_8));
    }

    private String escapeJson(String value) {
        if (value == null) {
            return "";
        }
        return value.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    private String extractString(String json, String key) {
        String marker = "\"" + key + "\":\"";
        int start = json.indexOf(marker);
        if (start < 0) {
            return "";
        }
        start += marker.length();
        StringBuilder value = new StringBuilder();
        boolean escaping = false;
        for (int i = start; i < json.length(); i++) {
            char ch = json.charAt(i);
            if (escaping) {
                value.append(ch);
                escaping = false;
                continue;
            }
            if (ch == '\\') {
                escaping = true;
                continue;
            }
            if (ch == '"') {
                break;
            }
            value.append(ch);
        }
        return value.toString();
    }

    private long extractLong(String json, String key) {
        String marker = "\"" + key + "\":";
        int start = json.indexOf(marker);
        if (start < 0) {
            return 0;
        }
        start += marker.length();
        int end = start;
        while (end < json.length() && Character.isDigit(json.charAt(end))) {
            end++;
        }
        return Long.parseLong(json.substring(start, end));
    }

    private String sign(String unsigned) {
        try {
            Mac mac = Mac.getInstance(HMAC_ALGORITHM);
            mac.init(new SecretKeySpec(resolveSecret().getBytes(StandardCharsets.UTF_8), HMAC_ALGORITHM));
            return URL_ENCODER.encodeToString(mac.doFinal(unsigned.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) {
            throw new IllegalStateException("Could not sign JWT.", e);
        }
    }

    private String resolveSecret() {
        String configured = authProperties.getJwtSecret();
        if (configured != null && !configured.isBlank()) {
            return configured;
        }
        return processLocalSecret;
    }

    private static String createProcessLocalSecret() {
        byte[] bytes = new byte[48];
        SECURE_RANDOM.nextBytes(bytes);
        return Base64.getEncoder().encodeToString(bytes);
    }

    private boolean constantTimeEquals(String a, String b) {
        byte[] left = a.getBytes(StandardCharsets.UTF_8);
        byte[] right = b.getBytes(StandardCharsets.UTF_8);
        if (left.length != right.length) {
            return false;
        }
        int result = 0;
        for (int i = 0; i < left.length; i++) {
            result |= left[i] ^ right[i];
        }
        return result == 0;
    }
}
