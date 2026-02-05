"""
Scout Database Models - SQLAlchemy ORM
"""
from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    String, Text, Integer, BigInteger, Boolean, Numeric,
    ForeignKey, ARRAY, DateTime, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, INET, MACADDR, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

# Try to import pgvector, fallback if not available
try:
    from pgvector.sqlalchemy import Vector
    VECTOR_AVAILABLE = True
except ImportError:
    Vector = None
    VECTOR_AVAILABLE = False


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class TimestampMixin:
    """Mixin for created_at and updated_at columns"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


# ============================================
# 1. USER MODEL
# ============================================
class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Istanbul")
    locale: Mapped[str] = mapped_column(String(10), default="tr")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(100))
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login_ip: Mapped[Optional[str]] = mapped_column(INET)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Relationships (disabled)
    
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_active", "is_active", postgresql_where=(is_active == True)),
    )


# ============================================
# 2. SUBSCRIPTION MODEL
# ============================================
class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tier: Mapped[str] = mapped_column(String(20), default="free")
    status: Mapped[str] = mapped_column(String(20), default="active")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancel_reason: Mapped[Optional[str]] = mapped_column(Text)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(100))
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(100))
    # Quotas
    quota_scans_daily: Mapped[int] = mapped_column(Integer, default=10)
    quota_assets: Mapped[int] = mapped_column(Integer, default=50)
    quota_users: Mapped[int] = mapped_column(Integer, default=1)
    quota_agents: Mapped[int] = mapped_column(Integer, default=4)
    quota_api_calls: Mapped[int] = mapped_column(Integer, default=1000)
    quota_storage_gb: Mapped[float] = mapped_column(Numeric(10, 2), default=1.0)
    # Usage
    usage_scans_today: Mapped[int] = mapped_column(Integer, default=0)
    usage_assets: Mapped[int] = mapped_column(Integer, default=0)
    usage_api_calls_today: Mapped[int] = mapped_column(Integer, default=0)
    usage_storage_gb: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    last_quota_reset: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships (disabled)

    
    __table_args__ = (
        CheckConstraint("tier IN ('free', 'pro', 'enterprise', 'ultimate')", name="chk_tier"),
        CheckConstraint("status IN ('active', 'trial', 'cancelled', 'expired', 'suspended')", name="chk_status"),
    )


# ============================================
# 3. ASSET MODEL
# ============================================
class Asset(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "assets"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(30), nullable=False)
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    label: Mapped[Optional[str]] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    mac_address: Mapped[Optional[str]] = mapped_column(MACADDR)
    hostname: Mapped[Optional[str]] = mapped_column(String(255))
    fqdn: Mapped[Optional[str]] = mapped_column(String(500))
    datacenter: Mapped[Optional[str]] = mapped_column(String(100))
    region: Mapped[Optional[str]] = mapped_column(String(100))
    availability_zone: Mapped[Optional[str]] = mapped_column(String(100))
    physical_location: Mapped[Optional[str]] = mapped_column(String(200))
    os_family: Mapped[Optional[str]] = mapped_column(String(50))
    os_name: Mapped[Optional[str]] = mapped_column(String(100))
    os_version: Mapped[Optional[str]] = mapped_column(String(50))
    architecture: Mapped[Optional[str]] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), default="active")
    criticality: Mapped[str] = mapped_column(String(20), default="medium")
    environment: Mapped[str] = mapped_column(String(30), default="production")
    owner_name: Mapped[Optional[str]] = mapped_column(String(200))
    owner_email: Mapped[Optional[str]] = mapped_column(String(255))
    department: Mapped[Optional[str]] = mapped_column(String(100))
    cost_center: Mapped[Optional[str]] = mapped_column(String(50))
    open_ports: Mapped[Optional[List[int]]] = mapped_column(ARRAY(Integer))
    services: Mapped[dict] = mapped_column(JSONB, default=list)
    last_scan_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_vuln_scan_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    vulnerability_count: Mapped[int] = mapped_column(Integer, default=0)
    risk_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    compliance_status: Mapped[str] = mapped_column(String(30), default="unknown")
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    extra_data: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    
    # Relationships (disabled)






# ============================================
# 4. INCIDENT MODEL
# ============================================
class Incident(Base, TimestampMixin):
    __tablename__ = "incidents"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL"))
    incident_number: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    threat_type: Mapped[Optional[str]] = mapped_column(String(100))
    attack_vector: Mapped[Optional[str]] = mapped_column(String(100))
    kill_chain_phase: Mapped[Optional[str]] = mapped_column(String(50))
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    priority: Mapped[str] = mapped_column(String(20), default="p3")
    impact_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    confidence_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    source_ip: Mapped[Optional[str]] = mapped_column(INET)
    source_port: Mapped[Optional[int]] = mapped_column(Integer)
    source_country: Mapped[Optional[str]] = mapped_column(String(3))
    source_asn: Mapped[Optional[str]] = mapped_column(String(50))
    source_isp: Mapped[Optional[str]] = mapped_column(String(200))
    source_is_tor: Mapped[bool] = mapped_column(Boolean, default=False)
    source_is_vpn: Mapped[bool] = mapped_column(Boolean, default=False)
    source_is_proxy: Mapped[bool] = mapped_column(Boolean, default=False)
    target_ip: Mapped[Optional[str]] = mapped_column(INET)
    target_port: Mapped[Optional[int]] = mapped_column(Integer)
    target_url: Mapped[Optional[str]] = mapped_column(String(2000))
    target_user: Mapped[Optional[str]] = mapped_column(String(200))
    detected_by: Mapped[Optional[str]] = mapped_column(String(100))
    detection_method: Mapped[Optional[str]] = mapped_column(String(100))
    rule_id: Mapped[Optional[str]] = mapped_column(String(100))
    payload_preview: Mapped[Optional[str]] = mapped_column(Text)
    payload_hash: Mapped[Optional[str]] = mapped_column(String(128))
    raw_log: Mapped[Optional[str]] = mapped_column(Text)
    indicators: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="new")
    resolution: Mapped[Optional[str]] = mapped_column(String(50))
    assigned_to: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    contained_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    mitre_tactic: Mapped[Optional[str]] = mapped_column(String(100))
    mitre_technique: Mapped[Optional[str]] = mapped_column(String(100))
    mitre_subtechnique: Mapped[Optional[str]] = mapped_column(String(100))
    affected_users: Mapped[int] = mapped_column(Integer, default=0)
    affected_systems: Mapped[int] = mapped_column(Integer, default=0)
    data_exfiltrated: Mapped[bool] = mapped_column(Boolean, default=False)
    downtime_minutes: Mapped[int] = mapped_column(Integer, default=0)
    financial_impact: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    parent_incident_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("incidents.id"))
    related_incidents: Mapped[Optional[List[UUID]]] = mapped_column(ARRAY(PGUUID(as_uuid=True)))
    is_automated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships (disabled)





# ============================================
# 5. SCAN_RESULT MODEL
# ============================================
class ScanResult(Base):
    __tablename__ = "scan_results"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL"))
    scan_type: Mapped[str] = mapped_column(String(50), nullable=False)
    scan_profile: Mapped[Optional[str]] = mapped_column(String(100))
    scanner_used: Mapped[Optional[str]] = mapped_column(String(50))
    scanner_version: Mapped[Optional[str]] = mapped_column(String(30))
    target: Mapped[str] = mapped_column(String(500), nullable=False)
    target_type: Mapped[Optional[str]] = mapped_column(String(30))
    ports_scanned: Mapped[Optional[str]] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    exit_code: Mapped[Optional[int]] = mapped_column(Integer)
    open_ports: Mapped[Optional[List[int]]] = mapped_column(ARRAY(Integer))
    closed_ports_count: Mapped[Optional[int]] = mapped_column(Integer)
    filtered_ports_count: Mapped[Optional[int]] = mapped_column(Integer)
    services_found: Mapped[dict] = mapped_column(JSONB, default=list)
    os_detection: Mapped[dict] = mapped_column(JSONB, default=dict)
    vulnerabilities_found: Mapped[int] = mapped_column(Integer, default=0)
    hosts_discovered: Mapped[int] = mapped_column(Integer, default=0)
    raw_output: Mapped[Optional[str]] = mapped_column(Text)
    parsed_results: Mapped[dict] = mapped_column(JSONB, default=dict)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    packets_sent: Mapped[Optional[int]] = mapped_column(BigInteger)
    packets_received: Mapped[Optional[int]] = mapped_column(BigInteger)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    triggered_by: Mapped[Optional[str]] = mapped_column(String(50))
    parent_scan_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("scan_results.id"))
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships (disabled)



# ============================================
# 6. VULNERABILITY MODEL
# ============================================
class Vulnerability(Base, TimestampMixin):
    __tablename__ = "vulnerabilities"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    asset_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    scan_result_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("scan_results.id", ondelete="SET NULL"))
    cve_id: Mapped[Optional[str]] = mapped_column(String(20))
    cwe_id: Mapped[Optional[str]] = mapped_column(String(20))
    nvd_url: Mapped[Optional[str]] = mapped_column(String(500))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    solution: Mapped[Optional[str]] = mapped_column(Text)
    references: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    cvss_version: Mapped[Optional[str]] = mapped_column(String(10))
    cvss_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 1))
    cvss_vector: Mapped[Optional[str]] = mapped_column(String(200))
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    affected_component: Mapped[Optional[str]] = mapped_column(String(300))
    affected_version: Mapped[Optional[str]] = mapped_column(String(100))
    affected_port: Mapped[Optional[int]] = mapped_column(Integer)
    affected_service: Mapped[Optional[str]] = mapped_column(String(100))
    affected_url: Mapped[Optional[str]] = mapped_column(String(2000))
    exploit_available: Mapped[bool] = mapped_column(Boolean, default=False)
    exploit_maturity: Mapped[Optional[str]] = mapped_column(String(30))
    exploit_db_id: Mapped[Optional[str]] = mapped_column(String(50))
    metasploit_module: Mapped[Optional[str]] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="open")
    risk_accepted_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    risk_accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    risk_accepted_reason: Mapped[Optional[str]] = mapped_column(Text)
    patch_available: Mapped[bool] = mapped_column(Boolean, default=False)
    patch_name: Mapped[Optional[str]] = mapped_column(String(200))
    patch_url: Mapped[Optional[str]] = mapped_column(String(500))
    patched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    patched_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    first_detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    fixed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sla_due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sla_breached: Mapped[bool] = mapped_column(Boolean, default=False)
    false_positive: Mapped[bool] = mapped_column(Boolean, default=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_method: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    
    # Relationships (disabled)



# ============================================
# 7. AGENT_RUN MODEL
# ============================================
class AgentRun(Base):
    __tablename__ = "agent_runs"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    agent_version: Mapped[Optional[str]] = mapped_column(String(20))
    task_id: Mapped[Optional[str]] = mapped_column(String(100))
    task_type: Mapped[Optional[str]] = mapped_column(String(100))
    task_priority: Mapped[Optional[str]] = mapped_column(String(20))
    task_description: Mapped[Optional[str]] = mapped_column(Text)
    input_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    output_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="queued")
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[Optional[str]] = mapped_column(String(200))
    steps_completed: Mapped[int] = mapped_column(Integer, default=0)
    steps_total: Mapped[Optional[int]] = mapped_column(Integer)
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    timeout_ms: Mapped[int] = mapped_column(Integer, default=300000)
    cpu_usage_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    memory_usage_mb: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    network_bytes_in: Mapped[Optional[int]] = mapped_column(BigInteger)
    network_bytes_out: Mapped[Optional[int]] = mapped_column(BigInteger)
    llm_model: Mapped[Optional[str]] = mapped_column(String(100))
    llm_calls_count: Mapped[int] = mapped_column(Integer, default=0)
    llm_total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    llm_cost_usd: Mapped[float] = mapped_column(Numeric(10, 4), default=0)
    error_code: Mapped[Optional[str]] = mapped_column(String(50))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_stack_trace: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    parent_run_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("agent_runs.id"))
    child_runs: Mapped[Optional[List[UUID]]] = mapped_column(ARRAY(PGUUID(as_uuid=True)))
    triggered_by: Mapped[Optional[str]] = mapped_column(String(50))
    related_incident_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("incidents.id"))
    related_asset_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("assets.id"))
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    actions_taken: Mapped[dict] = mapped_column(JSONB, default=list)
    recommendations: Mapped[dict] = mapped_column(JSONB, default=list)
    is_automated: Mapped[bool] = mapped_column(Boolean, default=True)
    extra_data: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ============================================
# 8. AGENT_MEMORY MODEL (with Vector)
# ============================================
class AgentMemory(Base, TimestampMixin):
    __tablename__ = "agent_memories"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    # Vector embedding - defined dynamically based on availability
    embedding_model: Mapped[str] = mapped_column(String(100), default="text-embedding-ada-002")
    source_type: Mapped[Optional[str]] = mapped_column(String(50))
    source_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    importance_score: Mapped[float] = mapped_column(Numeric(5, 2), default=50)
    confidence_score: Mapped[float] = mapped_column(Numeric(5, 2), default=80)
    relevance_decay: Mapped[float] = mapped_column(Numeric(5, 4), default=0.01)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    usefulness_rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    related_memories: Mapped[Optional[List[UUID]]] = mapped_column(ARRAY(PGUUID(as_uuid=True)))
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    event_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    extra_data: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)


# Add vector column dynamically if available
if VECTOR_AVAILABLE:
    AgentMemory.embedding = mapped_column(Vector(1536), nullable=True)


# ============================================
# 9. LEARNED_LESSON MODEL
# ============================================
class LearnedLesson(Base, TimestampMixin):
    __tablename__ = "learned_lessons"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("incidents.id", ondelete="SET NULL"))
    agent_run_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="SET NULL"))
    failure_type: Mapped[Optional[str]] = mapped_column(String(100))
    failure_description: Mapped[Optional[str]] = mapped_column(Text)
    root_cause: Mapped[Optional[str]] = mapped_column(Text)
    what_happened: Mapped[Optional[str]] = mapped_column(Text)
    why_it_happened: Mapped[Optional[str]] = mapped_column(Text)
    what_was_expected: Mapped[Optional[str]] = mapped_column(Text)
    gap_analysis: Mapped[Optional[str]] = mapped_column(Text)
    proposed_solution: Mapped[Optional[str]] = mapped_column(Text)
    solution_type: Mapped[Optional[str]] = mapped_column(String(50))
    implementation_steps: Mapped[dict] = mapped_column(JSONB, default=list)
    applied: Mapped[bool] = mapped_column(Boolean, default=False)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    applied_by: Mapped[Optional[str]] = mapped_column(String(50))
    applied_changes: Mapped[dict] = mapped_column(JSONB, default=list)
    effectiveness_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    prevented_incidents: Mapped[int] = mapped_column(Integer, default=0)
    llm_analysis: Mapped[dict] = mapped_column(JSONB, default=dict)
    analysis_confidence: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    # Extended fields
    confidence_score: Mapped[float] = mapped_column(Numeric(3, 2), default=0.5)
    human_feedback_score: Mapped[Optional[int]] = mapped_column(Integer)
    context_hash: Mapped[Optional[str]] = mapped_column(String(64))
    related_incident_ids: Mapped[Optional[List[UUID]]] = mapped_column(ARRAY(PGUUID(as_uuid=True)))
    
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    verification_notes: Mapped[Optional[str]] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))

    
if VECTOR_AVAILABLE:
    LearnedLesson.vector_embedding = mapped_column(Vector(1536), nullable=True)

    
    # Relationships (disabled)



# ============================================
# 10. DEFENSE_RULE MODEL
# ============================================
class DefenseRule(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "defense_rules"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    conditions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    action_params: Mapped[dict] = mapped_column(JSONB, default=dict)
    applies_to: Mapped[str] = mapped_column(String(50), default="all")
    target_assets: Mapped[Optional[List[UUID]]] = mapped_column(ARRAY(PGUUID(as_uuid=True)))
    target_tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    priority: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_temporary: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(50), default="manual")
    source_incident_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("incidents.id"))
    source_lesson_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("learned_lessons.id"))
    match_count: Mapped[int] = mapped_column(BigInteger, default=0)
    last_matched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    block_count: Mapped[int] = mapped_column(BigInteger, default=0)
    false_positive_count: Mapped[int] = mapped_column(Integer, default=0)
    is_test_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    test_mode_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)
    previous_version_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("defense_rules.id"))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    created_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))


# ============================================
# 11. NOTIFICATION MODEL
# ============================================
class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20), default="info")
    related_type: Mapped[Optional[str]] = mapped_column(String(50))
    related_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    related_url: Mapped[Optional[str]] = mapped_column(String(500))
    actions: Mapped[dict] = mapped_column(JSONB, default=list)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_actionable: Mapped[bool] = mapped_column(Boolean, default=False)
    action_taken: Mapped[bool] = mapped_column(Boolean, default=False)
    action_taken_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    channels_sent: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    email_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    slack_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sms_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    group_key: Mapped[Optional[str]] = mapped_column(String(200))
    grouped_count: Mapped[int] = mapped_column(Integer, default=1)
    show_after: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    extra_data: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)


# ============================================
# 12. AUDIT_LOG MODEL
# ============================================
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    user_email: Mapped[Optional[str]] = mapped_column(String(255))
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    actor_type: Mapped[str] = mapped_column(String(30), nullable=False)
    actor_id: Mapped[Optional[str]] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    action_category: Mapped[Optional[str]] = mapped_column(String(50))
    resource_type: Mapped[Optional[str]] = mapped_column(String(100))
    resource_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    resource_name: Mapped[Optional[str]] = mapped_column(String(300))
    description: Mapped[Optional[str]] = mapped_column(Text)
    changes: Mapped[dict] = mapped_column(JSONB, default=dict)
    request_path: Mapped[Optional[str]] = mapped_column(String(500))
    request_method: Mapped[Optional[str]] = mapped_column(String(10))
    request_body: Mapped[Optional[dict]] = mapped_column(JSONB)
    response_status: Mapped[Optional[int]] = mapped_column(Integer)
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    country_code: Mapped[Optional[str]] = mapped_column(String(3))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    device_type: Mapped[Optional[str]] = mapped_column(String(50))
    device_os: Mapped[Optional[str]] = mapped_column(String(50))
    browser: Mapped[Optional[str]] = mapped_column(String(100))
    session_id: Mapped[Optional[str]] = mapped_column(String(100))
    api_key_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    flagged_by: Mapped[Optional[str]] = mapped_column(String(100))
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    retention_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


# ============================================
# 13. LLM_LOG MODEL
# ============================================
class LlmLog(Base):
    __tablename__ = "llm_logs"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    agent_run_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="SET NULL"))
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[Optional[str]] = mapped_column(String(50))
    prompt_template: Mapped[Optional[str]] = mapped_column(String(200))
    system_prompt_hash: Mapped[Optional[str]] = mapped_column(String(64))
    user_prompt_preview: Mapped[Optional[str]] = mapped_column(Text)
    user_prompt_hash: Mapped[Optional[str]] = mapped_column(String(64))
    full_prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    response_preview: Mapped[Optional[str]] = mapped_column(Text)
    response_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    finish_reason: Mapped[Optional[str]] = mapped_column(String(30))
    cost_input_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    cost_output_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    cost_total_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    time_to_first_token_ms: Mapped[Optional[int]] = mapped_column(Integer)
    tokens_per_second: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    was_filtered: Mapped[bool] = mapped_column(Boolean, default=False)
    filter_reason: Mapped[Optional[str]] = mapped_column(String(100))
    was_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    block_reason: Mapped[Optional[str]] = mapped_column(String(100))
    risk_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    rating: Mapped[Optional[int]] = mapped_column(Integer)
    feedback: Mapped[Optional[str]] = mapped_column(Text)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    previous_attempt_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("llm_logs.id"))
    error: Mapped[bool] = mapped_column(Boolean, default=False)
    error_code: Mapped[Optional[str]] = mapped_column(String(50))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    cache_key: Mapped[Optional[str]] = mapped_column(String(100))
    temperature: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    max_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    top_p: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    request_extra_data: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ============================================
# 14. API_KEY MODEL
# ============================================
class ApiKey(Base, TimestampMixin):
    __tablename__ = "api_keys"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    key_prefix: Mapped[Optional[str]] = mapped_column(String(10))
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    scopes: Mapped[List[str]] = mapped_column(ARRAY(String), default=["read:*"])
    allowed_ips: Mapped[Optional[List[str]]] = mapped_column(ARRAY(INET))
    allowed_origins: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    rate_limit: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    revoke_reason: Mapped[Optional[str]] = mapped_column(Text)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_used_ip: Mapped[Optional[str]] = mapped_column(INET)
    usage_count: Mapped[int] = mapped_column(BigInteger, default=0)
    usage_today: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    never_expires: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    environment: Mapped[str] = mapped_column(String(30), default="development")
    
    # Relationships (disabled)



# ============================================
# 15. SESSION MODEL
# ============================================
class Session(Base):
    __tablename__ = "sessions"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    refresh_token_hash: Mapped[Optional[str]] = mapped_column(String(128))
    device_id: Mapped[Optional[str]] = mapped_column(String(100))
    device_name: Mapped[Optional[str]] = mapped_column(String(200))
    device_type: Mapped[Optional[str]] = mapped_column(String(50))
    device_os: Mapped[Optional[str]] = mapped_column(String(100))
    device_os_version: Mapped[Optional[str]] = mapped_column(String(50))
    browser: Mapped[Optional[str]] = mapped_column(String(100))
    browser_version: Mapped[Optional[str]] = mapped_column(String(50))
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    country_code: Mapped[Optional[str]] = mapped_column(String(3))
    country_name: Mapped[Optional[str]] = mapped_column(String(100))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked_reason: Mapped[Optional[str]] = mapped_column(String(100))
    mfa_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    security_flags: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Relationships (disabled)



# ============================================
# 16. SUPERVISOR_STATE MODEL
# ============================================
class SupervisorState(Base, TimestampMixin):
    __tablename__ = "supervisor_state"
    
    agent_name: Mapped[str] = mapped_column(String(50), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_execution_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    total_executions: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=100.0)
    restart_count: Mapped[int] = mapped_column(Integer, default=0)
    active_task_id: Mapped[Optional[str]] = mapped_column(String(100))
    uptime_seconds: Mapped[int] = mapped_column(BigInteger, default=0)
    version: Mapped[Optional[str]] = mapped_column(String(20))
    

# ============================================
# 17. AGENT_EXECUTION_HISTORY MODEL
# ============================================
class AgentExecutionHistory(Base):
    __tablename__ = "agent_execution_history"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    input_snapshot: Mapped[dict] = mapped_column(JSONB, default=dict)
    output_snapshot: Mapped[dict] = mapped_column(JSONB, default=dict)
    error_details: Mapped[Optional[str]] = mapped_column(Text)
    llm_usage: Mapped[dict] = mapped_column(JSONB, default=dict)
    cost_estimate: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    memory_usage_mb: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ============================================
# 18. SUPERVISOR_EVENT MODEL
# ============================================
class SupervisorEvent(Base):
    __tablename__ = "supervisor_events"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_agent: Mapped[Optional[str]] = mapped_column(String(50))
    trigger_reason: Mapped[Optional[str]] = mapped_column(Text)
    action_taken: Mapped[Optional[str]] = mapped_column(Text)
    outcome: Mapped[Optional[str]] = mapped_column(String(50))
    is_automated: Mapped[bool] = mapped_column(Boolean, default=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ============================================
# 19. AGENT_METRICS MODEL
# ============================================
class AgentMetric(Base):
    __tablename__ = "agent_metrics"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    window_size: Mapped[Optional[str]] = mapped_column(String(20))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())





