package com.sysagent.sysagent_backend.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.sysagent.sysagent_backend.model.entity.TaskEntity;

@Repository
public interface TaskRepository extends JpaRepository<TaskEntity, String> {
    
    /**
     * Find all tasks that were created by a specific user.
     * Prevents cross-user task leakage.
     * 
     * @param ownerId The unique ID of the device/task owner.
     * @return List of tasks for this owner.
     */
    List<TaskEntity> findByOwnerId(String ownerId);
}
