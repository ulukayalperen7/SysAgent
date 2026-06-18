package com.sysagent.sysagent_backend.service;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import com.sysagent.sysagent_backend.model.dto.AutomationRuleDto;

@SpringBootTest
class AutomationServiceTest {

    @Autowired
    private AutomationService automationService;

    @Test
    void listsAutomationRulesForOwner() {
        List<AutomationRuleDto> rules = automationService.listRulesByOwner("test-user-1");

        assertThat(rules).isNotNull();
    }
}
