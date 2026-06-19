package com.sysagent.sysagent_backend.repository;

import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.sysagent.sysagent_backend.model.entity.DeviceRegistrationTokenEntity;

@Repository
public interface DeviceRegistrationTokenRepository extends JpaRepository<DeviceRegistrationTokenEntity, UUID> {

    Optional<DeviceRegistrationTokenEntity> findByTokenHash(String tokenHash);
}
