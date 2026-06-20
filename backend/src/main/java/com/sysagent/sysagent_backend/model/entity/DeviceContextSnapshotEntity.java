package com.sysagent.sysagent_backend.model.entity;

import java.time.LocalDateTime;
import java.util.UUID;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "device_context_snapshots")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DeviceContextSnapshotEntity {

    @Id
    private UUID id;

    @Column(nullable = false)
    private Long deviceId;

    @Column(nullable = false)
    private String ownerId;

    private String activeWindowTitle;

    private String activeProcessName;

    private Integer screenWidth;

    private Integer screenHeight;

    private String screenshotMimeType;

    @Column(columnDefinition = "text")
    private String screenshotBase64;

    @Column(columnDefinition = "text")
    private String metadataJson;

    private LocalDateTime capturedAt;

    private LocalDateTime createdAt;
}
