package com.sysagent.sysagent_backend.service;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import com.sysagent.sysagent_backend.model.dto.AgentProfileDto;

@SpringBootTest
class AgentHubServiceTest {

    @Autowired
    private AgentHubService agentHubService;

    @Test
    void listsSeededAgentProfiles() {
        List<AgentProfileDto> profiles = agentHubService.listAgentProfiles();

        assertThat(profiles)
                .extracting(AgentProfileDto::getSlug)
                .contains("terminal_router", "mcp_read_agent", "script_proposal_agent");
    }
}
