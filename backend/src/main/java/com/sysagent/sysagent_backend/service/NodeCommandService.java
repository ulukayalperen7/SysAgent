package com.sysagent.sysagent_backend.service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.sysagent.sysagent_backend.model.dto.NodeCommandDto;
import com.sysagent.sysagent_backend.model.dto.NodeCommandResultRequestDto;
import com.sysagent.sysagent_backend.model.dto.NodeCommandStatusDto;
import com.sysagent.sysagent_backend.model.dto.NodeHeartbeatRequestDto;
import com.sysagent.sysagent_backend.model.entity.DeviceEntity;
import com.sysagent.sysagent_backend.model.entity.NodeCommandEntity;
import com.sysagent.sysagent_backend.model.entity.TaskEntity;
import com.sysagent.sysagent_backend.model.enums.NodeCommandStatus;
import com.sysagent.sysagent_backend.model.enums.TaskStatus;
import com.sysagent.sysagent_backend.repository.DeviceRepository;
import com.sysagent.sysagent_backend.repository.NodeCommandRepository;
import com.sysagent.sysagent_backend.security.NodeDeviceAuthService;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class NodeCommandService {

    private final DeviceRepository deviceRepository;
    private final NodeCommandRepository nodeCommandRepository;
    private final NodeDeviceAuthService nodeDeviceAuthService;
    private final TaskService taskService;

    @Transactional
    public NodeCommandDto enqueue(TaskEntity task) {
        DeviceEntity device = requireDevice(task.getTargetDeviceId());
        if (!device.getOwnerId().equals(task.getOwnerId())) {
            throw new IllegalArgumentException("Target device does not belong to the task owner.");
        }
        if (device.getNodeTokenHash() == null || device.getNodeTokenHash().isBlank()) {
            throw new IllegalArgumentException("Target device is not registered with a node runtime token.");
        }
        NodeCommandEntity command = NodeCommandEntity.builder()
                .id(UUID.randomUUID())
                .taskId(task.getId())
                .deviceId(device.getId())
                .ownerId(task.getOwnerId())
                .script(task.getScript())
                .status(NodeCommandStatus.QUEUED)
                .createdAt(LocalDateTime.now())
                .build();
        taskService.updateTaskStatus(task.getId(), TaskStatus.IN_PROGRESS, null);
        return NodeCommandDto.fromEntity(nodeCommandRepository.save(command));
    }

    @Transactional
    public void recordHeartbeat(String nodeToken, NodeHeartbeatRequestDto request, String fallbackIpAddress) {
        DeviceEntity device = nodeDeviceAuthService.authenticateDevice(request.getDeviceId(), nodeToken);
        if (request.getHostname() != null && !request.getHostname().isBlank()) {
            device.setName(clean(request.getHostname(), 120));
        }
        if (request.getIpAddress() != null && !request.getIpAddress().isBlank()) {
            device.setIpAddress(clean(request.getIpAddress(), 120));
        } else if (fallbackIpAddress != null && !fallbackIpAddress.isBlank()) {
            device.setIpAddress(clean(fallbackIpAddress, 120));
        }
        if (request.getType() != null) {
            device.setType(request.getType());
        }
        device.setNodeVersion(clean(request.getNodeVersion(), 80));
        device.setCpuUsage(normalizedPercent(request.getCpuUsage()));
        device.setRamUsage(normalizedPercent(request.getRamUsage()));
        device.setStatus("online");
        device.setLastSeen(LocalDateTime.now());
        deviceRepository.save(device);
    }

    @Transactional
    public Optional<NodeCommandDto> claimNextCommand(String nodeToken, Long deviceId) {
        nodeDeviceAuthService.authenticateDevice(deviceId, nodeToken);
        Optional<NodeCommandEntity> next = nodeCommandRepository
                .findFirstByDeviceIdAndStatusOrderByCreatedAtAsc(deviceId, NodeCommandStatus.QUEUED);
        if (next.isEmpty()) {
            return Optional.empty();
        }
        NodeCommandEntity command = next.get();
        command.setStatus(NodeCommandStatus.CLAIMED);
        command.setClaimedAt(LocalDateTime.now());
        return Optional.of(NodeCommandDto.fromEntity(nodeCommandRepository.save(command)));
    }

    @Transactional(readOnly = true)
    public List<NodeCommandStatusDto> getStatusesForOwner(String ownerId) {
        return nodeCommandRepository.findByOwnerIdOrderByCreatedAtDesc(ownerId).stream()
                .map(NodeCommandStatusDto::fromEntity)
                .toList();
    }

    @Transactional(readOnly = true)
    public Optional<NodeCommandStatusDto> getLatestStatusForTask(String taskId, String ownerId) {
        return nodeCommandRepository.findFirstByTaskIdAndOwnerIdOrderByCreatedAtDesc(taskId, ownerId)
                .map(NodeCommandStatusDto::fromEntity);
    }

    @Transactional
    public void recordCommandResult(String nodeToken, String commandId, NodeCommandResultRequestDto request) {
        DeviceEntity device = nodeDeviceAuthService.authenticateDevice(request.getDeviceId(), nodeToken);
        UUID id = parseCommandId(commandId);
        NodeCommandEntity command = nodeCommandRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Command not found."));
        if (!device.getId().equals(command.getDeviceId())) {
            throw new IllegalArgumentException("Command does not belong to this device.");
        }
        if (command.getStatus() == NodeCommandStatus.COMPLETED || command.getStatus() == NodeCommandStatus.FAILED) {
            throw new IllegalArgumentException("Command result was already recorded.");
        }

        command.setStatus(request.isSuccess() ? NodeCommandStatus.COMPLETED : NodeCommandStatus.FAILED);
        command.setOutput(cleanLarge(request.getOutput()));
        command.setError(cleanLarge(request.getError()));
        command.setCompletedAt(LocalDateTime.now());
        nodeCommandRepository.save(command);

        taskService.updateTaskStatus(
                command.getTaskId(),
                request.isSuccess() ? TaskStatus.COMPLETED : TaskStatus.FAILED,
                null);
    }

    private DeviceEntity requireDevice(Long deviceId) {
        if (deviceId == null) {
            throw new IllegalArgumentException("Device id is required.");
        }
        return deviceRepository.findById(deviceId)
                .orElseThrow(() -> new IllegalArgumentException("Device not found."));
    }

    private UUID parseCommandId(String commandId) {
        try {
            return UUID.fromString(commandId);
        } catch (Exception e) {
            throw new IllegalArgumentException("Invalid command id.");
        }
    }

    private String clean(String value, int maxLength) {
        if (value == null) {
            return null;
        }
        String cleaned = value.trim();
        return cleaned.length() > maxLength ? cleaned.substring(0, maxLength) : cleaned;
    }

    private String cleanLarge(String value) {
        if (value == null) {
            return null;
        }
        String cleaned = value.trim();
        int maxLength = 120_000;
        return cleaned.length() > maxLength ? cleaned.substring(0, maxLength) : cleaned;
    }

    private Integer normalizedPercent(Integer value) {
        if (value == null || value < 0 || value > 100) {
            return null;
        }
        return value;
    }
}
