package com.sysagent.sysagent_backend.repository;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.sysagent.sysagent_backend.model.entity.AppUserEntity;

@Repository
public interface AppUserRepository extends JpaRepository<AppUserEntity, String> {

    Optional<AppUserEntity> findByEmail(String email);

    boolean existsByEmail(String email);
}
