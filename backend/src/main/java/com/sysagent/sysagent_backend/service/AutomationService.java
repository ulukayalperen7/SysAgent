package com.sysagent.sysagent_backend.service;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import com.sysagent.sysagent_backend.model.dto.AutomationRuleDto;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class AutomationService {

    private final JdbcTemplate jdbcTemplate;

    public List<AutomationRuleDto> listRulesByOwner(String ownerId) {
        String sql = """
                select
                    ar.id::text,
                    ar.owner_id,
                    ar.name,
                    ar.description,
                    ar.trigger_type,
                    ar.trigger_summary,
                    ar.action_type,
                    ar.action_summary,
                    ap.slug as target_agent_slug,
                    ar.target_device_scope,
                    ar.status,
                    ar.requires_approval,
                    ar.risk_level,
                    ar.schedule_expression,
                    ar.last_run_at::text,
                    ar.next_run_at::text,
                    ar.created_at::text,
                    ar.updated_at::text
                from automation_rules ar
                left join agent_profiles ap on ap.id = ar.target_agent_id
                where ar.owner_id = ?
                  and ar.status <> 'disabled'
                order by ar.created_at desc
                """;
        return jdbcTemplate.query(sql, this::mapRule, ownerId);
    }

    private AutomationRuleDto mapRule(ResultSet rs, int rowNum) throws SQLException {
        return AutomationRuleDto.builder()
                .id(rs.getString("id"))
                .ownerId(rs.getString("owner_id"))
                .name(rs.getString("name"))
                .description(rs.getString("description"))
                .triggerType(rs.getString("trigger_type"))
                .triggerSummary(rs.getString("trigger_summary"))
                .actionType(rs.getString("action_type"))
                .actionSummary(rs.getString("action_summary"))
                .targetAgentSlug(rs.getString("target_agent_slug"))
                .targetDeviceScope(rs.getString("target_device_scope"))
                .status(rs.getString("status"))
                .requiresApproval(rs.getBoolean("requires_approval"))
                .riskLevel(rs.getString("risk_level"))
                .scheduleExpression(rs.getString("schedule_expression"))
                .lastRunAt(rs.getString("last_run_at"))
                .nextRunAt(rs.getString("next_run_at"))
                .createdAt(rs.getString("created_at"))
                .updatedAt(rs.getString("updated_at"))
                .build();
    }
}
