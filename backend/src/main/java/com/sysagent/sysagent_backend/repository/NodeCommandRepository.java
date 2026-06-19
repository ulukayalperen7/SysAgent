package com.sysagent.sysagent_backend.repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.sysagent.sysagent_backend.model.entity.NodeCommandEntity;
import com.sysagent.sysagent_backend.model.enums.NodeCommandStatus;

@Repository
public interface NodeCommandRepository extends JpaRepository<NodeCommandEntity, UUID> {

    Optional<NodeCommandEntity> findFirstByDeviceIdAndStatusOrderByCreatedAtAsc(Long deviceId, NodeCommandStatus status);

    List<NodeCommandEntity> findByOwnerIdOrderByCreatedAtDesc(String ownerId);

    Optional<NodeCommandEntity> findFirstByTaskIdAndOwnerIdOrderByCreatedAtDesc(String taskId, String ownerId);
}
