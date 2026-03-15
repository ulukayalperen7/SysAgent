package com.sysagent.sysagent_backend.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.sysagent.sysagent_backend.model.entity.TaskEntity;

@Repository
public interface TaskRepository extends JpaRepository<TaskEntity, String> {
}
