package com.sysagent.sysagent_backend.model.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PostCommandVerificationDto {
    private String taskId;
    private String status;
    private String reason;
    private String screenSummary;
}
