package com.sysagent.sysagent_backend.model.dto;

import java.util.Map;

import lombok.Data;

@Data
public class NodeDesktopContextRequestDto {
    private Long deviceId;
    private String capturedAt;
    private String activeWindowTitle;
    private String activeProcessName;
    private Integer screenWidth;
    private Integer screenHeight;
    private String screenshotMimeType;
    private String screenshotBase64;
    private Map<String, Object> metadata;
}
