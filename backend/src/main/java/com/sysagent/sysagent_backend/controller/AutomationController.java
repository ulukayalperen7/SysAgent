package com.sysagent.sysagent_backend.controller;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.sysagent.sysagent_backend.model.dto.AutomationRuleDto;
import com.sysagent.sysagent_backend.model.response.ApiResponse;
import com.sysagent.sysagent_backend.security.CurrentUserProvider;
import com.sysagent.sysagent_backend.service.AutomationService;

import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/api/automations")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class AutomationController {

    private final AutomationService automationService;
    private final CurrentUserProvider currentUserProvider;

    @GetMapping
    public ResponseEntity<ApiResponse<List<AutomationRuleDto>>> getAutomationRules() {
        List<AutomationRuleDto> rules = automationService.listRulesByOwner(currentUserProvider.getCurrentUserId());
        return ResponseEntity.ok(ApiResponse.success(rules, "Automation rules loaded"));
    }
}
