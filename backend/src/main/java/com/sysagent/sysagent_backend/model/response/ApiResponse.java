package com.sysagent.sysagent_backend.model.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * A standard response wrapper for all API endpoints.
 * Ensures that the frontend always receives data in a predictable format:
 * {
 *   "status": "SUCCESS",
 *   "message": "Operation completed",
 *   "data": { ... payload ... },
 *   "timestamp": "2024-03-15T10:00:00"
 * }
 * @param <T> The type of the data payload (e.g., DeviceDto, List<TaskEntity>)
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ApiResponse<T> {

    /**
     * The status of the operation (e.g., "SUCCESS", "ERROR").
     * Can be an enum in the future, kept as String for flexibility now.
     */
    private String status;

    /**
     * A human-readable message describing the result (e.g., "Device created successfully").
     */
    private String message;

    /**
     * The actual payload of the response. Can be null if there is no data to return.
     */
    private T data;

    /**
     * The time when the response was generated. Useful for debugging and logging.
     */
    @Builder.Default
    private LocalDateTime timestamp = LocalDateTime.now();

    /**
     * Helper method to create a successful response with data.
     */
    public static <T> ApiResponse<T> success(T data, String message) {
        return ApiResponse.<T>builder()
                .status("SUCCESS")
                .message(message)
                .data(data)
                .timestamp(LocalDateTime.now())
                .build();
    }

    /**
     * Helper method to create a successful response without data (e.g., for delete operations).
     */
    public static <T> ApiResponse<T> success(String message) {
        return success(null, message);
    }

    /**
     * Helper method to create an error response.
     */
    public static <T> ApiResponse<T> error(String message) {
        return ApiResponse.<T>builder()
                .status("ERROR")
                .message(message)
                .data(null)
                .timestamp(LocalDateTime.now())
                .build();
    }
}
