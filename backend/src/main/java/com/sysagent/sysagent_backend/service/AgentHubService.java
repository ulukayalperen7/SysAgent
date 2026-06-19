package com.sysagent.sysagent_backend.service;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;
import java.util.Optional;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import com.sysagent.sysagent_backend.model.dto.AgentProfileDto;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class AgentHubService {

    private final JdbcTemplate jdbcTemplate;

    public List<AgentProfileDto> listAgentProfiles() {
        String sql = """
                select
                    ap.id::text,
                    ap.slug,
                    ap.name,
                    ap.description,
                    ap.agent_type,
                    ap.status,
                    ap.owner_id,
                    ap.default_model_provider,
                    ap.default_model_name,
                    ap.risk_ceiling,
                    ap.requires_approval,
                    ap.created_at::text,
                    ap.updated_at::text,
                    count(distinct app.id) filter (where app.is_active = true) as active_prompt_versions,
                    count(distinct amtp.id) filter (where amtp.permission_mode = 'allow') as allowed_mcp_tools
                from agent_profiles ap
                left join agent_prompt_versions app on app.agent_id = ap.id
                left join agent_mcp_tool_permissions amtp on amtp.agent_id = ap.id
                where ap.status <> 'archived'
                group by ap.id
                order by
                    case ap.agent_type
                        when 'router' then 1
                        when 'langgraph_node' then 2
                        when 'tool_agent' then 3
                        when 'crewai_agent' then 4
                        when 'script_proposer' then 5
                        else 6
                    end,
                    ap.slug
                """;

        return jdbcTemplate.query(sql, this::mapAgentProfile);
    }

    public String findCommandBlockReason(String command, String osName) {
        String sql = """
                select rule_type, pattern, reason
                from agent_risk_policy_rules r
                join agent_risk_policies p on p.id = r.policy_id
                where p.enabled = true
                  and r.enabled = true
                  and r.effect = 'block'
                order by r.priority asc
                """;

        String lowerCommand = command == null ? "" : command.toLowerCase();
        boolean isWindows = osName != null && osName.toLowerCase().contains("win");
        try {
            Optional<String> reason = jdbcTemplate.query(sql, (rs, rowNum) -> new RiskRuleRow(
                            rs.getString("rule_type"),
                            rs.getString("pattern"),
                            rs.getString("reason")))
                    .stream()
                    .filter(rule -> rule.blocks(lowerCommand, isWindows))
                    .map(RiskRuleRow::reason)
                    .findFirst();
            return reason.orElse(null);
        } catch (Exception e) {
            return null;
        }
    }

    private AgentProfileDto mapAgentProfile(ResultSet rs, int rowNum) throws SQLException {
        return AgentProfileDto.builder()
                .id(rs.getString("id"))
                .slug(rs.getString("slug"))
                .name(rs.getString("name"))
                .description(rs.getString("description"))
                .agentType(rs.getString("agent_type"))
                .status(rs.getString("status"))
                .ownerId(rs.getString("owner_id"))
                .defaultModelProvider(rs.getString("default_model_provider"))
                .defaultModelName(rs.getString("default_model_name"))
                .riskCeiling(rs.getString("risk_ceiling"))
                .requiresApproval(rs.getBoolean("requires_approval"))
                .activePromptVersions(rs.getInt("active_prompt_versions"))
                .allowedMcpTools(rs.getInt("allowed_mcp_tools"))
                .createdAt(rs.getString("created_at"))
                .updatedAt(rs.getString("updated_at"))
                .build();
    }

    private record RiskRuleRow(String ruleType, String pattern, String reason) {

        boolean blocks(String lowerCommand, boolean isWindows) {
            String lowerPattern = pattern == null ? "" : pattern.toLowerCase();
            if (lowerPattern.isBlank()) {
                return false;
            }
            if ("command_contains".equals(ruleType)) {
                return lowerCommand.contains(lowerPattern);
            }
            if ("path_prefix".equals(ruleType)) {
                if (isWindows) {
                    return lowerCommand.contains(lowerPattern);
                }
                return lowerCommand.startsWith(lowerPattern) || lowerCommand.contains(" " + lowerPattern);
            }
            if ("regex".equals(ruleType)) {
                return lowerCommand.matches("(?s).*" + lowerPattern + ".*");
            }
            return false;
        }
    }
}
