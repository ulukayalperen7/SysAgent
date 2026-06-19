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
@Table(name = "device_registration_tokens")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DeviceRegistrationTokenEntity {

    @Id
    private UUID id;

    @Column(nullable = false)
    private String ownerId;

    @Column(nullable = false, unique = true)
    private String tokenHash;

    private String label;

    @Column(nullable = false)
    private LocalDateTime expiresAt;

    private LocalDateTime usedAt;

    @Column(nullable = false)
    private LocalDateTime createdAt;
}
