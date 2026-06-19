package com.sysagent.sysagent_backend.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.sysagent.sysagent_backend.model.dto.DeviceNodeRegistrationRequestDto;
import com.sysagent.sysagent_backend.model.dto.NodeCommandDto;
import com.sysagent.sysagent_backend.model.dto.NodeCommandResultRequestDto;
import com.sysagent.sysagent_backend.model.dto.NodeHeartbeatRequestDto;
import com.sysagent.sysagent_backend.model.dto.NodeRegistrationResponseDto;
import com.sysagent.sysagent_backend.model.response.ApiResponse;
import com.sysagent.sysagent_backend.service.DeviceService;
import com.sysagent.sysagent_backend.service.NodeCommandService;

import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/api/node")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class NodeRegistrationController {

    private final DeviceService deviceService;
    private final NodeCommandService nodeCommandService;

    @PostMapping("/register")
    public ResponseEntity<ApiResponse<NodeRegistrationResponseDto>> registerNode(
            @RequestBody DeviceNodeRegistrationRequestDto request,
            HttpServletRequest servletRequest) {
        try {
            NodeRegistrationResponseDto response = deviceService.registerNode(request, servletRequest.getRemoteAddr());
            return ResponseEntity.ok(ApiResponse.success(response, "Device registered successfully"));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(ApiResponse.error(e.getMessage()));
        }
    }

    @PostMapping("/heartbeat")
    public ResponseEntity<ApiResponse<Void>> heartbeat(
            @RequestHeader("X-SysAgent-Node-Token") String nodeToken,
            @RequestBody NodeHeartbeatRequestDto request,
            HttpServletRequest servletRequest) {
        try {
            nodeCommandService.recordHeartbeat(nodeToken, request, servletRequest.getRemoteAddr());
            return ResponseEntity.ok(ApiResponse.success("Heartbeat accepted"));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(ApiResponse.error(e.getMessage()));
        }
    }

    @GetMapping("/commands/next")
    public ResponseEntity<ApiResponse<NodeCommandDto>> nextCommand(
            @RequestHeader("X-SysAgent-Node-Token") String nodeToken,
            @RequestParam Long deviceId) {
        try {
            return ResponseEntity.ok(ApiResponse.success(
                    nodeCommandService.claimNextCommand(nodeToken, deviceId).orElse(null),
                    "Command poll completed"));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(ApiResponse.error(e.getMessage()));
        }
    }

    @PostMapping("/commands/{commandId}/result")
    public ResponseEntity<ApiResponse<Void>> commandResult(
            @RequestHeader("X-SysAgent-Node-Token") String nodeToken,
            @PathVariable String commandId,
            @RequestBody NodeCommandResultRequestDto request) {
        try {
            nodeCommandService.recordCommandResult(nodeToken, commandId, request);
            return ResponseEntity.ok(ApiResponse.success("Command result accepted"));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(ApiResponse.error(e.getMessage()));
        }
    }
}
