package com.sysagent.sysagent_backend.repository;

import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import com.sysagent.sysagent_backend.model.entity.DeviceContextSnapshotEntity;

@Repository
public interface DeviceContextSnapshotRepository extends JpaRepository<DeviceContextSnapshotEntity, UUID> {
    Optional<DeviceContextSnapshotEntity> findFirstByDeviceIdAndOwnerIdOrderByCreatedAtDesc(Long deviceId, String ownerId);

    @Modifying
    @Query(value = """
            delete from device_context_snapshots
            where id in (
                select id
                from (
                    select id,
                           row_number() over (
                               partition by device_id, owner_id
                               order by created_at desc
                           ) as row_number
                    from device_context_snapshots
                    where device_id = :deviceId
                      and owner_id = :ownerId
                ) ranked
                where ranked.row_number > :keepCount
            )
            """, nativeQuery = true)
    int deleteOlderThanLimit(
            @Param("deviceId") Long deviceId,
            @Param("ownerId") String ownerId,
            @Param("keepCount") int keepCount);
}
