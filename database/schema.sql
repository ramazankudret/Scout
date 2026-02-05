-- Scout Database Schema v1.0
-- PostgreSQL 15+ with pgvector extension
-- Run this in PgAdmin Query Tool

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Text search

-- ============================================
-- 1. USERS - Kullanıcı Hesapları
-- ============================================
CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email               VARCHAR(255) UNIQUE NOT NULL,
    username            VARCHAR(100) UNIQUE,
    hashed_password     VARCHAR(255) NOT NULL,
    full_name           VARCHAR(200),
    phone               VARCHAR(20),
    avatar_url          VARCHAR(500),
    timezone            VARCHAR(50) DEFAULT 'Europe/Istanbul',
    locale              VARCHAR(10) DEFAULT 'tr',
    is_active           BOOLEAN DEFAULT true,
    is_verified         BOOLEAN DEFAULT false,
    is_superuser        BOOLEAN DEFAULT false,
    mfa_enabled         BOOLEAN DEFAULT false,
    mfa_secret          VARCHAR(100),
    last_login_at       TIMESTAMP WITH TIME ZONE,
    last_login_ip       INET,
    failed_login_count  INTEGER DEFAULT 0,
    locked_until        TIMESTAMP WITH TIME ZONE,
    password_changed_at TIMESTAMP WITH TIME ZONE,
    preferences         JSONB DEFAULT '{}',
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE,
    deleted_at          TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;

-- ============================================
-- 2. SUBSCRIPTIONS - Abonelik
-- ============================================
CREATE TABLE subscriptions (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tier                    VARCHAR(20) NOT NULL DEFAULT 'free',
    status                  VARCHAR(20) NOT NULL DEFAULT 'active',
    started_at              TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at              TIMESTAMP WITH TIME ZONE,
    trial_ends_at           TIMESTAMP WITH TIME ZONE,
    cancelled_at            TIMESTAMP WITH TIME ZONE,
    cancel_reason           TEXT,
    payment_method          VARCHAR(50),
    stripe_customer_id      VARCHAR(100),
    stripe_subscription_id  VARCHAR(100),
    quota_scans_daily       INTEGER DEFAULT 10,
    quota_assets            INTEGER DEFAULT 50,
    quota_users             INTEGER DEFAULT 1,
    quota_agents            INTEGER DEFAULT 4,
    quota_api_calls         INTEGER DEFAULT 1000,
    quota_storage_gb        NUMERIC(10,2) DEFAULT 1.0,
    usage_scans_today       INTEGER DEFAULT 0,
    usage_assets            INTEGER DEFAULT 0,
    usage_api_calls_today   INTEGER DEFAULT 0,
    usage_storage_gb        NUMERIC(10,2) DEFAULT 0,
    last_quota_reset        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    auto_renew              BOOLEAN DEFAULT true,
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE,
    CONSTRAINT chk_tier CHECK (tier IN ('free', 'pro', 'enterprise', 'ultimate')),
    CONSTRAINT chk_status CHECK (status IN ('active', 'trial', 'cancelled', 'expired', 'suspended'))
);

CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

-- ============================================
-- 3. ASSETS - Varlıklar (IP/Host/Servis)
-- ============================================
CREATE TABLE assets (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    asset_type          VARCHAR(30) NOT NULL,
    value               VARCHAR(500) NOT NULL,
    label               VARCHAR(200),
    description         TEXT,
    ip_address          INET,
    mac_address         MACADDR,
    hostname            VARCHAR(255),
    fqdn                VARCHAR(500),
    datacenter          VARCHAR(100),
    region              VARCHAR(100),
    availability_zone   VARCHAR(100),
    physical_location   VARCHAR(200),
    os_family           VARCHAR(50),
    os_name             VARCHAR(100),
    os_version          VARCHAR(50),
    architecture        VARCHAR(20),
    status              VARCHAR(30) DEFAULT 'active',
    criticality         VARCHAR(20) DEFAULT 'medium',
    environment         VARCHAR(30) DEFAULT 'production',
    owner_name          VARCHAR(200),
    owner_email         VARCHAR(255),
    department          VARCHAR(100),
    cost_center         VARCHAR(50),
    open_ports          INTEGER[],
    services            JSONB DEFAULT '[]',
    last_scan_at        TIMESTAMP WITH TIME ZONE,
    last_vuln_scan_at   TIMESTAMP WITH TIME ZONE,
    vulnerability_count INTEGER DEFAULT 0,
    risk_score          NUMERIC(5,2) DEFAULT 0,
    compliance_status   VARCHAR(30) DEFAULT 'unknown',
    first_seen_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE,
    deleted_at          TIMESTAMP WITH TIME ZONE,
    tags                TEXT[],
    metadata            JSONB DEFAULT '{}',
    CONSTRAINT chk_asset_type CHECK (asset_type IN ('ip', 'hostname', 'domain', 'subnet', 'cloud_instance', 'container', 'service')),
    CONSTRAINT chk_status CHECK (status IN ('active', 'inactive', 'maintenance', 'decommissioned', 'compromised', 'suspicious')),
    CONSTRAINT chk_criticality CHECK (criticality IN ('low', 'medium', 'high', 'critical'))
);

CREATE INDEX idx_assets_user ON assets(user_id);
CREATE INDEX idx_assets_type ON assets(asset_type);
CREATE INDEX idx_assets_value ON assets(value);
CREATE INDEX idx_assets_ip ON assets(ip_address);
CREATE INDEX idx_assets_status ON assets(status);
CREATE INDEX idx_assets_risk ON assets(risk_score DESC);
CREATE INDEX idx_assets_tags ON assets USING GIN(tags);

-- ============================================
-- 4. INCIDENTS - Güvenlik Olayları
-- ============================================
CREATE TABLE incidents (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    asset_id            UUID REFERENCES assets(id) ON DELETE SET NULL,
    incident_number     VARCHAR(50) UNIQUE,
    title               VARCHAR(500) NOT NULL,
    description         TEXT,
    threat_type         VARCHAR(100),
    attack_vector       VARCHAR(100),
    kill_chain_phase    VARCHAR(50),
    severity            VARCHAR(20) NOT NULL DEFAULT 'medium',
    priority            VARCHAR(20) DEFAULT 'p3',
    impact_score        NUMERIC(5,2),
    confidence_score    NUMERIC(5,2),
    source_ip           INET,
    source_port         INTEGER,
    source_country      VARCHAR(3),
    source_asn          VARCHAR(50),
    source_isp          VARCHAR(200),
    source_is_tor       BOOLEAN DEFAULT false,
    source_is_vpn       BOOLEAN DEFAULT false,
    source_is_proxy     BOOLEAN DEFAULT false,
    target_ip           INET,
    target_port         INTEGER,
    target_url          VARCHAR(2000),
    target_user         VARCHAR(200),
    detected_by         VARCHAR(100),
    detection_method    VARCHAR(100),
    rule_id             VARCHAR(100),
    payload_preview     TEXT,
    payload_hash        VARCHAR(128),
    raw_log             TEXT,
    indicators          JSONB DEFAULT '{}',
    status              VARCHAR(30) NOT NULL DEFAULT 'new',
    resolution          VARCHAR(50),
    assigned_to         UUID REFERENCES users(id) ON DELETE SET NULL,
    detected_at         TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    acknowledged_at     TIMESTAMP WITH TIME ZONE,
    contained_at        TIMESTAMP WITH TIME ZONE,
    resolved_at         TIMESTAMP WITH TIME ZONE,
    closed_at           TIMESTAMP WITH TIME ZONE,
    mitre_tactic        VARCHAR(100),
    mitre_technique     VARCHAR(100),
    mitre_subtechnique  VARCHAR(100),
    affected_users      INTEGER DEFAULT 0,
    affected_systems    INTEGER DEFAULT 0,
    data_exfiltrated    BOOLEAN DEFAULT false,
    downtime_minutes    INTEGER DEFAULT 0,
    financial_impact    NUMERIC(15,2),
    parent_incident_id  UUID REFERENCES incidents(id),
    related_incidents   UUID[],
    is_automated        BOOLEAN DEFAULT false,
    is_recurring        BOOLEAN DEFAULT false,
    tags                TEXT[],
    notes               TEXT,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE,
    CONSTRAINT chk_severity CHECK (severity IN ('info', 'low', 'medium', 'high', 'critical')),
    CONSTRAINT chk_status CHECK (status IN ('new', 'investigating', 'contained', 'eradicated', 'recovered', 'closed', 'false_positive'))
);

CREATE INDEX idx_incidents_user ON incidents(user_id);
CREATE INDEX idx_incidents_asset ON incidents(asset_id);
CREATE INDEX idx_incidents_status ON incidents(status);
CREATE INDEX idx_incidents_severity ON incidents(severity);
CREATE INDEX idx_incidents_detected ON incidents(detected_at DESC);
CREATE INDEX idx_incidents_source_ip ON incidents(source_ip);
CREATE INDEX idx_incidents_threat_type ON incidents(threat_type);
CREATE INDEX idx_incidents_tags ON incidents USING GIN(tags);

-- ============================================
-- 5. SCAN_RESULTS - Tarama Sonuçları
-- ============================================
CREATE TABLE scan_results (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    asset_id            UUID REFERENCES assets(id) ON DELETE SET NULL,
    scan_type           VARCHAR(50) NOT NULL,
    scan_profile        VARCHAR(100),
    scanner_used        VARCHAR(50),
    scanner_version     VARCHAR(30),
    target              VARCHAR(500) NOT NULL,
    target_type         VARCHAR(30),
    ports_scanned       VARCHAR(200),
    status              VARCHAR(30) NOT NULL DEFAULT 'pending',
    exit_code           INTEGER,
    open_ports          INTEGER[],
    closed_ports_count  INTEGER,
    filtered_ports_count INTEGER,
    services_found      JSONB DEFAULT '[]',
    os_detection        JSONB DEFAULT '{}',
    vulnerabilities_found INTEGER DEFAULT 0,
    hosts_discovered    INTEGER DEFAULT 0,
    raw_output          TEXT,
    parsed_results      JSONB DEFAULT '{}',
    started_at          TIMESTAMP WITH TIME ZONE,
    completed_at        TIMESTAMP WITH TIME ZONE,
    duration_seconds    INTEGER,
    packets_sent        BIGINT,
    packets_received    BIGINT,
    error_message       TEXT,
    retry_count         INTEGER DEFAULT 0,
    triggered_by        VARCHAR(50),
    parent_scan_id      UUID REFERENCES scan_results(id),
    tags                TEXT[],
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT chk_scan_type CHECK (scan_type IN ('port_scan', 'vuln_scan', 'web_scan', 'network_discovery', 'compliance', 'custom')),
    CONSTRAINT chk_scan_status CHECK (status IN ('pending', 'queued', 'running', 'completed', 'failed', 'cancelled', 'timeout'))
);

CREATE INDEX idx_scans_user ON scan_results(user_id);
CREATE INDEX idx_scans_asset ON scan_results(asset_id);
CREATE INDEX idx_scans_status ON scan_results(status);
CREATE INDEX idx_scans_created ON scan_results(created_at DESC);

-- ============================================
-- 6. VULNERABILITIES - Açıklar
-- ============================================
CREATE TABLE vulnerabilities (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id            UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    scan_result_id      UUID REFERENCES scan_results(id) ON DELETE SET NULL,
    cve_id              VARCHAR(20),
    cwe_id              VARCHAR(20),
    nvd_url             VARCHAR(500),
    title               VARCHAR(500) NOT NULL,
    description         TEXT,
    solution            TEXT,
    references          TEXT[],
    cvss_version        VARCHAR(10),
    cvss_score          NUMERIC(3,1),
    cvss_vector         VARCHAR(200),
    severity            VARCHAR(20) NOT NULL DEFAULT 'medium',
    affected_component  VARCHAR(300),
    affected_version    VARCHAR(100),
    affected_port       INTEGER,
    affected_service    VARCHAR(100),
    affected_url        VARCHAR(2000),
    exploit_available   BOOLEAN DEFAULT false,
    exploit_maturity    VARCHAR(30),
    exploit_db_id       VARCHAR(50),
    metasploit_module   VARCHAR(200),
    status              VARCHAR(30) NOT NULL DEFAULT 'open',
    risk_accepted_by    UUID REFERENCES users(id),
    risk_accepted_at    TIMESTAMP WITH TIME ZONE,
    risk_accepted_reason TEXT,
    patch_available     BOOLEAN DEFAULT false,
    patch_name          VARCHAR(200),
    patch_url           VARCHAR(500),
    patched_at          TIMESTAMP WITH TIME ZONE,
    patched_by          UUID REFERENCES users(id),
    first_detected_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_detected_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    verified_at         TIMESTAMP WITH TIME ZONE,
    fixed_at            TIMESTAMP WITH TIME ZONE,
    sla_due_date        TIMESTAMP WITH TIME ZONE,
    sla_breached        BOOLEAN DEFAULT false,
    false_positive      BOOLEAN DEFAULT false,
    verified            BOOLEAN DEFAULT false,
    verification_method VARCHAR(100),
    notes               TEXT,
    tags                TEXT[],
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE,
    CONSTRAINT chk_vuln_severity CHECK (severity IN ('info', 'low', 'medium', 'high', 'critical')),
    CONSTRAINT chk_vuln_status CHECK (status IN ('open', 'in_progress', 'fixed', 'accepted_risk', 'false_positive', 'wont_fix'))
);

CREATE INDEX idx_vulns_asset ON vulnerabilities(asset_id);
CREATE INDEX idx_vulns_cve ON vulnerabilities(cve_id);
CREATE INDEX idx_vulns_severity ON vulnerabilities(severity);
CREATE INDEX idx_vulns_status ON vulnerabilities(status);
CREATE INDEX idx_vulns_cvss ON vulnerabilities(cvss_score DESC);

-- ============================================
-- 7. AGENT_RUNS - Agent Çalışma Kayıtları
-- ============================================
CREATE TABLE agent_runs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_name          VARCHAR(50) NOT NULL,
    agent_version       VARCHAR(20),
    task_id             VARCHAR(100),
    task_type           VARCHAR(100),
    task_priority       VARCHAR(20),
    task_description    TEXT,
    input_data          JSONB DEFAULT '{}',
    input_tokens        INTEGER,
    output_data         JSONB DEFAULT '{}',
    output_tokens       INTEGER,
    status              VARCHAR(30) NOT NULL DEFAULT 'queued',
    progress_percent    INTEGER DEFAULT 0,
    current_step        VARCHAR(200),
    steps_completed     INTEGER DEFAULT 0,
    steps_total         INTEGER,
    queued_at           TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at          TIMESTAMP WITH TIME ZONE,
    completed_at        TIMESTAMP WITH TIME ZONE,
    duration_ms         INTEGER,
    timeout_ms          INTEGER DEFAULT 300000,
    cpu_usage_percent   NUMERIC(5,2),
    memory_usage_mb     NUMERIC(10,2),
    network_bytes_in    BIGINT,
    network_bytes_out   BIGINT,
    llm_model           VARCHAR(100),
    llm_calls_count     INTEGER DEFAULT 0,
    llm_total_tokens    INTEGER DEFAULT 0,
    llm_cost_usd        NUMERIC(10,4) DEFAULT 0,
    error_code          VARCHAR(50),
    error_message       TEXT,
    error_stack_trace   TEXT,
    retry_count         INTEGER DEFAULT 0,
    parent_run_id       UUID REFERENCES agent_runs(id),
    child_runs          UUID[],
    triggered_by        VARCHAR(50),
    related_incident_id UUID REFERENCES incidents(id),
    related_asset_id    UUID REFERENCES assets(id),
    findings_count      INTEGER DEFAULT 0,
    actions_taken       JSONB DEFAULT '[]',
    recommendations     JSONB DEFAULT '[]',
    is_automated        BOOLEAN DEFAULT true,
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT chk_agent_name CHECK (agent_name IN ('orchestrator', 'hunter', 'stealth', 'defense', 'analyst')),
    CONSTRAINT chk_run_status CHECK (status IN ('queued', 'running', 'completed', 'failed', 'timeout', 'cancelled'))
);

CREATE INDEX idx_agent_runs_user ON agent_runs(user_id);
CREATE INDEX idx_agent_runs_agent ON agent_runs(agent_name);
CREATE INDEX idx_agent_runs_status ON agent_runs(status);
CREATE INDEX idx_agent_runs_created ON agent_runs(created_at DESC);

-- ============================================
-- 8. AGENT_MEMORIES - AI Vektör Hafızası
-- ============================================
CREATE TABLE agent_memories (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name          VARCHAR(50) NOT NULL,
    memory_type         VARCHAR(50) NOT NULL,
    title               VARCHAR(500),
    content             TEXT NOT NULL,
    summary             TEXT,
    embedding           VECTOR(1536),
    embedding_model     VARCHAR(100) DEFAULT 'text-embedding-ada-002',
    source_type         VARCHAR(50),
    source_id           UUID,
    source_url          VARCHAR(500),
    importance_score    NUMERIC(5,2) DEFAULT 50,
    confidence_score    NUMERIC(5,2) DEFAULT 80,
    relevance_decay     NUMERIC(5,4) DEFAULT 0.01,
    access_count        INTEGER DEFAULT 0,
    last_accessed_at    TIMESTAMP WITH TIME ZONE,
    usefulness_rating   NUMERIC(3,2),
    related_memories    UUID[],
    tags                TEXT[],
    event_timestamp     TIMESTAMP WITH TIME ZONE,
    expires_at          TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE,
    metadata            JSONB DEFAULT '{}',
    is_archived         BOOLEAN DEFAULT false,
    CONSTRAINT chk_memory_type CHECK (memory_type IN ('incident', 'lesson', 'pattern', 'context', 'knowledge', 'conversation'))
);

CREATE INDEX idx_memories_agent ON agent_memories(agent_name);
CREATE INDEX idx_memories_type ON agent_memories(memory_type);
CREATE INDEX idx_memories_importance ON agent_memories(importance_score DESC);
CREATE INDEX idx_memories_embedding ON agent_memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================
-- 9. LEARNED_LESSONS - Öğrenilen Dersler
-- ============================================
CREATE TABLE learned_lessons (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id         UUID REFERENCES incidents(id) ON DELETE SET NULL,
    agent_run_id        UUID REFERENCES agent_runs(id) ON DELETE SET NULL,
    failure_type        VARCHAR(100),
    failure_description TEXT,
    root_cause          TEXT,
    what_happened       TEXT,
    why_it_happened     TEXT,
    what_was_expected   TEXT,
    gap_analysis        TEXT,
    proposed_solution   TEXT,
    solution_type       VARCHAR(50),
    implementation_steps JSONB DEFAULT '[]',
    applied             BOOLEAN DEFAULT false,
    applied_at          TIMESTAMP WITH TIME ZONE,
    applied_by          VARCHAR(50),
    applied_changes     JSONB DEFAULT '[]',
    effectiveness_score NUMERIC(5,2),
    prevented_incidents INTEGER DEFAULT 0,
    llm_analysis        JSONB DEFAULT '{}',
    analysis_confidence NUMERIC(5,2),
    verified            BOOLEAN DEFAULT false,
    verified_by         UUID REFERENCES users(id),
    verified_at         TIMESTAMP WITH TIME ZONE,
    verification_notes  TEXT,
    priority            VARCHAR(20) DEFAULT 'medium',
    tags                TEXT[],
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_lessons_incident ON learned_lessons(incident_id);
CREATE INDEX idx_lessons_applied ON learned_lessons(applied);

-- ============================================
-- 10. DEFENSE_RULES - Savunma Kuralları
-- ============================================
CREATE TABLE defense_rules (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name                VARCHAR(200) NOT NULL,
    description         TEXT,
    rule_type           VARCHAR(50) NOT NULL,
    conditions          JSONB NOT NULL,
    action              VARCHAR(50) NOT NULL,
    action_params       JSONB DEFAULT '{}',
    applies_to          VARCHAR(50) DEFAULT 'all',
    target_assets       UUID[],
    target_tags         TEXT[],
    priority            INTEGER DEFAULT 100,
    is_active           BOOLEAN DEFAULT true,
    is_temporary        BOOLEAN DEFAULT false,
    expires_at          TIMESTAMP WITH TIME ZONE,
    source              VARCHAR(50) DEFAULT 'manual',
    source_incident_id  UUID REFERENCES incidents(id),
    source_lesson_id    UUID REFERENCES learned_lessons(id),
    match_count         BIGINT DEFAULT 0,
    last_matched_at     TIMESTAMP WITH TIME ZONE,
    block_count         BIGINT DEFAULT 0,
    false_positive_count INTEGER DEFAULT 0,
    is_test_mode        BOOLEAN DEFAULT false,
    test_mode_until     TIMESTAMP WITH TIME ZONE,
    version             INTEGER DEFAULT 1,
    previous_version_id UUID REFERENCES defense_rules(id),
    notes               TEXT,
    tags                TEXT[],
    created_by          UUID REFERENCES users(id),
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE,
    deleted_at          TIMESTAMP WITH TIME ZONE,
    CONSTRAINT chk_rule_type CHECK (rule_type IN ('firewall', 'waf', 'rate_limit', 'geo_block', 'user_block', 'ip_block', 'custom')),
    CONSTRAINT chk_action CHECK (action IN ('block', 'allow', 'challenge', 'redirect', 'rate_limit', 'log_only', 'alert'))
);

CREATE INDEX idx_rules_user ON defense_rules(user_id);
CREATE INDEX idx_rules_active ON defense_rules(is_active) WHERE is_active = true;
CREATE INDEX idx_rules_priority ON defense_rules(priority);

-- ============================================
-- 11. NOTIFICATIONS - Bildirimler
-- ============================================
CREATE TABLE notifications (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type   VARCHAR(50) NOT NULL,
    category            VARCHAR(50),
    title               VARCHAR(300) NOT NULL,
    message             TEXT,
    severity            VARCHAR(20) DEFAULT 'info',
    related_type        VARCHAR(50),
    related_id          UUID,
    related_url         VARCHAR(500),
    actions             JSONB DEFAULT '[]',
    is_read             BOOLEAN DEFAULT false,
    read_at             TIMESTAMP WITH TIME ZONE,
    is_dismissed        BOOLEAN DEFAULT false,
    dismissed_at        TIMESTAMP WITH TIME ZONE,
    is_actionable       BOOLEAN DEFAULT false,
    action_taken        BOOLEAN DEFAULT false,
    action_taken_at     TIMESTAMP WITH TIME ZONE,
    channels_sent       TEXT[],
    email_sent_at       TIMESTAMP WITH TIME ZONE,
    slack_sent_at       TIMESTAMP WITH TIME ZONE,
    sms_sent_at         TIMESTAMP WITH TIME ZONE,
    group_key           VARCHAR(200),
    grouped_count       INTEGER DEFAULT 1,
    show_after          TIMESTAMP WITH TIME ZONE,
    expires_at          TIMESTAMP WITH TIME ZONE,
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = false;
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);

-- ============================================
-- 12. AUDIT_LOGS - Denetim Kayıtları
-- ============================================
CREATE TABLE audit_logs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID REFERENCES users(id) ON DELETE SET NULL,
    user_email          VARCHAR(255),
    is_system           BOOLEAN DEFAULT false,
    actor_type          VARCHAR(30) NOT NULL,
    actor_id            VARCHAR(100),
    action              VARCHAR(100) NOT NULL,
    action_category     VARCHAR(50),
    resource_type       VARCHAR(100),
    resource_id         UUID,
    resource_name       VARCHAR(300),
    description         TEXT,
    changes             JSONB DEFAULT '{}',
    request_path        VARCHAR(500),
    request_method      VARCHAR(10),
    request_body        JSONB,
    response_status     INTEGER,
    ip_address          INET,
    user_agent          VARCHAR(500),
    country_code        VARCHAR(3),
    city                VARCHAR(100),
    device_type         VARCHAR(50),
    device_os           VARCHAR(50),
    browser             VARCHAR(100),
    session_id          VARCHAR(100),
    api_key_id          UUID,
    success             BOOLEAN DEFAULT true,
    failure_reason      TEXT,
    is_suspicious       BOOLEAN DEFAULT false,
    risk_score          NUMERIC(5,2),
    flagged_by          VARCHAR(100),
    duration_ms         INTEGER,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    retention_until     TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_created ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_suspicious ON audit_logs(is_suspicious) WHERE is_suspicious = true;

-- ============================================
-- 13. LLM_LOGS - LLM Kullanım Kayıtları
-- ============================================
CREATE TABLE llm_logs (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                 UUID REFERENCES users(id) ON DELETE SET NULL,
    agent_run_id            UUID REFERENCES agent_runs(id) ON DELETE SET NULL,
    provider                VARCHAR(50) NOT NULL,
    model                   VARCHAR(100) NOT NULL,
    model_version           VARCHAR(50),
    prompt_template         VARCHAR(200),
    system_prompt_hash      VARCHAR(64),
    user_prompt_preview     TEXT,
    user_prompt_hash        VARCHAR(64),
    full_prompt_tokens      INTEGER,
    response_preview        TEXT,
    response_tokens         INTEGER,
    total_tokens            INTEGER,
    finish_reason           VARCHAR(30),
    cost_input_usd          NUMERIC(10,6),
    cost_output_usd         NUMERIC(10,6),
    cost_total_usd          NUMERIC(10,6),
    latency_ms              INTEGER,
    time_to_first_token_ms  INTEGER,
    tokens_per_second       NUMERIC(10,2),
    was_filtered            BOOLEAN DEFAULT false,
    filter_reason           VARCHAR(100),
    was_blocked             BOOLEAN DEFAULT false,
    block_reason            VARCHAR(100),
    risk_score              NUMERIC(5,2),
    rating                  INTEGER,
    feedback                TEXT,
    attempt_number          INTEGER DEFAULT 1,
    previous_attempt_id     UUID REFERENCES llm_logs(id),
    error                   BOOLEAN DEFAULT false,
    error_code              VARCHAR(50),
    error_message           TEXT,
    cache_hit               BOOLEAN DEFAULT false,
    cache_key               VARCHAR(100),
    temperature             NUMERIC(3,2),
    max_tokens              INTEGER,
    top_p                   NUMERIC(3,2),
    request_metadata        JSONB DEFAULT '{}',
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_llm_user ON llm_logs(user_id);
CREATE INDEX idx_llm_agent ON llm_logs(agent_run_id);
CREATE INDEX idx_llm_model ON llm_logs(model);
CREATE INDEX idx_llm_created ON llm_logs(created_at DESC);
CREATE INDEX idx_llm_blocked ON llm_logs(was_blocked) WHERE was_blocked = true;

-- ============================================
-- 14. API_KEYS - API Anahtarları
-- ============================================
CREATE TABLE api_keys (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name                VARCHAR(200) NOT NULL,
    key_prefix          VARCHAR(10),
    key_hash            VARCHAR(128) NOT NULL,
    scopes              TEXT[] DEFAULT ARRAY['read:*'],
    allowed_ips         INET[],
    allowed_origins     TEXT[],
    rate_limit          INTEGER DEFAULT 100,
    is_active           BOOLEAN DEFAULT true,
    is_revoked          BOOLEAN DEFAULT false,
    revoked_at          TIMESTAMP WITH TIME ZONE,
    revoked_by          UUID REFERENCES users(id),
    revoke_reason       TEXT,
    last_used_at        TIMESTAMP WITH TIME ZONE,
    last_used_ip        INET,
    usage_count         BIGINT DEFAULT 0,
    usage_today         INTEGER DEFAULT 0,
    expires_at          TIMESTAMP WITH TIME ZONE,
    never_expires       BOOLEAN DEFAULT false,
    description         TEXT,
    environment         VARCHAR(30) DEFAULT 'development',
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_api_keys_user ON api_keys(user_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_active ON api_keys(is_active) WHERE is_active = true;

-- ============================================
-- 15. SESSIONS - Kullanıcı Oturumları
-- ============================================
CREATE TABLE sessions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash          VARCHAR(128) NOT NULL,
    refresh_token_hash  VARCHAR(128),
    device_id           VARCHAR(100),
    device_name         VARCHAR(200),
    device_type         VARCHAR(50),
    device_os           VARCHAR(100),
    device_os_version   VARCHAR(50),
    browser             VARCHAR(100),
    browser_version     VARCHAR(50),
    ip_address          INET,
    country_code        VARCHAR(3),
    country_name        VARCHAR(100),
    city                VARCHAR(100),
    latitude            NUMERIC(10,7),
    longitude           NUMERIC(10,7),
    is_active           BOOLEAN DEFAULT true,
    is_revoked          BOOLEAN DEFAULT false,
    revoked_at          TIMESTAMP WITH TIME ZONE,
    revoked_reason      VARCHAR(100),
    mfa_verified        BOOLEAN DEFAULT false,
    mfa_verified_at     TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_activity_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at          TIMESTAMP WITH TIME ZONE NOT NULL,
    is_suspicious       BOOLEAN DEFAULT false,
    risk_score          NUMERIC(5,2),
    security_flags      JSONB DEFAULT '{}'
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(token_hash);
CREATE INDEX idx_sessions_active ON sessions(is_active) WHERE is_active = true;

-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to all tables with updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_assets_updated_at BEFORE UPDATE ON assets 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_incidents_updated_at BEFORE UPDATE ON incidents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_vulnerabilities_updated_at BEFORE UPDATE ON vulnerabilities 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_learned_lessons_updated_at BEFORE UPDATE ON learned_lessons 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_defense_rules_updated_at BEFORE UPDATE ON defense_rules 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_notifications_updated_at BEFORE UPDATE ON notifications 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON api_keys 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-generate incident number
CREATE OR REPLACE FUNCTION generate_incident_number()
RETURNS TRIGGER AS $$
BEGIN
    NEW.incident_number = 'INC-' || TO_CHAR(NOW(), 'YYYY') || '-' || LPAD(NEXTVAL('incident_number_seq')::TEXT, 5, '0');
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE SEQUENCE incident_number_seq START 1;

CREATE TRIGGER set_incident_number BEFORE INSERT ON incidents
    FOR EACH ROW WHEN (NEW.incident_number IS NULL)
    EXECUTE FUNCTION generate_incident_number();

-- ============================================
-- SEED DATA (Demo User)
-- ============================================
INSERT INTO users (email, username, hashed_password, full_name, is_active, is_verified, is_superuser)
VALUES ('admin@scout.dev', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VN8nCd7QoK3jSa', 'Scout Admin', true, true, true);

-- Add subscription for admin
INSERT INTO subscriptions (user_id, tier, status, quota_scans_daily, quota_assets, quota_agents)
SELECT id, 'ultimate', 'active', 9999, 9999, 10
FROM users WHERE email = 'admin@scout.dev';

-- ============================================
-- COMPLETE! 🎉
-- ============================================
SELECT 'Scout Database Schema Created Successfully!' as status;
SELECT 
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE') as total_tables,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'public') as total_columns;
