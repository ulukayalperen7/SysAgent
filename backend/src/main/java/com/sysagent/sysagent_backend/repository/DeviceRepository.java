package com.sysagent.sysagent_backend.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.sysagent.sysagent_backend.model.entity.DeviceEntity;

/**
 * Repository for managing DeviceEntity data access.
 * Extends JpaRepository to provide standard CRUD operations.
 */
@Repository
public interface DeviceRepository extends JpaRepository<DeviceEntity, Long> {
    
    // Find all devices with a specific status (e.g., "online")
    List<DeviceEntity> findByStatus(String status);
    
    // Find a device by its name (hostname)
    DeviceEntity findByName(String name);

    /**
     * Finds all devices belonging to a specific user.
     * This is the core query for multi-tenant data isolation.
     * 
     * @param ownerId The unique identifier of the user (e.g., user email or UUID).
     * @return A list of DeviceEntity objects owned by the user.
     */
    List<DeviceEntity> findByOwnerId(String ownerId);
}
