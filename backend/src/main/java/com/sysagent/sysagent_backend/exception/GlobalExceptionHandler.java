package com.sysagent.sysagent_backend.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import com.sysagent.sysagent_backend.model.response.ApiResponse;

import lombok.extern.slf4j.Slf4j;

/**
 * Handles all uncaught exceptions in the application and returns a structured ApiResponse.
 * Prevents stack traces from leaking to the frontend and ensures consistent error messages.
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    /**
     * Handles generic RuntimeExceptions (e.g., NullPointerException, IllegalArgumentException).
     * @param ex The exception that was thrown.
     * @return A default 500 error response.
     */
    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<ApiResponse<Object>> handleRuntimeException(RuntimeException ex) {
        log.error("Unhandled exception occurred: ", ex);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.error(ex.getMessage()));
    }

    // You can add more specific handlers here, e.g., DeviceNotFoundException
    /*
    @ExceptionHandler(DeviceNotFoundException.class)
    public ResponseEntity<ApiResponse<Object>> handleDeviceNotFound(DeviceNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(ApiResponse.error("Device not found"));
    }
    */
}
