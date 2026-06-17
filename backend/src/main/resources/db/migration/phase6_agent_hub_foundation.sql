create extension if not exists pgcrypto;

create table if not exists agent_profiles (
    id uuid primary key default gen_random_uuid(),
    slug text not null unique,
    name text not null,
    description text,
    agent_type text not null check (agent_type in (
        'router',
        'langgraph_node',
        'crewai_agent',
        'tool_agent',
        'script_proposer',
        'chat_agent'
    )),
    status text not null default 'draft' check (status in ('draft', 'active', 'disabled', 'archived')),
    owner_id text,
    default_model_provider text,
    default_model_name text,
    risk_ceiling text not null default 'medium' check (risk_ceiling in ('low', 'medium', 'high')),
    requires_approval boolean not null default true,
    config jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists agent_prompt_versions (
    id uuid primary key default gen_random_uuid(),
    agent_id uuid not null references agent_profiles(id) on delete cascade,
    version integer not null,
    system_prompt text not null,
    developer_prompt text,
    response_contract jsonb not null default '{}'::jsonb,
    variables_schema jsonb not null default '{}'::jsonb,
    is_active boolean not null default false,
    created_by text,
    created_at timestamptz not null default now(),
    unique (agent_id, version)
);

create table if not exists mcp_tools (
    id uuid primary key default gen_random_uuid(),
    name text not null unique,
    server_name text not null default 'local_system',
    category text not null,
    description text,
    is_read_only boolean not null default true,
    default_risk_level text not null default 'low' check (default_risk_level in ('low', 'medium', 'high')),
    input_schema jsonb not null default '{}'::jsonb,
    output_schema jsonb not null default '{}'::jsonb,
    enabled boolean not null default true,
    created_at timestamptz not null default now()
);

create table if not exists agent_mcp_tool_permissions (
    id uuid primary key default gen_random_uuid(),
    agent_id uuid not null references agent_profiles(id) on delete cascade,
    mcp_tool_id uuid not null references mcp_tools(id) on delete cascade,
    permission_mode text not null default 'allow' check (permission_mode in ('allow', 'deny')),
    max_risk_level text not null default 'low' check (max_risk_level in ('low', 'medium', 'high')),
    requires_approval boolean not null default false,
    argument_constraints jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique (agent_id, mcp_tool_id)
);

create table if not exists agent_intent_routes (
    id uuid primary key default gen_random_uuid(),
    intent_key text not null,
    priority integer not null default 100,
    matcher jsonb not null default '{}'::jsonb,
    target_agent_id uuid references agent_profiles(id) on delete set null,
    target_langgraph_node text,
    route_type text not null check (route_type in (
        'chat',
        'mcp_read_only',
        'crewai_diagnostics',
        'script_proposal',
        'final_synthesis'
    )),
    approval_policy text not null default 'inherit' check (approval_policy in (
        'none',
        'always',
        'risk_based',
        'inherit'
    )),
    enabled boolean not null default true,
    created_at timestamptz not null default now()
);

create table if not exists agent_device_scopes (
    id uuid primary key default gen_random_uuid(),
    agent_id uuid not null references agent_profiles(id) on delete cascade,
    owner_id text,
    device_id bigint references devices(id) on delete cascade,
    os_type text check (os_type in ('WINDOWS', 'LINUX', 'MACOS')),
    scope_type text not null default 'allow' check (scope_type in ('allow', 'deny')),
    created_at timestamptz not null default now()
);

create table if not exists agent_risk_policies (
    id uuid primary key default gen_random_uuid(),
    name text not null unique,
    description text,
    default_approval_required boolean not null default true,
    max_autonomous_risk text not null default 'low' check (max_autonomous_risk in ('low', 'medium', 'high')),
    enabled boolean not null default true,
    created_at timestamptz not null default now()
);

create table if not exists agent_risk_policy_rules (
    id uuid primary key default gen_random_uuid(),
    policy_id uuid not null references agent_risk_policies(id) on delete cascade,
    rule_type text not null check (rule_type in (
        'command_contains',
        'path_prefix',
        'intent_key',
        'mcp_tool',
        'regex'
    )),
    pattern text not null,
    effect text not null check (effect in ('allow', 'require_approval', 'block')),
    risk_level text not null check (risk_level in ('low', 'medium', 'high')),
    reason text not null,
    priority integer not null default 100,
    enabled boolean not null default true
);

create table if not exists agent_decision_audit (
    id uuid primary key default gen_random_uuid(),
    task_id text references tasks(id) on delete set null,
    thread_id text,
    owner_id text,
    agent_id uuid references agent_profiles(id) on delete set null,
    prompt_version_id uuid references agent_prompt_versions(id) on delete set null,
    selected_route_id uuid references agent_intent_routes(id) on delete set null,
    intent_key text,
    mcp_tools_used jsonb not null default '[]'::jsonb,
    risk_level text,
    approval_required boolean,
    decision_summary text,
    raw_metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_agent_profiles_owner_status on agent_profiles(owner_id, status);
create index if not exists idx_agent_intent_routes_key_enabled on agent_intent_routes(intent_key, enabled, priority);
create index if not exists idx_agent_decision_audit_task on agent_decision_audit(task_id);
create index if not exists idx_agent_decision_audit_thread on agent_decision_audit(thread_id);
create unique index if not exists idx_agent_intent_routes_seed_unique on agent_intent_routes(intent_key, target_langgraph_node, route_type);
create unique index if not exists idx_agent_risk_policy_rules_seed_unique on agent_risk_policy_rules(policy_id, rule_type, pattern, effect);

insert into agent_profiles
    (slug, name, description, agent_type, status, risk_ceiling, requires_approval, config)
values
    ('terminal_router', 'Terminal Router', 'Routes terminal intents to the correct LangGraph path.', 'router', 'active', 'low', false, '{"langgraph_node":"detect_intent_node"}'::jsonb),
    ('direct_chat_agent', 'Direct Chat Agent', 'Handles greetings and conversation without tool access.', 'chat_agent', 'active', 'low', false, '{"langgraph_node":"direct_chat_node"}'::jsonb),
    ('mcp_read_agent', 'MCP Read Agent', 'Uses approved read-only MCP tools for local inspection.', 'tool_agent', 'active', 'low', false, '{"langgraph_node":"mcp_read_only_node"}'::jsonb),
    ('crewai_diagnostics_agent', 'CrewAI Diagnostics Agent', 'Runs deeper diagnostic reasoning with read-only MCP context.', 'crewai_agent', 'active', 'medium', false, '{"langgraph_node":"run_crewai_diagnostics_node"}'::jsonb),
    ('script_proposal_agent', 'Script Proposal Agent', 'Prepares approval-gated OS scripts for risky operations.', 'script_proposer', 'active', 'high', true, '{"langgraph_node":"generate_action_script_node"}'::jsonb)
on conflict (slug) do update set
    name = excluded.name,
    description = excluded.description,
    agent_type = excluded.agent_type,
    status = excluded.status,
    risk_ceiling = excluded.risk_ceiling,
    requires_approval = excluded.requires_approval,
    config = excluded.config,
    updated_at = now();

insert into agent_prompt_versions
    (agent_id, version, system_prompt, developer_prompt, response_contract, variables_schema, is_active, created_by)
select id, 1, 'You are a SysAgent runtime component. Follow the configured route, tool, and approval policy exactly.', null, '{}'::jsonb, '{}'::jsonb, true, 'phase6_seed'
from agent_profiles
where slug in ('terminal_router', 'direct_chat_agent', 'mcp_read_agent', 'crewai_diagnostics_agent', 'script_proposal_agent')
on conflict (agent_id, version) do nothing;

update agent_prompt_versions
set
    system_prompt = $$You are an intent classifier for an Enterprise AI Agent.
Classify the incoming user input into EXACTLY ONE of these categories:
- FILE_SYSTEM_READ (Listing files, viewing text files, searching for files)
- FILE_SYSTEM_WRITE (Creating, deleting, modifying, moving files or folders)
- APP_CONTROL (Opening, closing, managing desktop applications)
- DEVOPS_READ (Checking git status, docker ps, reading code)
- DEVOPS_WRITE (git push, npm install, docker restart)
- SYSTEM_OPERATION (Queries about OS stats, RAM, CPU, killing OS processes)
- NETWORK_READ (Ping, port scanning)
- CHAT (Greetings, casual talk)
- UNKNOWN (If it doesn't clearly fit)

User Input: {current_input}

Output ONLY THE EXACT CATEGORY STRING.$$,
    variables_schema = '{"current_input":"string"}'::jsonb
where agent_id = (select id from agent_profiles where slug = 'terminal_router')
  and version = 1
  and created_by = 'phase6_seed';

insert into mcp_tools
    (name, server_name, category, description, is_read_only, default_risk_level, input_schema)
values
    ('system_get_metrics_snapshot', 'local_system', 'system', 'Read CPU, memory, disk, and machine metrics.', true, 'low', '{}'::jsonb),
    ('system_list_processes', 'local_system', 'system', 'List local processes with bounded output.', true, 'low', '{"query":"string|null","limit":"integer"}'::jsonb),
    ('system_get_top_memory_processes', 'local_system', 'system', 'List top memory-consuming processes.', true, 'low', '{"limit":"integer"}'::jsonb),
    ('network_list_connections', 'local_system', 'network', 'List active network connections without mutating network state.', true, 'low', '{"limit":"integer"}'::jsonb),
    ('filesystem_list_directory', 'local_system', 'filesystem', 'List a safe local directory.', true, 'low', '{"path":"string|null"}'::jsonb),
    ('filesystem_read_file', 'local_system', 'filesystem', 'Read a bounded safe local text file.', true, 'low', '{"path":"string"}'::jsonb),
    ('filesystem_search', 'local_system', 'filesystem', 'Search a safe local directory tree with bounded output.', true, 'low', '{"path":"string|null","pattern":"string","limit":"integer","max_depth":"integer"}'::jsonb),
    ('filesystem_get_disk_usage', 'local_system', 'filesystem', 'Estimate bounded disk usage for a safe local path.', true, 'low', '{"path":"string|null","max_entries":"integer"}'::jsonb),
    ('system_get_platform_info', 'local_system', 'system', 'Read OS and platform metadata.', true, 'low', '{}'::jsonb)
on conflict (name) do update set
    server_name = excluded.server_name,
    category = excluded.category,
    description = excluded.description,
    is_read_only = excluded.is_read_only,
    default_risk_level = excluded.default_risk_level,
    input_schema = excluded.input_schema,
    enabled = true;

insert into agent_mcp_tool_permissions
    (agent_id, mcp_tool_id, permission_mode, max_risk_level, requires_approval, argument_constraints)
select a.id, t.id, 'allow', 'low', false, '{}'::jsonb
from agent_profiles a
cross join mcp_tools t
where a.slug = 'mcp_read_agent'
on conflict (agent_id, mcp_tool_id) do update set
    permission_mode = excluded.permission_mode,
    max_risk_level = excluded.max_risk_level,
    requires_approval = excluded.requires_approval,
    argument_constraints = excluded.argument_constraints;

insert into agent_mcp_tool_permissions
    (agent_id, mcp_tool_id, permission_mode, max_risk_level, requires_approval, argument_constraints)
select a.id, t.id, 'allow', 'low', false, '{}'::jsonb
from agent_profiles a
join mcp_tools t on t.name in (
    'system_get_metrics_snapshot',
    'system_list_processes',
    'system_get_top_memory_processes',
    'network_list_connections',
    'system_get_platform_info'
)
where a.slug = 'crewai_diagnostics_agent'
on conflict (agent_id, mcp_tool_id) do update set
    permission_mode = excluded.permission_mode,
    max_risk_level = excluded.max_risk_level,
    requires_approval = excluded.requires_approval,
    argument_constraints = excluded.argument_constraints;

insert into agent_intent_routes
    (intent_key, priority, matcher, target_agent_id, target_langgraph_node, route_type, approval_policy, enabled)
select 'CHAT', 10, '{}'::jsonb, id, 'direct_chat_node', 'chat', 'none', true
from agent_profiles where slug = 'direct_chat_agent'
on conflict (intent_key, target_langgraph_node, route_type) do update set
    priority = excluded.priority,
    matcher = excluded.matcher,
    target_agent_id = excluded.target_agent_id,
    approval_policy = excluded.approval_policy,
    enabled = excluded.enabled;

insert into agent_intent_routes
    (intent_key, priority, matcher, target_agent_id, target_langgraph_node, route_type, approval_policy, enabled)
select intent_key, 20, matcher, id, 'mcp_read_only_node', 'mcp_read_only', 'none', true
from agent_profiles
cross join (
    values
        ('FILE_SYSTEM_READ', '{"supported_by":"mcp_read_agent"}'::jsonb),
        ('DEVOPS_READ', '{"supported_by":"mcp_read_agent"}'::jsonb),
        ('NETWORK_READ', '{"supported_by":"mcp_read_agent"}'::jsonb)
) as route(intent_key, matcher)
where slug = 'mcp_read_agent'
on conflict (intent_key, target_langgraph_node, route_type) do update set
    priority = excluded.priority,
    matcher = excluded.matcher,
    target_agent_id = excluded.target_agent_id,
    approval_policy = excluded.approval_policy,
    enabled = excluded.enabled;

insert into agent_intent_routes
    (intent_key, priority, matcher, target_agent_id, target_langgraph_node, route_type, approval_policy, enabled)
select 'SYSTEM_OPERATION', 30, '{"diagnostic_terms":["why","investigate","diagnose","analyze","slow","suspicious","security","leak","problem","issue"]}'::jsonb, id, 'run_crewai_diagnostics_node', 'crewai_diagnostics', 'risk_based', true
from agent_profiles where slug = 'crewai_diagnostics_agent'
on conflict (intent_key, target_langgraph_node, route_type) do update set
    priority = excluded.priority,
    matcher = excluded.matcher,
    target_agent_id = excluded.target_agent_id,
    approval_policy = excluded.approval_policy,
    enabled = excluded.enabled;

insert into agent_intent_routes
    (intent_key, priority, matcher, target_agent_id, target_langgraph_node, route_type, approval_policy, enabled)
select intent_key, 90, '{}'::jsonb, id, 'generate_action_script_node', 'script_proposal', 'always', true
from agent_profiles
cross join (
    values
        ('FILE_SYSTEM_WRITE'),
        ('APP_CONTROL'),
        ('DEVOPS_WRITE'),
        ('UNKNOWN')
) as route(intent_key)
where slug = 'script_proposal_agent'
on conflict (intent_key, target_langgraph_node, route_type) do update set
    priority = excluded.priority,
    matcher = excluded.matcher,
    target_agent_id = excluded.target_agent_id,
    approval_policy = excluded.approval_policy,
    enabled = excluded.enabled;

insert into agent_risk_policies
    (name, description, default_approval_required, max_autonomous_risk, enabled)
values
    ('default_terminal_safety', 'Default SysAgent approval and blocking rules for terminal operations.', true, 'low', true)
on conflict (name) do update set
    description = excluded.description,
    default_approval_required = excluded.default_approval_required,
    max_autonomous_risk = excluded.max_autonomous_risk,
    enabled = excluded.enabled;

insert into agent_risk_policy_rules
    (policy_id, rule_type, pattern, effect, risk_level, reason, priority, enabled)
select p.id, rule_type, pattern, effect, risk_level, reason, priority, true
from agent_risk_policies p
cross join (
    values
        ('command_contains', 'rm -rf /', 'block', 'high', 'Blocks recursive root deletion.', 1),
        ('command_contains', 'mkfs', 'block', 'high', 'Blocks filesystem formatting.', 2),
        ('command_contains', 'dd if=', 'block', 'high', 'Blocks raw disk overwrite patterns.', 3),
        ('command_contains', 'shutdown', 'block', 'high', 'Blocks shutdown commands.', 4),
        ('command_contains', 'reboot', 'block', 'high', 'Blocks reboot commands.', 5),
        ('path_prefix', 'c:\windows', 'block', 'high', 'Blocks Windows system directory mutation.', 10),
        ('path_prefix', 'c:\program files', 'block', 'high', 'Blocks Program Files mutation.', 11),
        ('path_prefix', '/etc', 'block', 'high', 'Blocks Unix system configuration mutation.', 12),
        ('path_prefix', '/boot', 'block', 'high', 'Blocks boot directory mutation.', 13),
        ('intent_key', 'FILE_SYSTEM_WRITE', 'require_approval', 'medium', 'File writes require user approval.', 40),
        ('intent_key', 'APP_CONTROL', 'require_approval', 'medium', 'Application control requires user approval.', 41),
        ('intent_key', 'DEVOPS_WRITE', 'require_approval', 'medium', 'DevOps write operations require user approval.', 42),
        ('intent_key', 'UNKNOWN', 'require_approval', 'high', 'Unknown actions require user approval.', 43)
) as rule(rule_type, pattern, effect, risk_level, reason, priority)
where p.name = 'default_terminal_safety'
on conflict (policy_id, rule_type, pattern, effect) do update set
    risk_level = excluded.risk_level,
    reason = excluded.reason,
    priority = excluded.priority,
    enabled = excluded.enabled;
