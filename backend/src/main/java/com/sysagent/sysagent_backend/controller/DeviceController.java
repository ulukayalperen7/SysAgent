package com.sysagent.sysagent_backend.controller;

import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.sysagent.sysagent_backend.model.dto.DeviceDto;
import com.sysagent.sysagent_backend.model.dto.DeviceContextSnapshotDto;
import com.sysagent.sysagent_backend.model.dto.DeviceRegistrationTokenRequestDto;
import com.sysagent.sysagent_backend.model.dto.DeviceRegistrationTokenResponseDto;
import com.sysagent.sysagent_backend.model.dto.NodeCommandStatusDto;
import com.sysagent.sysagent_backend.model.dto.TaskHistoryDto;
import com.sysagent.sysagent_backend.model.response.ApiResponse;
import com.sysagent.sysagent_backend.security.CurrentUserProvider;
import com.sysagent.sysagent_backend.service.DeviceService;
import com.sysagent.sysagent_backend.service.DeviceContextService;
import com.sysagent.sysagent_backend.service.NodeCommandService;
import com.sysagent.sysagent_backend.service.TaskService;

import lombok.RequiredArgsConstructor;

/**
 * Controller for managing connected devices.
 * Provides endpoints to list devices and get their status.
 */
@RestController
@RequestMapping("/api/devices")
@RequiredArgsConstructor
public class DeviceController {

    private final DeviceService deviceService;
    private final CurrentUserProvider currentUserProvider;
    private final TaskService taskService;
    private final NodeCommandService nodeCommandService;
    private final DeviceContextService deviceContextService;

    @GetMapping
    public ResponseEntity<ApiResponse<List<DeviceDto>>> getConnectedDevices() {
        List<DeviceDto> devices = deviceService.getDevicesByOwner(currentUserProvider.getCurrentUserId());

        return ResponseEntity.ok(ApiResponse.<List<DeviceDto>>builder()
                .status("SUCCESS")
                .message("Devices fetched successfully")
                .data(devices)
                .build());
    }

    @GetMapping("/{id}/tasks")
    public ResponseEntity<ApiResponse<List<TaskHistoryDto>>> getDeviceTasks(@PathVariable("id") Long deviceId) {
        String ownerId = currentUserProvider.getCurrentUserId();
        deviceService.getOwnedDevice(deviceId, ownerId);
        List<TaskHistoryDto> tasks = taskService.getTaskHistoryByOwnerAndDevice(ownerId, deviceId);
        attachRemoteCommandStatuses(tasks, ownerId);

        return ResponseEntity.ok(ApiResponse.<List<TaskHistoryDto>>builder()
                .status("SUCCESS")
                .message("Device task history fetched successfully")
                .data(tasks)
                .build());
    }

    @GetMapping("/{id}/context/latest")
    public ResponseEntity<ApiResponse<DeviceContextSnapshotDto>> getLatestDeviceContext(@PathVariable("id") Long deviceId) {
        String ownerId = currentUserProvider.getCurrentUserId();
        deviceService.getOwnedDevice(deviceId, ownerId);
        DeviceContextSnapshotDto latest = deviceContextService.getLatestForOwner(deviceId, ownerId).orElse(null);
        return ResponseEntity.ok(ApiResponse.success(latest, "Latest device context fetched successfully"));
    }

    @PostMapping("/registration-token")
    public ResponseEntity<ApiResponse<DeviceRegistrationTokenResponseDto>> createRegistrationToken(
            @RequestBody(required = false) DeviceRegistrationTokenRequestDto request) {
        String label = request == null ? null : request.getLabel();
        DeviceRegistrationTokenResponseDto token = deviceService.createRegistrationToken(
                currentUserProvider.getCurrentUserId(),
                label);
        return ResponseEntity.ok(ApiResponse.success(token, "Device registration token created"));
    }

    private void attachRemoteCommandStatuses(List<TaskHistoryDto> tasks, String ownerId) {
        Map<String, NodeCommandStatusDto> latestByTask = nodeCommandService.getStatusesForOwner(ownerId).stream()
                .collect(Collectors.toMap(
                        NodeCommandStatusDto::getTaskId,
                        Function.identity(),
                        (first, ignored) -> first));
        tasks.forEach(task -> task.attachRemoteCommand(latestByTask.get(task.getId())));
    }
}
