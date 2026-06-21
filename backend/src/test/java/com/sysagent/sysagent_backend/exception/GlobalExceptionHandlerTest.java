package com.sysagent.sysagent_backend.exception;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MissingRequestHeaderException;

import com.sysagent.sysagent_backend.model.response.ApiResponse;

class GlobalExceptionHandlerTest {

    private final GlobalExceptionHandler handler = new GlobalExceptionHandler();

    @Test
    void mapsUserInputErrorsToBadRequest() {
        ResponseEntity<ApiResponse<Object>> response =
                handler.handleIllegalArgumentException(new IllegalArgumentException("Invalid request."));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody().getMessage()).isEqualTo("Invalid request.");
    }

    @Test
    void mapsMissingNodeTokenToUnauthorized() {
        ResponseEntity<ApiResponse<Object>> response = handler.handleMissingRequestHeader(
                new MissingRequestHeaderException("X-SysAgent-Node-Token", null));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.UNAUTHORIZED);
        assertThat(response.getBody().getMessage()).contains("node authentication token");
    }
}
