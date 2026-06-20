package com.sysagent.sysagent_backend.repository;

import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.sysagent.sysagent_backend.model.entity.DeviceContextSnapshotEntity;

@Repository
public interface DeviceContextSnapshotRepository extends JpaRepository<DeviceContextSnapshotEntity, UUID> {
    Optional<DeviceContextSnapshotEntity> findFirstByDeviceIdAndOwnerIdOrderByCreatedAtDesc(Long deviceId, String ownerId);
}
