package com.sysagent.sysagent_backend.model.dto;

import lombok.Data;

@Data
public class NodeCommandResultRequestDto {
    private Long deviceId;
    private boolean success;
    private String output;
    private String error;
}
