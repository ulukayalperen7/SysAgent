package com.sysagent.sysagent_backend.model.entity;

import java.time.LocalDateTime;
import java.util.UUID;

import com.sysagent.sysagent_backend.model.enums.NodeCommandStatus;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "node_commands")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NodeCommandEntity {

    @Id
    private UUID id;

    @Column(nullable = false)
    private String taskId;

    @Column(nullable = false)
    private Long deviceId;

    @Column(nullable = false)
    private String ownerId;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String script;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private NodeCommandStatus status;

    @Column(columnDefinition = "TEXT")
    private String output;

    @Column(columnDefinition = "TEXT")
    private String error;

    @Column(nullable = false)
    private LocalDateTime createdAt;

    private LocalDateTime claimedAt;
    private LocalDateTime completedAt;
}
